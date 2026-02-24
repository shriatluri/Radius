"""
Travel Rule schemas.
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel


class TravelRuleTransmitRequest(BaseModel):
    """Request to transmit Travel Rule data to counterparty VASP."""
    transaction_id: str
    originator: Dict[str, Any]
    beneficiary: Dict[str, Any]
    beneficiary_vasp: Dict[str, Any]


class TravelRuleTransmitResponse(BaseModel):
    """Response from Travel Rule transmission."""
    transaction_id: str
    travel_rule_status: Literal["sent", "failed"]
    proof_id: Optional[str] = None
