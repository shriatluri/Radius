"""
Database configuration and session management.

This module sets up the SQLAlchemy engine and session factory.
The database URL is read from environment variables, allowing
different databases for development, testing, and production.

Usage:
    from app.db import get_db, engine

    # In FastAPI endpoints, use dependency injection:
    def my_endpoint(db: Session = Depends(get_db)):
        ...

Environment Variables:
    DATABASE_URL: PostgreSQL connection string
        Example: postgresql://user:password@localhost:5432/radius

    For local development, defaults to SQLite at backend/radius_dev.db
"""

import os
from typing import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

# Load environment variables from .env file
load_dotenv()

# Get backend directory (two levels up from db/)
BACKEND_DIR = Path(__file__).parent.parent.parent
DEFAULT_DB_PATH = BACKEND_DIR / "radius_dev.db"

# Get database URL from environment
# Default to SQLite for easy local development without PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DEFAULT_DB_PATH}"
)

# SQLAlchemy requires "postgresql://" but some providers use "postgres://"
# This handles both formats
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create the SQLAlchemy engine
# - For SQLite: need check_same_thread=False for FastAPI's async nature
# - For PostgreSQL: pool_pre_ping=True ensures stale connections are recycled
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # SQLite-specific
        echo=False,  # Set to True to see SQL queries in logs
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=5,         # Number of connections to keep open
        max_overflow=10,     # Additional connections when pool is full
        echo=False,          # Set to True to see SQL queries in logs
    )

# SessionLocal is a factory for creating database sessions
# - autocommit=False: We control when commits happen
# - autoflush=False: We control when data is flushed to DB
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for all our database models
# All model classes will inherit from this
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.

    Use this in FastAPI endpoints like:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()

    The session is automatically closed after the request completes,
    even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Create all database tables.

    Call this once at application startup to ensure
    all tables exist. In production, you'd use Alembic
    migrations instead for more control.
    """
    # Import models so SQLAlchemy knows about them
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
