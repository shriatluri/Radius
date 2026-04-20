"""
API Key authentication for Radius.

Features:
- Database-backed key storage with SHA-256 hashing
- Key generation with secure random tokens
- Key rotation and expiration support
- Scoped permissions (read, write, admin)
- Automatic last_used tracking
- Fallback to mock keys for demo/testing
"""

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db


@dataclass
class APIKeyInfo:
    """Information associated with an API key."""
    key_id: str
    business_id: str
    name: str
    scopes: list[str]
    is_test_key: bool = False


@dataclass
class AuthInfo:
    """
    Unified auth context for both Clerk JWT and API key authentication.

    Every authenticated request resolves to an AuthInfo that carries the
    business_id regardless of auth method. Endpoints don't care which
    method was used — they just read business_id and scopes.
    """
    business_id: str
    auth_type: str  # "clerk" | "api_key"
    scopes: list[str] = field(default_factory=list)
    user_id: Optional[str] = None   # Clerk user DB id (for clerk auth)
    key_id: Optional[str] = None    # API key id (for api_key auth)


# Mock API keys for demo/testing (used when database is unavailable or USE_DATABASE=false)
MOCK_API_KEYS: dict[str, APIKeyInfo] = {
    "sk_test_acme_123456": APIKeyInfo(
        key_id="key_mock_acme",
        business_id="acme_corp",  # Acme Corp's business ID
        name="Acme Corp Test Key",
        scopes=["transactions:write", "transactions:read", "reports:read"],
        is_test_key=True,
    ),
    "sk_test_globalcorp_789012": APIKeyInfo(
        key_id="key_mock_globalcorp",
        business_id="globalcorp",  # GlobalCorp's business ID
        name="GlobalCorp Test Key",
        scopes=["transactions:write", "transactions:read", "reports:read"],
        is_test_key=True,
    ),
    "sk_test_techstartup_000000": APIKeyInfo(
        key_id="key_mock_techstartup",
        business_id="techstartup_inc",  # TechStartup's business ID
        name="TechStartup Test Key",
        scopes=["transactions:write", "transactions:read", "reports:read"],
        is_test_key=True,
    ),
    "sk_test_admin_radius_dev": APIKeyInfo(
        key_id="key_mock_admin",
        business_id="radius_internal",
        name="Radius Admin (dev only)",
        scopes=["admin:all", "transactions:write", "transactions:read", "reports:read"],
        is_test_key=True,
    ),
}


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using SHA-256.

    We store hashes, not plaintext keys, so even if the database
    is compromised, the actual keys cannot be recovered.
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key(prefix: str = "sk_live_") -> tuple[str, str]:
    """
    Generate a new API key and its hash.

    Returns:
        tuple: (plaintext_key, key_hash)

    The plaintext key is shown to the user ONCE at creation time.
    We only store the hash.

    Key format: {prefix}{random_32_chars}
    Example: sk_live_<32 hex characters>
    """
    # Generate 32 random bytes, encode as hex (64 chars), take first 32
    random_part = secrets.token_hex(16)  # 32 hex characters
    plaintext_key = f"{prefix}{random_part}"
    key_hash = hash_api_key(plaintext_key)

    return plaintext_key, key_hash


def validate_api_key_mock(api_key: str) -> Optional[APIKeyInfo]:
    """Validate against mock keys (for demo/testing)."""
    return MOCK_API_KEYS.get(api_key)


def validate_api_key_db(api_key: str, db: Session) -> Optional[APIKeyInfo]:
    """
    Validate an API key against the database.

    Steps:
    1. Hash the provided key
    2. Look up the hash in the database
    3. Check if key is active and not expired
    4. Update last_used timestamp
    5. Return key info
    """
    from app.db.repositories import APIKeyRepository

    key_hash = hash_api_key(api_key)
    repo = APIKeyRepository(db)

    db_key = repo.get_by_hash(key_hash)
    if not db_key:
        return None

    # Check expiration
    if db_key.expires_at and db_key.expires_at < datetime.utcnow():
        return None

    # Update last used
    repo.update_last_used(db_key.id)

    # Parse scopes from comma-separated string
    scopes = db_key.scopes.split(",") if db_key.scopes else []

    return APIKeyInfo(
        key_id=db_key.id,
        business_id=db_key.business_id,
        name=db_key.name or "Unnamed Key",
        scopes=scopes,
        is_test_key=db_key.key_prefix.startswith("sk_test_"),
    )


def validate_api_key(api_key: str, db: Optional[Session] = None) -> Optional[APIKeyInfo]:
    """
    Validate an API key.

    In development: checks DB first, then falls back to mock keys (sk_test_*).
    In production:  checks DB only — mock keys are never accepted.

    Switch via ENVIRONMENT env var ("development" | "production").
    """
    from app.core.config import settings

    # Try database first if session provided
    if db is not None:
        try:
            result = validate_api_key_db(api_key, db)
            if result:
                return result
        except Exception:
            # Database error - fall through to mock keys (dev only)
            pass

    # Mock keys are only available in development
    if settings.environment != "production":
        return validate_api_key_mock(api_key)

    return None


