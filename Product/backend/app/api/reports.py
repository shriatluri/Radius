"""
Report export endpoints.
"""

import csv
import io
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core import APIKeyInfo, require_api_key
from app.core.auth import check_scope
from app.core.config import settings
from app.db import get_db, AuditRecordRepository
from app.storage import STORE

router = APIRouter(prefix="/reports")

EXPORTS_DIR = Path(__file__).parent.parent.parent / "exports"


@router.get("/export")
def export_report(
    auth: APIKeyInfo = Depends(require_api_key),
    db: Session = Depends(get_db),
    format: str = Query("csv", regex="^(csv|json)$"),
    from_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    _: None = Depends(check_scope("reports:read")),
):
    """
    Export audit records as CSV or JSON.

    Automatically scoped to the authenticated business's data only.
    """

    def db_audit_to_dict(db_audit):
        return {
            "transaction_id": db_audit.transaction_id,
            "business_id": db_audit.business_id,
            "from_entity": db_audit.from_entity,
            "to_entity": db_audit.to_entity,
            "from_wallet": db_audit.from_wallet or "",
            "to_wallet": db_audit.to_wallet or "",
            "amount": str(db_audit.amount),
            "asset": db_audit.asset,
            "purpose": db_audit.purpose or "",
            "risk_score": db_audit.risk_score,
            "risk_level": db_audit.risk_level,
            "sanctions_result": db_audit.sanctions_result,
            "travel_rule_status": db_audit.travel_rule_status,
            "tx_hash": db_audit.tx_hash or "",
            "timestamp": db_audit.timestamp.isoformat() + "Z" if db_audit.timestamp else "",
            "reconciliation_status": db_audit.reconciliation_status,
        }

    records = []

    if settings.use_database:
        audit_repo = AuditRecordRepository(db)
        # Automatically filter by authenticated business_id
        db_records = audit_repo.list_for_export(
            business_id=auth.business_id,  # Scoped to authenticated business
            from_date=from_date,
            to_date=to_date,
        )

        if format == "json":
            return {"records": [db_audit_to_dict(r) for r in db_records], "count": len(db_records)}

        records = [db_audit_to_dict(r) for r in db_records]
    else:
        for audit in STORE.audit_records.values():
            # Filter by authenticated business_id
            if audit.business_id != auth.business_id:
                continue

            if audit.timestamp:
                record_date = audit.timestamp[:10]
                if from_date and record_date < from_date:
                    continue
                if to_date and record_date > to_date:
                    continue

            records.append(audit)

        records.sort(key=lambda r: r.timestamp or "", reverse=True)

        if format == "json":
            return {"records": [r.dict() for r in records], "count": len(records)}

    # Generate CSV for audit/compliance use
    # Ordered by importance for auditors
    output = io.StringIO()
    fieldnames = [
        "timestamp",
        "transaction_id",
        "from_entity",
        "to_entity",
        "amount",
        "asset",
        "purpose",
        "risk_score",
        "risk_level",
        "sanctions_result",
        "travel_rule_status",
        "reconciliation_status",
        "from_wallet",
        "to_wallet",
        "tx_hash",
        "business_id",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for record in records:
        if isinstance(record, dict):
            writer.writerow(record)
        else:
            writer.writerow({
                "transaction_id": record.transaction_id,
                "business_id": record.business_id,
                "from_entity": record.from_entity,
                "to_entity": record.to_entity,
                "from_wallet": record.wallets.get("from", ""),
                "to_wallet": record.wallets.get("to", ""),
                "amount": record.amount,
                "asset": record.asset,
                "purpose": record.purpose or "",
                "risk_score": record.risk_score,
                "risk_level": record.risk_level,
                "sanctions_result": record.sanctions_result,
                "travel_rule_status": record.travel_rule_status,
                "tx_hash": record.tx_hash or "",
                "timestamp": record.timestamp,
                "reconciliation_status": record.reconciliation_status,
            })

    output.seek(0)
    csv_content = output.getvalue()

    # Save to exports directory
    EXPORTS_DIR.mkdir(exist_ok=True)
    export_path = EXPORTS_DIR / "latest_audit_export.csv"
    export_path.write_text(csv_content)

    # Generate audit-friendly filename with business name and date range
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"acme_corp_compliance_audit_{today}"
    if from_date and to_date:
        filename = f"acme_corp_compliance_audit_{from_date}_to_{to_date}"
    elif from_date:
        filename = f"acme_corp_compliance_audit_from_{from_date}"
    elif to_date:
        filename = f"acme_corp_compliance_audit_to_{to_date}"
    filename += ".csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
