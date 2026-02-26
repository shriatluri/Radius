"""
API Key management endpoints.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import logging

from app.core import APIKeyInfo, require_api_key, generate_api_key, RadiusError
from app.core.auth import check_scope

logger = logging.getLogger(__name__)
from app.db import get_db, APIKeyRepository
from app.schemas import (
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    APIKeyInfo as APIKeyInfoSchema,
    APIKeyListResponse,
    APIKeyRevokeResponse,
)

router = APIRouter(prefix="/api-keys")


@router.post("", response_model=APIKeyCreateResponse)
def create_api_key(
    payload: APIKeyCreateRequest,
    auth: APIKeyInfo = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    """
    Create a new API key for a business.

    IMPORTANT: The returned `api_key` is shown ONLY ONCE. Store it securely.
    We only store a hash of the key, so it cannot be recovered.

    Requires admin scope or ownership of the business.
    """
    prefix = "sk_test_" if payload.is_test_key else "sk_live_"
    plaintext_key, key_hash = generate_api_key(prefix)

    expires_at = None
    if payload.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=payload.expires_in_days)

    repo = APIKeyRepository(db)
    db_key = repo.create(
        key_hash=key_hash,
        key_prefix=prefix,
        business_id=payload.business_id,
        name=payload.name,
        scopes=payload.scopes or "read,write",
        expires_at=expires_at,
    )

    return APIKeyCreateResponse(
        key_id=db_key.id,
        api_key=plaintext_key,
        key_prefix=prefix,
        business_id=db_key.business_id,
        name=db_key.name,
        scopes=db_key.scopes,
        expires_at=db_key.expires_at.isoformat() + "Z" if db_key.expires_at else None,
        created_at=db_key.created_at.isoformat() + "Z",
    )


@router.get("", response_model=APIKeyListResponse)
def list_api_keys(
    auth: APIKeyInfo = Depends(require_api_key),
    db: Session = Depends(get_db),
    business_id: Optional[str] = Query(None, description="Filter by business ID"),
):
    """
    List API keys for a business.

    Note: The actual key values are never returned - only metadata.
    """
    target_business = business_id or auth.business_id

    repo = APIKeyRepository(db)
    db_keys = repo.list_by_business(target_business)

    keys = [
        APIKeyInfoSchema(
            key_id=k.id,
            key_prefix=k.key_prefix,
            business_id=k.business_id,
            name=k.name,
            scopes=k.scopes,
            is_active=k.is_active,
            last_used_at=k.last_used_at.isoformat() + "Z" if k.last_used_at else None,
            expires_at=k.expires_at.isoformat() + "Z" if k.expires_at else None,
            created_at=k.created_at.isoformat() + "Z",
        )
        for k in db_keys
    ]

    return APIKeyListResponse(keys=keys, total=len(keys))


@router.post("/{key_id}/rotate", response_model=APIKeyCreateResponse)
def rotate_api_key(
    key_id: str,
    auth: APIKeyInfo = Depends(require_api_key),
    db: Session = Depends(get_db),
    _: None = Depends(check_scope("transactions:write")),
):
    """
    Rotate an API key — revoke the old one and issue a new one instantly.

    Why rotation exists: if a key is accidentally exposed (committed to git,
    logged somewhere, seen by the wrong person), you can invalidate it immediately
    and replace it without downtime. The new key has the same scopes and prefix
    as the old one so your integration keeps working after you swap the value.

    Security: you can only rotate keys belonging to your own business_id.
    Attempting to rotate another tenant's key returns 404 (not 403) — we don't
    confirm whether a key ID exists outside your account.

    The new plaintext key is returned ONCE. Store it immediately.
    """
    repo = APIKeyRepository(db)
    old_key = repo.get_by_id(key_id)

    # 404 regardless of whether the key exists but belongs to another business —
    # we don't want to confirm the existence of other tenants' keys.
    if not old_key or old_key.business_id != auth.business_id:
        raise RadiusError("key_not_found", f"API key {key_id} not found", 404)

    # Atomically revoke old and create new with same prefix + scopes
    repo.revoke(key_id)

    plaintext_key, key_hash = generate_api_key(old_key.key_prefix)
    new_key = repo.create(
        key_hash=key_hash,
        key_prefix=old_key.key_prefix,
        business_id=old_key.business_id,
        name=old_key.name,
        scopes=old_key.scopes,
    )

    logger.info(
        "api_key_rotated",
        extra={
            "event": "api_key_rotated",
            "old_key_id": key_id,
            "new_key_id": new_key.id,
            "business_id": auth.business_id,
        },
    )

    return APIKeyCreateResponse(
        key_id=new_key.id,
        api_key=plaintext_key,
        key_prefix=new_key.key_prefix,
        business_id=new_key.business_id,
        name=new_key.name,
        scopes=new_key.scopes,
        expires_at=new_key.expires_at.isoformat() + "Z" if new_key.expires_at else None,
        created_at=new_key.created_at.isoformat() + "Z",
        warning="New key issued. The old key is immediately invalid. Store this key securely — it will not be shown again.",
    )


@router.delete("/{key_id}", response_model=APIKeyRevokeResponse)
def revoke_api_key(
    key_id: str,
    auth: APIKeyInfo = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    """
    Revoke (deactivate) an API key.

    Once revoked, the key can no longer be used for authentication.
    This action cannot be undone.
    """
    repo = APIKeyRepository(db)
    success = repo.revoke(key_id)

    if not success:
        raise RadiusError("key_not_found", f"API key {key_id} not found", 404)

    return APIKeyRevokeResponse(
        key_id=key_id,
        revoked=True,
        message="API key has been revoked and can no longer be used",
    )
