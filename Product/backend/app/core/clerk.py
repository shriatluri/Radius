"""
Clerk JWT verification for dashboard authentication.

Fetches and caches JWKS keys from Clerk, then verifies RS256 JWTs
issued by Clerk's Frontend API. Extracts the `sub` claim (Clerk user ID)
for downstream user lookup.
"""

import time
from typing import Optional

import jwt
import requests

from app.core.config import settings

# JWKS cache: list of keys + expiry timestamp
_jwks_cache: dict = {"keys": [], "expires_at": 0.0}
_CACHE_TTL = 3600  # 1 hour


def _get_jwks_url() -> str:
    """
    Return the JWKS URL for the configured Clerk instance.

    If CLERK_JWKS_URL is set explicitly, use it.
    Otherwise, derive from CLERK_SECRET_KEY (not implemented — requires publishable key).
    """
    if settings.clerk_jwks_url:
        return settings.clerk_jwks_url
    raise ValueError(
        "CLERK_JWKS_URL must be set. "
        "Find it in Clerk Dashboard → API Keys → JWKS URL."
    )


def _fetch_jwks() -> list[dict]:
    """Fetch JWKS keys from Clerk, with 1-hour caching."""
    now = time.time()
    if _jwks_cache["keys"] and now < _jwks_cache["expires_at"]:
        return _jwks_cache["keys"]

    url = _get_jwks_url()
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    keys = resp.json().get("keys", [])

    _jwks_cache["keys"] = keys
    _jwks_cache["expires_at"] = now + _CACHE_TTL
    return keys


def verify_clerk_token(token: str) -> Optional[dict]:
    """
    Verify a Clerk-issued JWT and return its claims.

    Returns None if verification fails for any reason.
    The `sub` claim contains the Clerk user ID.
    """
    try:
        jwks = _fetch_jwks()
        # Build a PyJWKClient-compatible key set
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        signing_key = None
        for key_data in jwks:
            if key_data.get("kid") == kid:
                signing_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
                break

        if signing_key is None:
            # Key not found — try refreshing cache once
            _jwks_cache["expires_at"] = 0.0
            jwks = _fetch_jwks()
            for key_data in jwks:
                if key_data.get("kid") == kid:
                    signing_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
                    break

        if signing_key is None:
            return None

        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            options={"verify_aud": False},  # Clerk doesn't set aud by default
        )
        return claims

    except (jwt.PyJWTError, requests.RequestException, ValueError, KeyError):
        return None
