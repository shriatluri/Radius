"""
Transaction-related schemas.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, validator

from .common import Entity, parse_amount, utc_now


class TravelRuleInfo(BaseModel):
    """Travel Rule compliance information."""
    status: Literal["required", "not_required", "verification_required"]
    threshold_exceeded: bool
    applicable_threshold: str
    threshold_currency: str
    jurisdiction: str
    self_hosted_verification_needed: bool
    notes: Optional[str] = None


class TransactionIngestRequest(BaseModel):
    """Request to ingest a new transaction for compliance checking."""
    external_id: Optional[str] = None
    direction: Literal["outbound", "inbound"]
    business_id: str
    from_entity: Entity
    to_entity: Entity
    amount: str
    asset: str
    chain: str
    purpose: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator("amount")
    def validate_amount(cls, value: str) -> str:
        parse_amount(value)
        return value


class TransactionIngestResponse(BaseModel):
    """Response from transaction ingestion."""
    transaction_id: str
    status: Literal["pending", "approved", "blocked", "completed"]
    risk_score: int
    risk_level: Literal["low", "medium", "high", "critical"]
    sanctions_result: Literal["passed", "failed", "unknown"]
    travel_rule: TravelRuleInfo
    required_actions: List[str]
    audit_record_id: str


class PaymentAnnotateRequest(BaseModel):
    """Request to annotate a transaction with on-chain data."""
    transaction_id: str
    tx_hash: str
    executed_at: str
    provider_refs: Optional[Dict[str, str]] = None


class PaymentAnnotateResponse(BaseModel):
    """Response from payment annotation."""
    transaction_id: str
    status: Literal["completed"]
    audit_record_id: str


class AuditApproval(BaseModel):
    """An approval decision in an audit record."""
    type: str
    result: str
    rule_id: str


class AuditRecord(BaseModel):
    """Audit record for compliance reporting."""
    transaction_id: str
    business_id: str
    from_entity: str
    to_entity: str
    wallets: Dict[str, Optional[str]]
    amount: str
    asset: str
    purpose: Optional[str] = None
    risk_score: int
    risk_level: str
    sanctions_result: str
    travel_rule_status: str
    tx_hash: Optional[str] = None
    timestamp: str = Field(default_factory=utc_now)
    approvals: List[AuditApproval]
    reconciliation_status: str


class TransactionSummary(BaseModel):
    """Summary of a transaction for list views."""
    transaction_id: str
    external_id: Optional[str] = None
    status: str
    business_id: str
    amount: str
    asset: str
    chain: str
    risk_level: str
    created_at: str


class TransactionListResponse(BaseModel):
    """Paginated list of transactions."""
    transactions: List[TransactionSummary]
    total: int
    limit: int
    offset: int
