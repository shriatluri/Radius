"""
Health check and rate limit status endpoints.
"""

from fastapi import APIRouter, Depends, Response

from app.core import APIKeyInfo, require_api_key, RateLimitResult
from app.core.config import settings
from app.services.sanctions import get_sanctions_status

from .dependencies import apply_rate_limit, add_rate_limit_headers

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    """Health check endpoint for load balancers and k8s probes."""
    sanctions = get_sanctions_status()
    return {
        "status": "healthy",
        "version": settings.api_version,
        "rate_limiting": settings.rate_limit_enabled,
        "sanctions_screening": {
            "loaded": sanctions.get("loaded", False),
            "address_count": sanctions.get("address_count", 0),
            "last_updated": sanctions.get("last_updated"),
            "data_stale": sanctions.get("data_stale", True),
        },
    }


@router.get("/rate-limit/status")
def rate_limit_status(
    response: Response,
    auth: APIKeyInfo = Depends(require_api_key),
    rate_limit: RateLimitResult = Depends(apply_rate_limit),
):
    """
    Check your current rate limit status.

    Returns remaining requests and reset time.
    This request itself consumes 1 token.
    """
    add_rate_limit_headers(response, rate_limit)

    return {
        "rate_limit": {
            "limit": rate_limit.limit,
            "remaining": rate_limit.remaining,
            "reset_at": rate_limit.reset_at.isoformat() + "Z",
            "enabled": settings.rate_limit_enabled,
        }
    }
