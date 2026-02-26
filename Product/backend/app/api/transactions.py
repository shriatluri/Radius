"""
Transaction endpoints.

Handles transaction ingestion, listing, annotation, and audit records.
"""

import json
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core import APIKeyInfo, require_api_key, RadiusError, RateLimitResult
from app.core.auth import check_scope
from app.core.logging import set_business_id
from app.core.config import settings
from app.db import get_db, TransactionRepository, AuditRecordRepository
from app.schemas import (
    AuditApproval,
    AuditRecord,
    PaymentAnnotateRequest,
    PaymentAnnotateResponse,
    TransactionIngestRequest,
    TransactionIngestResponse,
    TransactionListResponse,
    TransactionSummary,
    TravelRuleInfo,
)
from app.services import score_transaction, check_travel_rule

from .dependencies import apply_rate_limit, add_rate_limit_headers

# Legacy in-memory storage (for fallback)
from app.storage import STORE

router = APIRouter(prefix="/transactions")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@router.post("/ingest", response_model=TransactionIngestResponse)
def ingest_transaction(
    payload: TransactionIngestRequest,
    response: Response,
    auth: APIKeyInfo = Depends(require_api_key),
    db: Session = Depends(get_db),
    rate_limit: RateLimitResult = Depends(apply_rate_limit),
    _: None = Depends(check_scope("transactions:write")),
) -> TransactionIngestResponse:
    """
    Ingest a transaction for compliance checking.

    This endpoint:
    1. Checks for sanctions violations
    2. Calculates risk score
    3. Determines Travel Rule requirements based on jurisdiction
    4. Creates an audit record
    5. Returns compliance status and required actions

    Rate limited: Consumes 1 token per request.

    Note: business_id is automatically set from the authenticated API key.
    """
    add_rate_limit_headers(response, rate_limit)

    # Override business_id with authenticated business for security
    payload.business_id = auth.business_id

    # Stamp all log lines for this request with the tenant's business_id
    set_business_id(auth.business_id)

    if settings.use_database:
        return _ingest_transaction_db(payload, db)
    else:
        return _ingest_transaction_memory(payload)


