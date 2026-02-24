"""
Wallet verification schemas.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class WalletProof(BaseModel):
    """Proof of wallet ownership via signed message."""
    type: Literal["signed_message"]
    message: str
    signature: str


class WalletVerifyRequest(BaseModel):
    """Request to verify wallet ownership."""
    wallet: str
    entity_type: Literal["user", "business"]
    entity_id: str
    proof: WalletProof


class WalletVerifyResponse(BaseModel):
    """Response from wallet verification."""
    wallet_id: str
    verification_status: Literal["pending", "verified", "rejected"]
    verified_at: Optional[str] = None
    expires_at: Optional[str] = None
    error: Optional[str] = None
