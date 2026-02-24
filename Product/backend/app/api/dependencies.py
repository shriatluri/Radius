"""
Shared dependencies for API routes.

Contains rate limiting and other common dependencies.
"""

from datetime import datetime

from fastapi import Depends, Request, Response

from app.core import (
    APIKeyInfo,
    require_api_key,
    RateLimitResult,
    check_rate_limit,
    rate_limit_headers,
    raise_rate_limit_exceeded,
    RATE_LIMIT_TOKENS,
)
from app.core.config import settings


async def apply_rate_limit(
    request: Request,
    auth: APIKeyInfo = Depends(require_api_key),
) -> RateLimitResult:
    """
    FastAPI dependency that applies rate limiting per API key.

    Returns RateLimitResult so endpoints can include headers.
    Raises 429 if rate limit exceeded.
    """
    if not settings.rate_limit_enabled:
        # Return a dummy result when disabled
        return RateLimitResult(
            allowed=True,
            remaining=RATE_LIMIT_TOKENS,
            limit=RATE_LIMIT_TOKENS,
            reset_at=datetime.utcnow(),
        )

    # Use API key ID as the rate limit key
    result = check_rate_limit(auth.key_id)

    if not result.allowed:
        raise_rate_limit_exceeded(result)

    return result


def add_rate_limit_headers(response: Response, result: RateLimitResult) -> Response:
    """Add rate limit headers to a response."""
    for header, value in rate_limit_headers(result).items():
        response.headers[header] = value
    return response
