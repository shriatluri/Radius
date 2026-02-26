"""
Repository layer for database operations.

The repository pattern provides a clean abstraction over the database,
making it easy to:
1. Swap database implementations (e.g., for testing)
2. Keep business logic separate from data access
3. Centralize query logic

Each repository handles CRUD operations for one entity type.
"""

import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from . import models


def _generate_id(prefix: str) -> str:
    """Generate a prefixed ID like 'txn_abc123'."""
    return f"{prefix}_{uuid4().hex[:12]}"


class TransactionRepository:
    """
    Repository for Transaction operations.

    Handles creating, reading, updating transactions and their audit records.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        business_id: str,
        direction: str,
        from_entity: Dict[str, Any],
        to_entity: Dict[str, Any],
        amount: str,
        asset: str,
        chain: str,
        risk_score: int,
        risk_level: str,
        sanctions_result: str,
        travel_rule_status: str,
        travel_rule_jurisdiction: Optional[str] = None,
        travel_rule_threshold: Optional[str] = None,
        purpose: Optional[str] = None,
        external_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        extra_data: Optional[Dict] = None,
    ) -> models.Transaction:
        """
        Create a new transaction with its audit record.

        extra_data stores internal compliance data (e.g. SDN match details).
        metadata stores user-supplied context (e.g. invoice_id, country).
        Both are merged into the extra_data JSON column, keyed separately.
        """

        txn_id = _generate_id("txn")
        audit_id = _generate_id("aud")

        # Determine status based on risk
        if sanctions_result == "failed":
            status = "blocked"
        elif risk_level in ("low", "medium"):
            status = "pending"
        else:
            status = "blocked"

        # Merge user metadata and internal extra_data into the JSON column
        combined: Dict = {}
        if metadata:
            combined["metadata"] = metadata
        if extra_data:
            combined.update(extra_data)

        # Create transaction
        transaction = models.Transaction(
            id=txn_id,
            external_id=external_id,
            business_id=business_id,
            direction=direction,
            from_entity_type=from_entity.get("type", "unknown"),
            from_entity_id=from_entity.get("entity_id", ""),
            from_wallet=from_entity.get("wallet"),
            from_jurisdiction=from_entity.get("jurisdiction"),
            to_entity_type=to_entity.get("type", "unknown"),
            to_entity_id=to_entity.get("entity_id", ""),
            to_wallet=to_entity.get("wallet"),
            to_jurisdiction=to_entity.get("jurisdiction"),
            amount=Decimal(amount),
            asset=asset,
            chain=chain,
            purpose=purpose,
            status=status,
            risk_score=risk_score,
            risk_level=risk_level,
            sanctions_result=sanctions_result,
            travel_rule_status=travel_rule_status,
            travel_rule_jurisdiction=travel_rule_jurisdiction,
            travel_rule_threshold=travel_rule_threshold,
            extra_data=json.dumps(combined) if combined else None,
        )
        self.db.add(transaction)

        # Create audit record
        approvals = [
            {
                "type": "policy",
                "result": "approved" if status != "blocked" else "blocked",
                "rule_id": "rule_low_risk_auto",
            }
        ]

        audit_record = models.AuditRecord(
            id=audit_id,
            transaction_id=txn_id,
            business_id=business_id,
            from_entity=from_entity.get("entity_id", ""),
            to_entity=to_entity.get("entity_id", ""),
            from_wallet=from_entity.get("wallet"),
            to_wallet=to_entity.get("wallet"),
            amount=Decimal(amount),
            asset=asset,
            purpose=purpose,
            risk_score=risk_score,
            risk_level=risk_level,
            sanctions_result=sanctions_result,
            travel_rule_status=travel_rule_status,
            approvals=json.dumps(approvals),
        )
        self.db.add(audit_record)

        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    def get_by_id(self, transaction_id: str) -> Optional[models.Transaction]:
        """Get a transaction by ID."""
        return self.db.query(models.Transaction).filter(
            models.Transaction.id == transaction_id
        ).first()

    def get_by_external_id(self, external_id: str) -> Optional[models.Transaction]:
        """Get a transaction by external ID (for idempotency)."""
        return self.db.query(models.Transaction).filter(
            models.Transaction.external_id == external_id
        ).first()

    def list_transactions(
        self,
        business_id: Optional[str] = None,
        status: Optional[str] = None,
        risk_level: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[models.Transaction], int]:
        """List transactions with filtering and pagination."""

        query = self.db.query(models.Transaction)

        if business_id:
            query = query.filter(models.Transaction.business_id == business_id)
        if status:
            query = query.filter(models.Transaction.status == status)
        if risk_level:
            query = query.filter(models.Transaction.risk_level == risk_level)

        total = query.count()

        transactions = query.order_by(
            desc(models.Transaction.created_at)
        ).offset(offset).limit(limit).all()

        return transactions, total

    def update_with_tx_hash(
        self,
        transaction_id: str,
        tx_hash: str,
        executed_at: str,
    ) -> Optional[models.Transaction]:
        """Update transaction with on-chain data after execution."""

        transaction = self.get_by_id(transaction_id)
        if not transaction:
            return None

        transaction.tx_hash = tx_hash
        transaction.executed_at = datetime.fromisoformat(executed_at.replace("Z", "+00:00"))
        transaction.status = "completed"

        # Update audit record too
        if transaction.audit_record:
            transaction.audit_record.tx_hash = tx_hash
            transaction.audit_record.reconciliation_status = "matched"

        self.db.commit()
        self.db.refresh(transaction)

        return transaction


class AuditRecordRepository:
    """Repository for AuditRecord operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_transaction_id(self, transaction_id: str) -> Optional[models.AuditRecord]:
        """Get audit record by transaction ID."""
        return self.db.query(models.AuditRecord).filter(
            models.AuditRecord.transaction_id == transaction_id
        ).first()

    def list_for_export(
        self,
        business_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[models.AuditRecord]:
        """Get audit records for export with filtering."""

        query = self.db.query(models.AuditRecord)

        if business_id:
            query = query.filter(models.AuditRecord.business_id == business_id)

        if from_date:
            query = query.filter(models.AuditRecord.timestamp >= from_date)

        if to_date:
            query = query.filter(models.AuditRecord.timestamp <= to_date)

        return query.order_by(desc(models.AuditRecord.timestamp)).all()


class WalletVerificationRepository:
    """Repository for WalletVerification operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        wallet: str,
        entity_type: str,
        entity_id: str,
        verification_status: str,
        recovered_address: Optional[str] = None,
        verified_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
    ) -> models.WalletVerification:
        """Create a new wallet verification record."""

        verification = models.WalletVerification(
            id=_generate_id("wal"),
            wallet=wallet,
            entity_type=entity_type,
            entity_id=entity_id,
            verification_status=verification_status,
            recovered_address=recovered_address,
            verified_at=verified_at,
            expires_at=expires_at,
        )
        self.db.add(verification)
        self.db.commit()
        self.db.refresh(verification)

        return verification

    def get_valid_verification(
        self,
        wallet: str,
        entity_id: str,
    ) -> Optional[models.WalletVerification]:
        """Get a valid (non-expired) verification for a wallet."""
        return self.db.query(models.WalletVerification).filter(
            and_(
                models.WalletVerification.wallet == wallet,
                models.WalletVerification.entity_id == entity_id,
                models.WalletVerification.verification_status == "verified",
                models.WalletVerification.expires_at > datetime.utcnow(),
            )
        ).first()


class TravelRuleProofRepository:
    """Repository for TravelRuleProof operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        transaction_id: str,
        originator_data: Dict,
        beneficiary_data: Dict,
        beneficiary_vasp: Dict,
    ) -> models.TravelRuleProof:
        """Create a new travel rule proof record."""

        proof = models.TravelRuleProof(
            id=_generate_id("trp"),
            transaction_id=transaction_id,
            status="sent",
            originator_data=json.dumps(originator_data),
            beneficiary_data=json.dumps(beneficiary_data),
            beneficiary_vasp=json.dumps(beneficiary_vasp),
            transmitted_at=datetime.utcnow(),
        )
        self.db.add(proof)
        self.db.commit()
        self.db.refresh(proof)

        return proof

    def get_by_transaction_id(
        self,
        transaction_id: str,
    ) -> Optional[models.TravelRuleProof]:
        """Get travel rule proof by transaction ID."""
        return self.db.query(models.TravelRuleProof).filter(
            models.TravelRuleProof.transaction_id == transaction_id
        ).first()


