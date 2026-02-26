"""
Payments endpoints.

Handles payment annotation (linking on-chain data to transactions).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core import APIKeyInfo, require_api_key, RadiusError
from app.core.auth import check_scope
from app.core.config import settings
from app.db import get_db, TransactionRepository
from app.schemas import PaymentAnnotateRequest, PaymentAnnotateResponse
from app.storage import STORE

router = APIRouter(prefix="/payments")


@router.post("/annotate", response_model=PaymentAnnotateResponse)
def annotate_payment(
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
