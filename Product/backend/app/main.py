"""
Radius Compliance API

Main application entry point.
"""

import asyncio
import logging
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core import RadiusError
from app.core.config import settings
from app.core.errors import radius_error_handler
from app.db import init_db

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Radius",
    version=settings.api_version,
    description="Payment attestation infrastructure. Turn stablecoin transfers into audit-ready financial records.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(RadiusError, radius_error_handler)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": exc.detail}},
    )


# Include API routes
app.include_router(api_router)


# Mount static files for frontend (production mode)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Initialize database and kick off background OFAC sanctions refresh.

    The OFAC refresh is non-blocking — the API serves traffic immediately
    using whatever cached data exists while the refresh runs in the background.
    If no cache exists yet (cold start), the screener lazy-loads on the first
    request that triggers a sanctions check.
    """
    if settings.use_database:
        init_db()
        logger.info("Database initialized")

    if settings.rate_limit_enabled:
        logger.info(f"Rate limiting enabled: {settings.rate_limit_tokens} req/burst")

    # Schedule OFAC refresh check without blocking startup
    asyncio.create_task(_startup_ofac_refresh())


async def _startup_ofac_refresh() -> None:
    """
    Background task: load OFAC screener from cache, refresh if stale.

    Cold start (no cache)   → download + parse in background thread (~2-3 min)
    Warm start (fresh cache) → load JSON index into memory (~1 sec)
    Warm start (stale cache) → load stale data immediately, then re-download
    """
    from app.services.ofac import get_screener

    screener = get_screener()

    if screener._is_stale():
        # Load whatever cached data exists first so checks don't block on download
        cached = screener._load_index_from_cache()
        if cached:
            screener._index = cached
            screener._loaded = True
            logger.info(
                f"OFAC: loaded stale cache ({len(cached)} addresses) — "
                "refreshing in background"
            )
        else:
            logger.info("OFAC: no cache found — will download on first sanctions check")

        # Now refresh (download + parse) in a thread so the event loop stays free
        ok = await asyncio.to_thread(screener.refresh, True)
        if ok:
            logger.info(
                f"OFAC startup refresh complete: {screener.address_count} addresses indexed"
            )
        else:
            logger.warning(
                "OFAC startup refresh failed — "
                f"{'stale cache active' if screener._loaded else 'no data available'}"
            )
    else:
        # Fresh cache: just load the JSON index (fast, no download)
        await asyncio.to_thread(screener.load)
        logger.info(
            f"OFAC: loaded {screener.address_count} addresses from cache "
            f"(last updated: {screener.last_updated})"
        )
