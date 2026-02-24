from __future__ import annotations

from typing import Dict

from app.db.models import AuditRecord


class InMemoryStore:
    def __init__(self) -> None:
        self.transactions: Dict[str, dict] = {}
        self.audit_records: Dict[str, AuditRecord] = {}
        self.wallet_verifications: Dict[str, dict] = {}
        self.travel_rule_proofs: Dict[str, dict] = {}
        # Index: external_id -> transaction_id for idempotency
        self.external_id_index: Dict[str, str] = {}


STORE = InMemoryStore()
