"""
Test infrastructure for Radius API.

Sets up:
- In-memory SQLite database (StaticPool so all sessions share one connection)
- FastAPI TestClient with overridden database dependency
- OFAC startup refresh mocked out (no internet calls)
- Auth, transaction, and other data fixtures

Import order matters here. database.py evaluates DATABASE_URL at module load
time, so we must set env vars *and* patch the db module's engine/SessionLocal
before importing any app code. That way init_db() and get_db() both resolve to
the test engine at call time.
"""

import os
import pytest
from unittest.mock import patch, AsyncMock

# ---------------------------------------------------------------------------
# 1. Set test environment before any app module is imported.
# ---------------------------------------------------------------------------
os.environ["USE_DATABASE"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["RATE_LIMIT_ENABLED"] = "false"

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

# ---------------------------------------------------------------------------
# 2. Build a shared in-memory SQLite engine.
#    StaticPool ensures every session uses the same underlying connection so
#    they all see the same in-memory database state.
# ---------------------------------------------------------------------------
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)

# ---------------------------------------------------------------------------
# 3. Patch the database module's engine and SessionLocal before the app is
#    imported. Both init_db() and get_db() look these names up at call time
#    (not at import time), so replacing the module attributes here makes them
#    point at our test engine for every call that follows.
# ---------------------------------------------------------------------------
import app.db.database as _db_module  # noqa: E402

_db_module.engine = TEST_ENGINE
_db_module.SessionLocal = TestingSessionLocal

# ---------------------------------------------------------------------------
# 4. Import the app now that the database is wired to the test engine.
# ---------------------------------------------------------------------------
from app.main import app  # noqa: E402
from app.db.database import get_db  # noqa: E402
from app.db.models import Base  # noqa: E402


# ---------------------------------------------------------------------------
# Database dependency override
# ---------------------------------------------------------------------------
def _get_test_db():
    """Replace the real get_db with a session bound to the shared test engine."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """
    FastAPI TestClient with a fresh in-memory SQLite database per test.

    Each invocation drops and recreates all tables so tests are fully
    isolated — no state leaks between test functions.

    OFAC startup refresh is mocked so tests run offline without hitting
    Treasury.gov.
    """
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)

    app.dependency_overrides[get_db] = _get_test_db

    with patch("app.main._startup_ofac_refresh", new=AsyncMock(return_value=None)):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """HTTP headers for the default test API key (transactions:write + read)."""
    return {"X-API-Key": "sk_test_acme_123456"}


@pytest.fixture
def admin_headers():
    """HTTP headers for the admin test API key (admin:all scope)."""
    return {"X-API-Key": "sk_test_admin_radius_dev"}


@pytest.fixture(autouse=True)
def seed_ofac_screener():
    """
    Pre-seed the OFAC screener singleton as loaded-with-empty-index before
    every test. This prevents check_sanctions() from trying to download the
    80 MB SDN XML from Treasury.gov during integration tests.

    With _index={} and _loaded=True:
    - screener.check() returns no match
    - address_count == 0, so check_sanctions() falls through to
      KNOWN_SANCTIONED_WALLETS (the offline fallback list)
    - Wallets in KNOWN_SANCTIONED_WALLETS are still caught as blocked
    - Clean wallets pass through cleanly
    """
    import app.services.ofac as _ofac_module
    from app.services.ofac import OFACScreener

    screener = OFACScreener()
    screener._loaded = True
    screener._index = {}
    _ofac_module._screener = screener
    yield
    _ofac_module._screener = None


@pytest.fixture
def sample_transaction():
    """
    Minimal valid payload for POST /v1/transactions/ingest.

    Chosen so it produces a predictable, low-risk result:
    - Clean wallet addresses (not on OFAC SDN)
    - $500 USDC on Ethereum
    - US-to-US, sub-$3 000 → Travel Rule not required
    - Expected: risk low, sanctions passed, status approved
    """
    return {
        "external_id": "test-tx-001",
        "direction": "outbound",
        "business_id": "acme_corp",
        "from_entity": {
            "type": "business",
            "entity_id": "acme_corp",
            "wallet": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            "jurisdiction": "US",
        },
        "to_entity": {
            "type": "user",
            "entity_id": "contractor_001",
            "wallet": "0x742d35Cc6634C0532925a3b8D4C9C79D3b3B4123",
            "jurisdiction": "US",
        },
        "amount": "500.00",
        "asset": "USDC",
        "chain": "ethereum",
        "purpose": "contractor_payout",
    }
