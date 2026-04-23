"""Stdlib dataclass models for Radius API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Entity:
    """An entity involved in a transaction (sender or receiver)."""
    type: str  # "business", "user", "vasp", "unknown"
    entity_id: str
    wallet: Optional[str] = None
    jurisdiction: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"type": self.type, "entity_id": self.entity_id}
        if self.wallet is not None:
            d["wallet"] = self.wallet
        if self.jurisdiction is not None:
            d["jurisdiction"] = self.jurisdiction
        return d


@dataclass
class TravelRuleInfo:
    """Travel Rule compliance information."""
    status: str
    threshold_exceeded: bool
    applicable_threshold: str
    threshold_currency: str
    jurisdiction: str
    self_hosted_verification_needed: bool
    notes: Optional[str] = None


@dataclass
class IngestResponse:
    """Response from transaction ingestion."""
    transaction_id: str
    status: str
    risk_score: int
    risk_level: str
    sanctions_result: str
    travel_rule: TravelRuleInfo
    required_actions: List[str]
    audit_record_id: str


@dataclass
class AnnotateResponse:
    """Response from payment annotation."""
    transaction_id: str
    status: str
    audit_record_id: str


@dataclass
class AuditApproval:
    """An approval decision in an audit record."""
    type: str
    result: str
    rule_id: str


@dataclass
class AuditRecord:
    """Full audit record for compliance reporting."""
    transaction_id: str
    business_id: str
    from_entity: str
    to_entity: str
    wallets: Dict[str, Optional[str]]
    amount: str
    asset: str
    risk_score: int
    risk_level: str
    sanctions_result: str
    travel_rule_status: str
    reconciliation_status: str
    timestamp: str
    approvals: List[AuditApproval]
    purpose: Optional[str] = None
    tx_hash: Optional[str] = None


@dataclass
class TransactionSummary:
    """Summary of a transaction for list views."""
    transaction_id: str
    status: str
    business_id: str
    amount: str
    asset: str
    chain: str
    risk_level: str
    created_at: str
    external_id: Optional[str] = None


@dataclass
class TransactionListResponse:
    """Paginated list of transactions."""
    transactions: List[TransactionSummary]
    total: int
    limit: int
    offset: int


@dataclass
class WalletVerifyResponse:
    """Response from wallet verification."""
    wallet_id: str
    verification_status: str
    verified_at: Optional[str] = None
    expires_at: Optional[str] = None
    error: Optional[str] = None


@dataclass
class TravelRuleCheckResponse:
    """Response from Travel Rule pre-flight check."""
    status: str
    threshold_exceeded: bool
    applicable_threshold: str
    threshold_currency: str
    jurisdiction: str
    required_actions: List[str]
    self_hosted_verification_needed: bool
    notes: Optional[str] = None
    required_data_fields: Optional[List[str]] = None


@dataclass
class TravelRuleTransmitResponse:
    """Response from Travel Rule transmission."""
    transaction_id: str
    travel_rule_status: str
    proof_id: Optional[str] = None


@dataclass
class ReportExportResponse:
    """Response from JSON report export."""
    records: List[Dict[str, Any]]
    count: int


@dataclass
class HealthResponse:
    """Response from health check endpoint."""
    status: str
    version: str
    environment: str
    db_connected: bool
    sanctions_screening: Dict[str, Any]
