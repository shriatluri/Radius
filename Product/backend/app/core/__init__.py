"""
Core infrastructure for Radius API.

Contains authentication, rate limiting, configuration, and error handling.
"""

from .auth import (
    APIKeyInfo,
    require_api_key,
    check_scope,
    generate_api_key,
    hash_api_key,
    validate_api_key,
)
from .rate_limit import (
    RateLimitResult,
    check_rate_limit,
    rate_limit_headers,
    raise_rate_limit_exceeded,
    RATE_LIMIT_TOKENS,
)
from .errors import RadiusError
from .config import settings

__all__ = [
    # Auth
    "APIKeyInfo",
    "require_api_key",
    "check_scope",
    "generate_api_key",
    "hash_api_key",
    "validate_api_key",
    # Rate limiting
    "RateLimitResult",
    "check_rate_limit",
    "rate_limit_headers",
    "raise_rate_limit_exceeded",
    "RATE_LIMIT_TOKENS",
    # Errors
    "RadiusError",
    # Config
    "settings",
]
