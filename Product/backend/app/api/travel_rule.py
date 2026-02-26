"""
Travel Rule endpoints.
"""

from decimal import Decimal
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Query

from app.core import APIKeyInfo, require_api_key
from app.core.auth import check_scope
from app.schemas import TravelRuleTransmitRequest, TravelRuleTransmitResponse
from app.services import (
    check_travel_rule,
    get_required_data_fields,
    Jurisdiction,
    JURISDICTION_RULES,
)
from app.storage import STORE

router = APIRouter(prefix="/travel-rule")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@router.post("/transmit", response_model=TravelRuleTransmitResponse)
def travel_rule_transmit(
    payload: TravelRuleTransmitRequest,
    auth: APIKeyInfo = Depends(require_api_key),
    _: None = Depends(check_scope("transactions:write")),
) -> TravelRuleTransmitResponse:
    """Transmit Travel Rule data to counterparty VASP."""
    proof_id = _new_id("trp")
    STORE.travel_rule_proofs[proof_id] = payload.dict()
    return TravelRuleTransmitResponse(
        transaction_id=payload.transaction_id,
        travel_rule_status="sent",
        proof_id=proof_id,
    )


@router.get("/check")
def check_travel_rule_requirements(
    auth: APIKeyInfo = Depends(require_api_key),
    _: None = Depends(check_scope("transactions:read")),
    amount: str = Query(..., description="Transaction amount in USD"),
    originator_jurisdiction: Optional[str] = Query(None, description="ISO 3166-1 alpha-2 country code"),
    beneficiary_jurisdiction: Optional[str] = Query(None, description="ISO 3166-1 alpha-2 country code"),
    originator_entity_type: str = Query("user", description="Entity type: user, business, vasp"),
    beneficiary_entity_type: str = Query("user", description="Entity type: user, business, vasp"),
    involves_self_hosted: bool = Query(False, description="Whether self-hosted wallet is involved"),
):
    """
    Check Travel Rule requirements for a potential transaction.

    This endpoint allows pre-flight checks before submitting a transaction
    to determine what compliance requirements will apply.
    """
    amount_usd = Decimal(amount)

    result = check_travel_rule(
        amount_usd=amount_usd,
        originator_jurisdiction=originator_jurisdiction,
        beneficiary_jurisdiction=beneficiary_jurisdiction,
        originator_entity_type=originator_entity_type,
        beneficiary_entity_type=beneficiary_entity_type,
        originator_wallet="0x" + "0" * 40 if involves_self_hosted else None,
        beneficiary_wallet=None,
    )

    return {
        "status": result.status,
        "threshold_exceeded": result.threshold_exceeded,
        "applicable_threshold": str(result.applicable_threshold),
        "threshold_currency": result.threshold_currency,
        "jurisdiction": result.jurisdiction,
        "required_actions": result.required_actions,
        "self_hosted_verification_needed": result.self_hosted_verification_needed,
        "notes": result.notes,
        "required_data_fields": get_required_data_fields(result.jurisdiction),
    }


@router.get("/jurisdictions")
def list_travel_rule_jurisdictions(
    auth: APIKeyInfo = Depends(require_api_key),
    _: None = Depends(check_scope("transactions:read")),
):
    """
    List all supported jurisdictions with their Travel Rule requirements.

    Returns threshold amounts, currencies, and special requirements for each.
    """
    jurisdictions = []
    for jurisdiction, rule in JURISDICTION_RULES.items():
        if jurisdiction == Jurisdiction.UNKNOWN:
            continue
        jurisdictions.append({
            "code": jurisdiction.value,
            "threshold_amount": str(rule.threshold_amount),
            "threshold_currency": rule.threshold_currency,
            "threshold_usd_equivalent": str(rule.threshold_usd_equivalent),
            "requires_self_hosted_verification": rule.requires_self_hosted_verification,
            "self_hosted_verification_threshold": str(rule.self_hosted_verification_threshold) if rule.self_hosted_verification_threshold else None,
            "enforcement_date": rule.enforcement_date,
            "notes": rule.notes,
        })

    jurisdictions.sort(key=lambda x: x["code"])

    return {
        "jurisdictions": jurisdictions,
        "total": len(jurisdictions),
        "default_threshold": {
            "amount": "1000",
            "currency": "USD",
            "notes": "FATF Recommendation 16 default for unknown jurisdictions",
        },
    }
