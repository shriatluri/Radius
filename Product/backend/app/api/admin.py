"""
Admin endpoints for internal operations.

All routes require the `admin:all` scope. Use `sk_test_admin_radius_dev`
in development or a properly-scoped live key in production.
"""

import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.core.auth import APIKeyInfo, check_scope, require_api_key
from app.core.config import settings
from app.services.ofac import get_screener
from app.services.sanctions import get_sanctions_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin")

# Shared dependency: valid key + admin scope
_admin = [Depends(require_api_key), Depends(check_scope("admin:all"))]


# ---------------------------------------------------------------------------
# Sanctions screener endpoints
# ---------------------------------------------------------------------------

@router.get("/sanctions/status", dependencies=_admin)
def sanctions_status() -> dict:
    """
    Return the current state of the OFAC SDN screener.

    Reports how many addresses are loaded, when data was last refreshed,
    and whether a refresh is needed.
    """
    status = get_sanctions_status()
    return {
        "screener": status,
        "provider": settings.sanctions_provider,
    }


@router.post("/sanctions/refresh", dependencies=_admin, status_code=202)
async def refresh_sanctions(force: bool = False) -> dict:
    """
    Trigger a refresh of OFAC SDN data in the background.

    Returns 202 immediately. Poll `GET /v1/admin/sanctions/status` or
    `GET /v1/health` to see when the refresh completes.

    Args:
        force: If true, re-download even if data is fresh.
    """
    screener = get_screener()

    if not force and not screener._is_stale():
        status = screener.status()
        return {
            "status": "skipped",
            "reason": "Data is fresh — pass ?force=true to override",
            "address_count": status["address_count"],
            "last_updated": status["last_updated"],
        }

    # Run the blocking refresh in a thread so the event loop stays free
    asyncio.create_task(_run_refresh(screener, force=force))

    return {
        "status": "refresh_started",
        "message": "OFAC SDN refresh running in background. "
                   "Check GET /v1/admin/sanctions/status for progress.",
        "force": force,
    }


async def _run_refresh(screener, force: bool = False) -> None:
    """Thin async wrapper so refresh() (sync, blocking) runs off the event loop."""
    try:
        ok = await asyncio.to_thread(screener.refresh, force)
        if ok:
            logger.info(
                f"Background OFAC refresh complete: {screener.address_count} addresses"
            )
        else:
            logger.warning("Background OFAC refresh failed — cached data still active")
    except Exception as exc:
        logger.error(f"Background OFAC refresh raised an exception: {exc}")
