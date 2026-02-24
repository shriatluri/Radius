"""
API routes for Radius.

Each module contains routes for a specific domain.
Routes are registered to the main app using APIRouter.
"""

from fastapi import APIRouter

from . import transactions, wallets, travel_rule, reports, api_keys, health, payments, admin

# Create main API router with /v1 prefix
api_router = APIRouter(prefix="/v1")

# Include all domain routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(transactions.router, tags=["Transactions"])
api_router.include_router(wallets.router, tags=["Wallets"])
api_router.include_router(travel_rule.router, tags=["Travel Rule"])
api_router.include_router(reports.router, tags=["Reports"])
api_router.include_router(api_keys.router, tags=["API Keys"])
api_router.include_router(payments.router, tags=["Payments"])
api_router.include_router(admin.router, tags=["Admin"])

__all__ = ["api_router"]
