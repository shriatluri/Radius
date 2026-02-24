"""
Common schemas used across multiple domains.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Literal, Optional

from pydantic import BaseModel


def utc_now() -> str:
    """Return current UTC time as ISO string."""
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def parse_amount(value: str) -> Decimal:
    """Parse a string amount to Decimal."""
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError("amount must be a decimal string")


class Entity(BaseModel):
    """An entity involved in a transaction (sender or receiver)."""
    type: Literal["business", "user", "vasp", "unknown"]
    entity_id: str
    wallet: Optional[str] = None
    jurisdiction: Optional[str] = None  # ISO 3166-1 alpha-2 country code