def _ingest_transaction_db(
    payload: TransactionIngestRequest,
    db: Session,
) -> TransactionIngestResponse:
    """Database-backed transaction ingestion."""
    txn_repo = TransactionRepository(db)

    # Idempotency: if external_id already exists, return existing
    if payload.external_id:
        existing = txn_repo.get_by_external_id(payload.external_id)
        if existing:
            travel_rule_info = TravelRuleInfo(
                status=existing.travel_rule_status,
                threshold_exceeded=existing.travel_rule_status != "not_required",
                applicable_threshold=existing.travel_rule_threshold or "0",
                threshold_currency="USD",
                jurisdiction=existing.travel_rule_jurisdiction or "UNKNOWN",
                self_hosted_verification_needed=False,
                notes=None,
            )

            audit_id = existing.audit_record.id if existing.audit_record else _new_id("aud")

            return TransactionIngestResponse(
                transaction_id=existing.id,
                status=existing.status,
                risk_score=existing.risk_score,
                risk_level=existing.risk_level,
                sanctions_result=existing.sanctions_result,
                travel_rule=travel_rule_info,
                required_actions=[],
                audit_record_id=audit_id,
            )

    # Risk scoring
    risk = score_transaction(
        payload.amount,
        payload.chain,
        from_wallet=payload.from_entity.wallet,
        to_wallet=payload.to_entity.wallet,
    )

    # Travel Rule check
    amount_usd = Decimal(payload.amount)
    travel_rule_result = check_travel_rule(
        amount_usd=amount_usd,
        originator_jurisdiction=payload.from_entity.jurisdiction,
        beneficiary_jurisdiction=payload.to_entity.jurisdiction,
        originator_entity_type=payload.from_entity.type,
        beneficiary_entity_type=payload.to_entity.type,
        originator_wallet=payload.from_entity.wallet,
        beneficiary_wallet=payload.to_entity.wallet,
    )

    # Combine required actions
    all_required_actions = list(risk.required_actions)
    for action in travel_rule_result.required_actions:
        if action not in all_required_actions:
            all_required_actions.append(action)

    # Build extra_data — stores rich sanctions detail when blocked
    extra_data: dict = {}
    if risk.sanctions_result == "failed":
        extra_data["sanctions"] = {
            "sdn_name": risk.sdn_name,
            "sdn_id": risk.sdn_id,
            "sdn_program": risk.sdn_program,
            "list_source": risk.list_source,
            "reason": risk.sanctions_reason,
        }

    # Create transaction in database
    transaction = txn_repo.create(
        business_id=payload.business_id,
        direction=payload.direction,
        from_entity=payload.from_entity.dict(),
        to_entity=payload.to_entity.dict(),
        amount=payload.amount,
        asset=payload.asset,
        chain=payload.chain,
        risk_score=risk.score,
        risk_level=risk.level,
        sanctions_result=risk.sanctions_result,
        travel_rule_status=travel_rule_result.status,
        travel_rule_jurisdiction=travel_rule_result.jurisdiction,
        travel_rule_threshold=f"{travel_rule_result.applicable_threshold} {travel_rule_result.threshold_currency}",
        purpose=payload.purpose,
        external_id=payload.external_id,
        metadata=payload.metadata,
        extra_data=extra_data if extra_data else None,
    )

    travel_rule_info = TravelRuleInfo(
        status=travel_rule_result.status,
        threshold_exceeded=travel_rule_result.threshold_exceeded,
        applicable_threshold=str(travel_rule_result.applicable_threshold),
        threshold_currency=travel_rule_result.threshold_currency,
        jurisdiction=travel_rule_result.jurisdiction,
        self_hosted_verification_needed=travel_rule_result.self_hosted_verification_needed,
        notes=travel_rule_result.notes,
    )

    return TransactionIngestResponse(
        transaction_id=transaction.id,
        status=transaction.status,
        risk_score=transaction.risk_score,
        risk_level=transaction.risk_level,
        sanctions_result=transaction.sanctions_result,
        travel_rule=travel_rule_info,
        required_actions=all_required_actions,
        audit_record_id=transaction.audit_record.id,
    )