class BusinessRepository:
    """Repository for Business operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        name: str,
        email: str,
        intended_use: Optional[str] = None,
    ) -> models.Business:
        """Create a new business. Raises ValueError if email already registered."""
        existing = self.get_by_email(email)
        if existing:
            raise ValueError(f"Email {email} is already registered")

        business = models.Business(
            id=_generate_id("biz"),
            name=name,
            email=email.lower().strip(),
            intended_use=intended_use,
            plan="sandbox",
        )
        self.db.add(business)
        self.db.commit()
        self.db.refresh(business)
        return business

    def get_by_email(self, email: str) -> Optional[models.Business]:
        """Look up a business by email address."""
        return self.db.query(models.Business).filter(
            models.Business.email == email.lower().strip()
        ).first()

    def get_by_id(self, business_id: str) -> Optional[models.Business]:
        """Look up a business by its ID."""
        return self.db.query(models.Business).filter(
            models.Business.id == business_id
        ).first()

    def upgrade_to_live(self, business_id: str) -> bool:
        """Manually upgrade a business from sandbox to live plan."""
        result = self.db.query(models.Business).filter(
            models.Business.id == business_id
        ).update({"plan": "live"})
        self.db.commit()
        return result > 0


class APIKeyRepository:
    """Repository for API key operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        key_hash: str,
        key_prefix: str,
        business_id: str,
        name: Optional[str] = None,
        scopes: str = "read,write",
        expires_at: Optional[datetime] = None,
    ) -> models.APIKey:
        """Create a new API key."""

        api_key = models.APIKey(
            id=_generate_id("key"),
            key_hash=key_hash,
            key_prefix=key_prefix,
            business_id=business_id,
            name=name,
            scopes=scopes,
            expires_at=expires_at,
        )
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)

        return api_key

    def get_by_hash(self, key_hash: str) -> Optional[models.APIKey]:
        """Get an API key by its hash."""
        return self.db.query(models.APIKey).filter(
            and_(
                models.APIKey.key_hash == key_hash,
                models.APIKey.is_active.is_(True),
            )
        ).first()

    def update_last_used(self, key_id: str) -> None:
        """Update the last_used_at timestamp."""
        self.db.query(models.APIKey).filter(
            models.APIKey.id == key_id
        ).update({"last_used_at": datetime.utcnow()})
        self.db.commit()

    def list_by_business(self, business_id: str) -> List[models.APIKey]:
        """List all API keys for a business."""
        return self.db.query(models.APIKey).filter(
            models.APIKey.business_id == business_id
        ).all()

    def revoke(self, key_id: str) -> bool:
        """Revoke (deactivate) an API key."""
        result = self.db.query(models.APIKey).filter(
            models.APIKey.id == key_id
        ).update({"is_active": False})
        self.db.commit()
        return result > 0
