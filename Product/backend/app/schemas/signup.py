"""
Signup request/response schemas.

Two intake formats are supported:
1. Direct JSON — from developers calling the API directly or from a custom form
2. Tally webhook — from Tally form submissions

Both are normalised into SignupRequest before processing.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    """Direct signup from a developer or custom form."""
    business_name: str
    email: EmailStr
    intended_use: Optional[str] = None


class TallyField(BaseModel):
    """A single field from a Tally form response."""
    key: str
    label: str
    type: str
    value: Any


class TallyWebhookData(BaseModel):
    """The data object inside a Tally webhook payload."""
    responseId: str
    fields: List[TallyField]


class TallyWebhookPayload(BaseModel):
    """
    Full Tally webhook payload shape.

    Tally sends this when a form is submitted. We detect this format
    by checking for the presence of `data.fields`.

    Expected field labels in the Tally form (configure these when building the form):
        - "Company name"   → business_name
        - "Email"          → email
        - "Intended use"   → intended_use (optional)
    """
    eventId: str
    eventType: str
    data: TallyWebhookData


class SignupResponse(BaseModel):
    """Returned after a successful signup."""
    business_id: str
    business_name: str
    api_key: str           # Plaintext — shown ONCE, never stored
    key_id: str
    plan: str              # "sandbox"
    email_sent: bool
    warning: str = "Store this API key securely. It will not be shown again."