def _ingest_transaction_memory(
    payload: TransactionIngestRequest,
) -> TransactionIngestResponse:
    """In-memory transaction ingestion (legacy fallback)."""
    if payload.external_id:
        existing_txn_id = STORE.external_id_index.get(payload.external_id)
        if existing_txn_id:
            existing = STORE.transactions[existing_txn_id]
            return TransactionIngestResponse(
                transaction_id=existing_txn_id,
                status=existing["status"],
                risk_score=existing["risk_score"],
                risk_level=existing["risk_level"],
                sanctions_result=existing["sanctions_result"],
                travel_rule=TravelRuleInfo(**existing["travel_rule"]),
                required_actions=existing.get("required_actions", []),
                audit_record_id=existing["audit_record_id"],
            )

    risk = score_transaction(
        payload.amount,
        payload.chain,
        from_wallet=payload.from_entity.wallet,
        to_wallet=payload.to_entity.wallet,
    )

    amount_usd = Decimal(payload.amount)
    travel_rule_result = check_travel_rule(
        amount_usd=amount_usd,
        originator_jurisdiction=payload.from_entity.jurisdiction,
        beneficiary_jurisdiction=payload.to_entity.jurisdiction,
        originator_entity_type=payload.from_entity.type,
        beneficiary_entity_type=payload.to_entity.type,
        originator_wallet=payload.from_entity.wallet,
        beneficiary_wallet=payload.to_entity.wallet,
    )

    transaction_id = _new_id("txn")
    audit_record_id = _new_id("aud")

    all_required_actions = list(risk.required_actions)
    for action in travel_rule_result.required_actions:
        if action not in all_required_actions:
            all_required_actions.append(action)

    if risk.sanctions_result == "failed":
        status = "blocked"
    elif risk.level in {"low", "medium"}:
        status = "pending"
    else:
        status = "blocked"

    travel_rule_info = TravelRuleInfo(
        status=travel_rule_result.status,
        threshold_exceeded=travel_rule_result.threshold_exceeded,
        applicable_threshold=str(travel_rule_result.applicable_threshold),
        threshold_currency=travel_rule_result.threshold_currency,
        jurisdiction=travel_rule_result.jurisdiction,
        self_hosted_verification_needed=travel_rule_result.self_hosted_verification_needed,
        notes=travel_rule_result.notes,
    )

    STORE.transactions[transaction_id] = {
        "payload": payload.dict(),
        "status": status,
        "risk_score": risk.score,
        "risk_level": risk.level,
        "sanctions_result": risk.sanctions_result,
        "travel_rule": travel_rule_info.dict(),
        "required_actions": all_required_actions,
        "audit_record_id": audit_record_id,
    }

    if payload.external_id:
        STORE.external_id_index[payload.external_id] = transaction_id

    audit = AuditRecord(
        transaction_id=transaction_id,
        business_id=payload.business_id,
        from_entity=payload.from_entity.entity_id,
        to_entity=payload.to_entity.entity_id,
        wallets={
            "from": payload.from_entity.wallet,
            "to": payload.to_entity.wallet,
        },
        amount=payload.amount,
        asset=payload.asset,
        purpose=payload.purpose,
        risk_score=risk.score,
        risk_level=risk.level,
        sanctions_result=risk.sanctions_result,
        travel_rule_status=travel_rule_result.status,
        tx_hash=None,
        approvals=[
            AuditApproval(
                type="policy",
                result="approved" if status != "blocked" else "blocked",
                rule_id="rule_low_risk_auto",
            )
        ],
        reconciliation_status="unmatched",
    )
    STORE.audit_records[audit_record_id] = audit

    return TransactionIngestResponse(
        transaction_id=transaction_id,
        status=status,
        risk_score=risk.score,
        risk_level=risk.level,
        sanctions_result=risk.sanctions_result,
        travel_rule=travel_rule_info,
        required_actions=all_required_actions,
        audit_record_id=audit_record_id,
    )


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    auth: APIKeyInfo = Depends(require_api_key),
    db: Session = Depends(get_db),
    status: str | None = None,
    risk_level: str | None = None,
    limit: int = 50,
    offset: int = 0,
    _: None = Depends(check_scope("transactions:read")),
) -> TransactionListResponse:
    """
    List transactions with optional filtering.

    Automatically scoped to the authenticated business's transactions only.
    """
    if settings.use_database:
        txn_repo = TransactionRepository(db)
        # Automatically filter by authenticated business_id
        transactions, total = txn_repo.list_transactions(
            business_id=auth.business_id,  # Scoped to authenticated business
            status=status,
            risk_level=risk_level,
            limit=limit,
            offset=offset,
        )

        results = [
            TransactionSummary(
                transaction_id=txn.id,
                external_id=txn.external_id,
                status=txn.status,
                business_id=txn.business_id,
                amount=str(txn.amount),
                asset=txn.asset,
                chain=txn.chain,
                risk_level=txn.risk_level,
                created_at=txn.created_at.isoformat() + "Z",
            )
            for txn in transactions
        ]

        return TransactionListResponse(
            transactions=results,
            total=total,
            limit=limit,
            offset=offset,
        )

    # Fallback to in-memory
    results = []
    for txn_id, txn in STORE.transactions.items():
        payload = txn["payload"]
        if status and txn["status"] != status:
            continue
        if risk_level and txn["risk_level"] != risk_level:
            continue
        if auth.business_id and payload.get("business_id") != auth.business_id:
            continue

        audit = STORE.audit_records.get(txn["audit_record_id"])
        created_at = audit.timestamp if audit else datetime.utcnow().isoformat() + "Z"

        results.append(
            TransactionSummary(
                transaction_id=txn_id,
                external_id=payload.get("external_id"),
                status=txn["status"],
                business_id=payload["business_id"],
                amount=payload["amount"],
                asset=payload["asset"],
                chain=payload["chain"],
                risk_level=txn["risk_level"],
                created_at=created_at,
            )
        )

    total = len(results)
    paginated = results[offset : offset + limit]

    return TransactionListResponse(
        transactions=paginated,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/{transaction_id}/annotate", response_model=PaymentAnnotateResponse)
def annotate_payment(
    transaction_id: str,
    payload: PaymentAnnotateRequest,
    auth: APIKeyInfo = Depends(require_api_key),
    db: Session = Depends(get_db),
    _: None = Depends(check_scope("transactions:write")),
) -> PaymentAnnotateResponse:
    """
    Annotate a transaction with on-chain execution data.

    Call this after the transaction has been executed on-chain
    to link the tx_hash and mark the transaction as completed.
    """
    if settings.use_database:
        txn_repo = TransactionRepository(db)
        transaction = txn_repo.update_with_tx_hash(
            transaction_id=payload.transaction_id,
            tx_hash=payload.tx_hash,
            executed_at=payload.executed_at,
        )
        if not transaction:
            raise RadiusError("transaction_not_found", "Transaction not found", 404)

        audit_id = transaction.audit_record.id if transaction.audit_record else ""
        return PaymentAnnotateResponse(
            transaction_id=payload.transaction_id,
            status="completed",
            audit_record_id=audit_id,
        )

    # Fallback to in-memory
    txn = STORE.transactions.get(payload.transaction_id)
    if not txn:
        raise RadiusError("transaction_not_found", "Transaction not found", 404)

    audit_id = txn["audit_record_id"]
    audit = STORE.audit_records.get(audit_id)
    if not audit:
        raise RadiusError("audit_record_not_found", "Audit record not found", 404)

    audit.tx_hash = payload.tx_hash
    audit.timestamp = payload.executed_at
    audit.reconciliation_status = "matched"
    txn["status"] = "completed"

    return PaymentAnnotateResponse(
        transaction_id=payload.transaction_id,
        status="completed",
        audit_record_id=audit_id,
    )


@router.get("/{transaction_id}/audit", response_model=AuditRecord)
def get_audit_record(
    transaction_id: str,
    auth: APIKeyInfo = Depends(require_api_key),
    db: Session = Depends(get_db),
    _: None = Depends(check_scope("transactions:read")),
) -> AuditRecord:
    """
    Get the audit record for a specific transaction.

    Automatically scoped to the authenticated business's transactions only.
    """
    if settings.use_database:
        audit_repo = AuditRecordRepository(db)
        db_audit = audit_repo.get_by_transaction_id(transaction_id)
        if not db_audit:
            raise RadiusError("audit_record_not_found", "Audit record not found", 404)

        # Security check: ensure the audit record belongs to the authenticated business
        if db_audit.business_id != auth.business_id:
            raise RadiusError("audit_record_not_found", "Audit record not found", 404)

        approvals = json.loads(db_audit.approvals) if db_audit.approvals else []
        return AuditRecord(
            transaction_id=db_audit.transaction_id,
            business_id=db_audit.business_id,
            from_entity=db_audit.from_entity,
            to_entity=db_audit.to_entity,
            wallets={"from": db_audit.from_wallet, "to": db_audit.to_wallet},
            amount=str(db_audit.amount),
            asset=db_audit.asset,
            purpose=db_audit.purpose,
            risk_score=db_audit.risk_score,
            risk_level=db_audit.risk_level,
            sanctions_result=db_audit.sanctions_result,
            travel_rule_status=db_audit.travel_rule_status,
            tx_hash=db_audit.tx_hash,
            timestamp=db_audit.timestamp.isoformat() + "Z",
            approvals=[AuditApproval(**a) for a in approvals],
            reconciliation_status=db_audit.reconciliation_status,
        )

    # Fallback to in-memory
    for audit in STORE.audit_records.values():
        if audit.transaction_id == transaction_id:
            # Security check: ensure belongs to authenticated business
            if audit.business_id != auth.business_id:
                raise RadiusError("audit_record_not_found", "Audit record not found", 404)
            return audit
    raise RadiusError("audit_record_not_found", "Audit record not found", 404)
