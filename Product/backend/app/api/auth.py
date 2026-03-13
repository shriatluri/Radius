"""
Authentication endpoints for dashboard users.

Provides /v1/auth/me for Clerk-authenticated users to retrieve
their business context after login.
"""

from fastapi import APIRouter, Depends

from app.core.auth import AuthInfo, require_auth
from app.db import get_db, BusinessRepository
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth")


@router.get("/me")
def get_current_user(
    auth: AuthInfo = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Return the authenticated user's business context.

    Works with both Clerk JWT and API key authentication.
    Dashboard uses this to display the business name in the header.
    """
    biz_repo = BusinessRepository(db)
    business = biz_repo.get_by_id(auth.business_id)

    return {
        "business_id": auth.business_id,
        "business_name": business.name if business else auth.business_id,
        "email": business.email if business else None,
        "auth_type": auth.auth_type,
        "scopes": auth.scopes,
    }
