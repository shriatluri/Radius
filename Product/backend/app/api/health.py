"""
Health check and rate limit status endpoints.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Response
from sqlalchemy import text

from app.core import APIKeyInfo, require_api_key, RateLimitResult
from app.core.config import settings
from app.services.sanctions import get_sanctions_status

from .dependencies import apply_rate_limit, add_rate_limit_headers

router = APIRouter()


def _check_db() -> bool:
    """Return True if the database is reachable, False otherwise."""
    try:
        from app.db.database import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _sanctions_data_age_hours(last_updated: str | None) -> float | None:
    """
    Return how many hours ago the OFAC data was last refreshed.
    Returns None if we have no timestamp yet (cold start, never loaded).
    """
    if not last_updated:
        return None
    try:
        updated_at = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - updated_at
        return round(delta.total_seconds() / 3600, 1)
    except Exception:
        return None


@router.get("/health")
def health_check() -> dict:
    """
    Health check endpoint for load balancers and monitoring.

    Returns overall status plus the state of each critical subsystem.
    A 200 response with status='healthy' means all subsystems are up.
    """
    db_connected = _check_db()
    sanctions = get_sanctions_status()
    data_age = _sanctions_data_age_hours(sanctions.get("last_updated"))

    # Degraded if DB is down or sanctions data is stale (>26h = missed a refresh cycle)
    sanctions_stale = sanctions.get("data_stale", True)
    overall = "healthy" if (db_connected and not sanctions_stale) else "degraded"

    return {
        "status": overall,
        "version": settings.api_version,
        "environment": settings.environment,
        "db_connected": db_connected,
        "sanctions_screening": {
            "loaded": sanctions.get("loaded", False),
            "address_count": sanctions.get("address_count", 0),
            "last_updated": sanctions.get("last_updated"),
            "data_age_hours": data_age,
            "data_stale": sanctions_stale,
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
