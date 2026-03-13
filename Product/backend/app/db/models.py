"""
SQLAlchemy database models for Radius compliance platform.

These models define the database schema. Each class represents a table,
and each attribute represents a column.

Key Design Decisions:
1. UUIDs as primary keys - Better for distributed systems, no sequential guessing
2. Timestamps on everything - Critical for audit trails
3. JSONB for flexible data - Travel Rule payloads, metadata vary by jurisdiction
4. Indexes on frequently queried columns - business_id, status, created_at
"""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


# For SQLite compatibility, we use String for UUID and JSON
# In production with PostgreSQL, you'd use native UUID and JSONB
def generate_uuid():
    return str(uuid.uuid4())


class Business(Base):
    """
    A company that has signed up to use Radius.

    Each Business gets a random ID (biz_a3f9c2) as its primary key.
    The human-readable name and email live here — not on the APIKey rows.
    One Business can have many APIKeys (sandbox + live, multiple environments).

    plan: "sandbox" (default) or "live" (manually upgraded by Radius team after review).
    """
    __tablename__ = "businesses"

    id = Column(String(20), primary_key=True)           # e.g. biz_a3f9c2
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    intended_use = Column(Text, nullable=True)
    plan = Column(String(20), nullable=False, default="sandbox")  # sandbox | live
    created_at = Column(DateTime, nullable=False, default=func.now())


class APIKey(Base):
    """
    API keys for authentication.

    Each key belongs to a business and has scopes defining
    what operations it can perform.
    """
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    key_prefix = Column(String(12), nullable=False)  # "sk_test_" or "sk_live_"
    business_id = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=True)  # Human-readable name
    scopes = Column(Text, nullable=False, default="read,write")  # Comma-separated
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    expires_at = Column(DateTime, nullable=True)

    # Index for looking up active keys by business
    __table_args__ = (
        Index("ix_api_keys_business_active", "business_id", "is_active"),
    )


class Transaction(Base):
    """
    Core transaction record.

    This is the main entity - every payment that goes through
    Radius gets a transaction record for compliance tracking.
    """
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    external_id = Column(String(255), unique=True, nullable=True, index=True)

    # Business context
    business_id = Column(String(100), nullable=False, index=True)
    direction = Column(String(20), nullable=False)  # "inbound" or "outbound"

    # Entities involved
    from_entity_type = Column(String(50), nullable=False)
    from_entity_id = Column(String(255), nullable=False)
    from_wallet = Column(String(255), nullable=True, index=True)
    from_jurisdiction = Column(String(10), nullable=True)

    to_entity_type = Column(String(50), nullable=False)
    to_entity_id = Column(String(255), nullable=False)
    to_wallet = Column(String(255), nullable=True, index=True)
    to_jurisdiction = Column(String(10), nullable=True)

    # Transaction details
    amount = Column(Numeric(36, 18), nullable=False)  # Supports crypto precision
    asset = Column(String(50), nullable=False)
    chain = Column(String(50), nullable=False)
    purpose = Column(String(255), nullable=True)

    # Compliance results
    status = Column(String(20), nullable=False, default="pending", index=True)
    risk_score = Column(Integer, nullable=False, default=0)
    risk_level = Column(String(20), nullable=False, default="low")
    sanctions_result = Column(String(20), nullable=False, default="unknown")

    # Travel Rule
    travel_rule_status = Column(String(30), nullable=False, default="not_required")
    travel_rule_jurisdiction = Column(String(10), nullable=True)
    travel_rule_threshold = Column(String(50), nullable=True)

    # On-chain data (added after execution)
    tx_hash = Column(String(255), nullable=True, index=True)
    executed_at = Column(DateTime, nullable=True)

    # Extra data (flexible JSON for additional data)
    extra_data = Column(Text, nullable=True)  # JSON string

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    audit_record = relationship("AuditRecord", back_populates="transaction", uselist=False)

    __table_args__ = (
        Index("ix_transactions_business_status", "business_id", "status"),
        Index("ix_transactions_business_created", "business_id", "created_at"),
    )


