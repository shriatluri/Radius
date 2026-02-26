"""
Wallet verification endpoints.
"""

from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core import APIKeyInfo, require_api_key
from app.core.auth import check_scope
from app.core.config import settings
from app.db import get_db, WalletVerificationRepository
from app.schemas import WalletVerifyRequest, WalletVerifyResponse
from app.services import verify_wallet_signature, is_message_expired
from app.storage import STORE

router = APIRouter(prefix="/wallets")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@router.post("/verify", response_model=WalletVerifyResponse)
def verify_wallet(
    payload: WalletVerifyRequest,
    auth: APIKeyInfo = Depends(require_api_key),
    db: Session = Depends(get_db),
    _: None = Depends(check_scope("transactions:write")),
) -> WalletVerifyResponse:
    """
    Verify wallet ownership via signed message.

    The message format should be: "radius-verify:{entity_id}:{YYYY-MM-DD}"
    The signature must be from the wallet address being verified.
    """
    wallet_id = _new_id("wal")

    # Check if message has expired (older than 7 days)
    if is_message_expired(payload.proof.message):
        return WalletVerifyResponse(
            wallet_id=wallet_id,
            verification_status="rejected",
            error="Verification message has expired. Please sign a new message.",
        )

    # Verify the signature
    result = verify_wallet_signature(
        wallet=payload.wallet,
        message=payload.proof.message,
        signature=payload.proof.signature,
    )

    if not result.is_valid:
        return WalletVerifyResponse(
            wallet_id=wallet_id,
            verification_status="rejected",
            error=result.error,
        )

    # Signature is valid - store the verification
    now = datetime.utcnow().replace(microsecond=0)
    expires = now + timedelta(days=90)  # Verification valid for 90 days

    if settings.use_database:
        wallet_repo = WalletVerificationRepository(db)
        verification = wallet_repo.create(
            wallet=payload.wallet,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            verification_status="verified",
            recovered_address=result.recovered_address,
            verified_at=now,
            expires_at=expires,
        )
        wallet_id = verification.id
    else:
        STORE.wallet_verifications[wallet_id] = {
            "wallet": payload.wallet,
            "entity_type": payload.entity_type,
            "entity_id": payload.entity_id,
            "verified_at": now.isoformat() + "Z",
            "expires_at": expires.isoformat() + "Z",
            "recovered_address": result.recovered_address,
        }

    return WalletVerifyResponse(
        wallet_id=wallet_id,
        verification_status="verified",
        verified_at=now.isoformat() + "Z",
        expires_at=expires.isoformat() + "Z",
    )
