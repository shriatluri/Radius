"""
Public signup endpoint — no authentication required.

POST /v1/signup

Accepts two formats:
  1. Direct JSON  { "business_name": "...", "email": "...", "intended_use": "..." }
  2. Tally webhook payload (sent automatically when someone submits the Tally form)

Both paths produce the same result:
  - A Business record is created in the database
  - A sandbox API key is generated and hashed (plaintext returned once only)
  - A welcome email is sent via Resend with the key

Why a single endpoint for both formats?
  The Tally form is the customer-facing intake. The direct JSON format lets
  us call the same endpoint programmatically (tests, internal provisioning).
  Normalising in one place means the business logic runs identically either way.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core import RadiusError
from app.core.auth import generate_api_key
from app.core.logging import set_business_id
from app.db import get_db, BusinessRepository, APIKeyRepository
from app.schemas.signup import SignupRequest, SignupResponse, TallyWebhookPayload
from app.services.email import send_welcome_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/signup")

# Scopes granted to every new sandbox key.
# Full write + read access so developers can explore the whole API.
_SANDBOX_SCOPES = "transactions:write,transactions:read,reports:read"


@router.post("", response_model=SignupResponse, status_code=201)
async def signup(request: Request, db: Session = Depends(get_db)) -> SignupResponse:
    """
    Sign up for a Radius sandbox account.

    Accepts direct JSON or a Tally form webhook. Returns a sandbox API key
    that is shown exactly once — store it immediately.

    Rate limited: intentionally generous (signup is a rare action).
    No auth required — this is the entry point.
    """
    body: Dict[str, Any] = await request.json()
    signup_data = _parse_body(body)
    return _run_signup(signup_data, db)


def _parse_body(body: Dict[str, Any]) -> SignupRequest:
    """
    Detect whether the request body is a Tally webhook or direct JSON,
    and normalise both into a SignupRequest.

    Tally webhooks have a specific shape: { eventId, eventType, data: { fields: [...] } }
    Direct JSON has: { business_name, email, intended_use? }
    """
    # Detect Tally by the presence of data.fields
    if "data" in body and "fields" in body.get("data", {}):
        return _parse_tally(TallyWebhookPayload(**body))

    # Otherwise treat as direct JSON
    return SignupRequest(**body)


def _parse_tally(payload: TallyWebhookPayload) -> SignupRequest:
    """
    Extract signup fields from a Tally webhook payload.

    Maps field labels to our internal fields. The Tally form must use these
    exact labels (case-insensitive match):
        "Company name"  → business_name
        "Email"         → email
        "Intended use"  → intended_use (optional)
    """
    fields = {f.label.lower().strip(): f.value for f in payload.data.fields}

    business_name = (
        fields.get("company name")
        or fields.get("business name")
        or fields.get("company")
        or ""
    )
    email = (
        fields.get("email")
        or fields.get("work email")
        or fields.get("email address")
        or ""
    )
    intended_use = (
        fields.get("intended use")
        or fields.get("how do you plan to use radius?")
        or fields.get("use case")
        or None
    )

    if not business_name or not email:
        raise RadiusError(
            "invalid_tally_payload",
            "Could not extract 'Company name' and 'Email' from Tally fields. "
            "Check the field labels in your Tally form.",
            400,
        )

    return SignupRequest(business_name=business_name, email=email, intended_use=intended_use)


def _run_signup(data: SignupRequest, db: Session) -> SignupResponse:
    """
    Core signup logic — identical regardless of intake format.

    1. Check email isn't already registered
    2. Create Business record
    3. Generate sandbox API key
    4. Send welcome email
    5. Return key (plaintext, once only)
    """
    biz_repo = BusinessRepository(db)
    key_repo = APIKeyRepository(db)

    # Duplicate check — friendly error instead of DB constraint violation
    if biz_repo.get_by_email(data.email):
        raise RadiusError(
            "email_already_registered",
            f"An account already exists for {data.email}. "
            "Check your inbox for your existing API key, or contact hello@getradius.com.",
            409,
        )

    # Create business
    business = biz_repo.create(
        name=data.business_name,
        email=data.email,
        intended_use=data.intended_use,
    )

    set_business_id(business.id)

    logger.info(
        "business_created",
        extra={
            "event": "business_created",
            "business_id": business.id,
            "plan": "sandbox",
        },
    )

    # Generate sandbox key
    plaintext_key, key_hash = generate_api_key(prefix="sk_sandbox_")

    db_key = key_repo.create(
        key_hash=key_hash,
        key_prefix="sk_sandbox_",
        business_id=business.id,
        name=f"{data.business_name} — Sandbox",
        scopes=_SANDBOX_SCOPES,
    )

    logger.info(
        "sandbox_key_created",
        extra={
            "event": "sandbox_key_created",
            "business_id": business.id,
            "key_id": db_key.id,
        },
    )

    # Send welcome email (non-blocking — a failure here doesn't fail the signup)
    email_sent = send_welcome_email(
        to_email=data.email,
        business_name=data.business_name,
        api_key=plaintext_key,
        business_id=business.id,
    )

    return SignupResponse(
        business_id=business.id,
        business_name=business.name,
        api_key=plaintext_key,
        key_id=db_key.id,
        plan="sandbox",
        email_sent=email_sent,
    )