async def require_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> APIKeyInfo:
    """
    FastAPI dependency that requires a valid API key.

    Usage:
        @app.get("/endpoint")
        def endpoint(auth: APIKeyInfo = Depends(require_api_key)):
            # auth.business_id is available here
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "missing_api_key", "message": "X-API-Key header is required"}},
        )

    key_info = validate_api_key(x_api_key, db)
    if not key_info:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "invalid_api_key", "message": "Invalid API key"}},
        )

    return key_info


def check_scope(required_scope: str):
    """
    Dependency factory to check if API key has required scope.

    Usage:
        @app.post("/admin/endpoint")
        def admin_endpoint(
            auth: APIKeyInfo = Depends(require_api_key),
            _: None = Depends(check_scope("admin:write")),
        ):
            ...
    """
    async def scope_checker(auth: APIKeyInfo = Depends(require_api_key)) -> None:
        if required_scope not in auth.scopes and "admin:all" not in auth.scopes:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "code": "insufficient_scope",
                        "message": f"This endpoint requires the '{required_scope}' scope",
                    }
                },
            )
    return scope_checker


def check_auth_scope(required_scope: str):
    """
    Dependency factory to check scope on unified auth (Clerk JWT or API key).

    Same as check_scope but works with require_auth instead of require_api_key.
    Clerk users with 'dashboard:all' scope pass all dashboard-level checks.
    """
    async def scope_checker(auth: AuthInfo = Depends(require_auth)) -> None:
        if (
            required_scope not in auth.scopes
            and "admin:all" not in auth.scopes
            and "dashboard:all" not in auth.scopes
        ):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "code": "insufficient_scope",
                        "message": f"This endpoint requires the '{required_scope}' scope",
                    }
                },
            )
    return scope_checker


async def require_auth(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> AuthInfo:
    """
    Unified auth dependency: accepts Clerk JWT (Bearer token) or API key.

    Checks Authorization: Bearer <jwt> first, then falls back to X-API-Key.
    Both resolve to an AuthInfo with business_id so endpoints are auth-agnostic.

    Clerk users get dashboard:all scope (read access to transactions, audit, reports).
    API key users get their configured scopes.
    """
    # Try Bearer JWT first
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:]  # Strip "Bearer "
        return _auth_from_clerk_token(token, db)

    # Fall back to API key
    if x_api_key:
        key_info = validate_api_key(x_api_key, db)
        if not key_info:
            raise HTTPException(
                status_code=401,
                detail={"error": {"code": "invalid_api_key", "message": "Invalid API key"}},
            )
        return AuthInfo(
            business_id=key_info.business_id,
            auth_type="api_key",
            scopes=key_info.scopes,
            key_id=key_info.key_id,
        )

    raise HTTPException(
        status_code=401,
        detail={
            "error": {
                "code": "missing_credentials",
                "message": "Authorization header (Bearer token) or X-API-Key header is required",
            }
        },
    )


def _auth_from_clerk_token(token: str, db: Session) -> AuthInfo:
    """Verify a Clerk JWT and resolve it to an AuthInfo."""
    from app.core.clerk import verify_clerk_token
    from app.db.repositories import UserRepository

    claims = verify_clerk_token(token)
    if claims is None:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "invalid_token", "message": "Invalid or expired token"}},
        )

    clerk_user_id = claims.get("sub")
    if not clerk_user_id:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "invalid_token", "message": "Token missing sub claim"}},
        )

    user_repo = UserRepository(db)
    user = user_repo.get_by_clerk_id(clerk_user_id)

    if not user:
        # Auto-provision: try to match by email from Clerk claims
        user = _auto_provision_user(claims, clerk_user_id, db)

    return AuthInfo(
        business_id=user.business_id,
        auth_type="clerk",
        scopes=["dashboard:all", "transactions:read", "reports:read"],
        user_id=user.id,
    )


def _auto_provision_user(claims: dict, clerk_user_id: str, db: Session):
    """
    Auto-provision a User record on first Clerk login.

    Tries to match the Clerk email to an existing Business.
    If no match, creates a new Business + User.
    """
    from app.db.repositories import BusinessRepository, UserRepository

    # Clerk stores email in different claim locations depending on config
    email = (
        claims.get("email")
        or claims.get("email_addresses", [{}])[0].get("email_address", "")
        if isinstance(claims.get("email_addresses"), list) and claims.get("email_addresses")
        else claims.get("email", "")
    )

    if not email:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "missing_email", "message": "Could not determine email from Clerk token"}},
        )

    biz_repo = BusinessRepository(db)
    user_repo = UserRepository(db)

    # Try matching email to existing business
    business = biz_repo.get_by_email(email)
    if not business:
        # Create a new business for this user
        name = claims.get("name") or claims.get("first_name", "") + " " + claims.get("last_name", "")
        name = name.strip() or email.split("@")[0]
        business = biz_repo.create(name=name, email=email)

    user = user_repo.create(
        clerk_user_id=clerk_user_id,
        business_id=business.id,
        email=email,
        role="admin",  # First user for a business gets admin
    )
    return user
