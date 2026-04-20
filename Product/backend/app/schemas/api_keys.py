"""
API Key management schemas.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class APIKeyCreateRequest(BaseModel):
    """Request to create a new API key."""
    business_id: Optional[str] = None  # Defaults to authenticated user's business
    name: Optional[str] = None
    scopes: Optional[str] = "read,write"  # Comma-separated
    expires_in_days: Optional[int] = None  # None = never expires
    is_test_key: bool = False


class APIKeyCreateResponse(BaseModel):
    """Response when creating an API key. Contains the plaintext key (shown only once)."""
    key_id: str
    api_key: str  # Plaintext key - ONLY shown once at creation
    key_prefix: str
    business_id: str
    name: Optional[str]
    scopes: str
    expires_at: Optional[str]
    created_at: str
    warning: str = "Store this key securely. It will not be shown again."


class APIKeyInfo(BaseModel):
    """API key information (without the actual key)."""
    key_id: str
    key_prefix: str
    business_id: str
    name: Optional[str]
    scopes: str
    is_active: bool
    last_used_at: Optional[str]
    expires_at: Optional[str]
    created_at: str


class APIKeyListResponse(BaseModel):
    """List of API keys for a business."""
    keys: List[APIKeyInfo]
    total: int


class APIKeyRevokeResponse(BaseModel):
    """Response when revoking an API key."""
    key_id: str
    revoked: bool
    message: str