class AuditRecord(Base):
    """
    Immutable audit record for each transaction.

    This is the compliance-critical record that auditors review.
    Once created, these should never be modified - only appended to.
    """
    __tablename__ = "audit_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    transaction_id = Column(
        String(36),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Snapshot of transaction data at time of audit
    business_id = Column(String(100), nullable=False, index=True)
    from_entity = Column(String(255), nullable=False)
    to_entity = Column(String(255), nullable=False)
    from_wallet = Column(String(255), nullable=True)
    to_wallet = Column(String(255), nullable=True)
    amount = Column(Numeric(36, 18), nullable=False)
    asset = Column(String(50), nullable=False)
    purpose = Column(String(255), nullable=True)

    # Compliance snapshot
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(20), nullable=False)
    sanctions_result = Column(String(20), nullable=False)
    travel_rule_status = Column(String(30), nullable=False)

    # Execution data
    tx_hash = Column(String(255), nullable=True)
    reconciliation_status = Column(String(20), nullable=False, default="unmatched")

    # Approvals stored as JSON array
    approvals = Column(Text, nullable=True)  # JSON string

    # Timestamps - created_at is immutable
    timestamp = Column(DateTime, nullable=False, default=func.now())

    # Relationship
    transaction = relationship("Transaction", back_populates="audit_record")

    __table_args__ = (
        Index("ix_audit_records_business_timestamp", "business_id", "timestamp"),
    )


class WalletVerification(Base):
    """
    Record of wallet ownership verification.

    When a user proves they control a wallet by signing a message,
    we store the verification here with an expiration date.
    """
    __tablename__ = "wallet_verifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    wallet = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(255), nullable=False, index=True)

    # Verification details
    verification_status = Column(String(20), nullable=False, default="pending")
    recovered_address = Column(String(255), nullable=True)

    # Validity period
    verified_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())

    __table_args__ = (
        Index("ix_wallet_verifications_wallet_entity", "wallet", "entity_id"),
    )


class TravelRuleProof(Base):
    """
    Record of Travel Rule data transmission.

    When we send originator/beneficiary data to a counterparty VASP,
    we store proof of the transmission here.
    """
    __tablename__ = "travel_rule_proofs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    transaction_id = Column(
        String(36),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Transmission status
    status = Column(String(20), nullable=False, default="pending")

    # Data sent (encrypted or hashed in production)
    originator_data = Column(Text, nullable=True)  # JSON string
    beneficiary_data = Column(Text, nullable=True)  # JSON string
    beneficiary_vasp = Column(Text, nullable=True)  # JSON string

    # Response from counterparty
    counterparty_response = Column(Text, nullable=True)
    counterparty_proof_id = Column(String(255), nullable=True)

    # Timestamps
    transmitted_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())


class User(Base):
    """
    A dashboard user authenticated via Clerk.

    Maps a Clerk user ID to a Business, enabling email+password / OAuth
    login for compliance officers, finance teams, and auditors.
    """
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    clerk_user_id = Column(String(255), unique=True, nullable=False, index=True)
    business_id = Column(String(20), ForeignKey("businesses.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="member")  # member | admin
    created_at = Column(DateTime, nullable=False, default=func.now())

    __table_args__ = (
        Index("ix_users_business_role", "business_id", "role"),
    )


class RateLimitBucket(Base):
    """
    Rate limiting tracking per API key.

    Uses token bucket algorithm - each key gets a bucket
    that refills over time.
    """
    __tablename__ = "rate_limit_buckets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    api_key_id = Column(String(36), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)

    # Token bucket state
    tokens = Column(Integer, nullable=False, default=100)
    last_refill = Column(DateTime, nullable=False, default=func.now())

    __table_args__ = (
        Index("ix_rate_limit_key_endpoint", "api_key_id", "endpoint", unique=True),
    )
