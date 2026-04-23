"""Radius API client with resource-based namespacing."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from ._exceptions import raise_for_status
from ._models import (
    AnnotateResponse,
    AuditApproval,
    AuditRecord,
    Entity,
    HealthResponse,
    IngestResponse,
    ReportExportResponse,
    TransactionListResponse,
    TransactionSummary,
    TravelRuleCheckResponse,
    TravelRuleInfo,
    TravelRuleTransmitResponse,
    WalletVerifyResponse,
)
from ._version import __version__

_DEFAULT_BASE_URL = "https://api.getradius.com"


class _Resource:
    """Base for resource sub-objects that share the client's session."""

    def __init__(self, client: RadiusClient):
        self._client = client

    # Convenience shortcuts
    def _get(self, path: str, **kwargs):
        return self._client._request("GET", path, **kwargs)

    def _post(self, path: str, **kwargs):
        return self._client._request("POST", path, **kwargs)


# ── Transactions ──────────────────────────────────────────────────────────


class Transactions(_Resource):
    """client.transactions.*"""

    def ingest(
        self,
        *,
        direction: str,
        from_entity: Entity,
        to_entity: Entity,
        amount: str,
        asset: str,
        chain: str,
        business_id: str = "",
        external_id: Optional[str] = None,
        purpose: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IngestResponse:
        """Ingest a transaction for compliance checking.

        ``business_id`` is automatically set from your API key on the server
        side, so you can leave it empty.
        """
        body: Dict[str, Any] = {
            "direction": direction,
            "from_entity": from_entity.to_dict(),
            "to_entity": to_entity.to_dict(),
            "amount": amount,
            "asset": asset,
            "chain": chain,
            "business_id": business_id,
        }
        if external_id is not None:
            body["external_id"] = external_id
        if purpose is not None:
            body["purpose"] = purpose
        if metadata is not None:
            body["metadata"] = metadata

        data = self._post("/v1/transactions/ingest", json=body)
        tr = data["travel_rule"]
        return IngestResponse(
            transaction_id=data["transaction_id"],
            status=data["status"],
            risk_score=data["risk_score"],
            risk_level=data["risk_level"],
            sanctions_result=data["sanctions_result"],
            travel_rule=TravelRuleInfo(
                status=tr["status"],
                threshold_exceeded=tr["threshold_exceeded"],
                applicable_threshold=tr["applicable_threshold"],
                threshold_currency=tr["threshold_currency"],
                jurisdiction=tr["jurisdiction"],
                self_hosted_verification_needed=tr["self_hosted_verification_needed"],
                notes=tr.get("notes"),
            ),
            required_actions=data["required_actions"],
            audit_record_id=data["audit_record_id"],
        )

    def list(
        self,
        *,
        status: Optional[str] = None,
        risk_level: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> TransactionListResponse:
        """List transactions with optional filtering."""
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if status is not None:
            params["status"] = status
        if risk_level is not None:
            params["risk_level"] = risk_level

        data = self._get("/v1/transactions", params=params)
        return TransactionListResponse(
            transactions=[
                TransactionSummary(
                    transaction_id=t["transaction_id"],
                    status=t["status"],
                    business_id=t["business_id"],
                    amount=t["amount"],
                    asset=t["asset"],
                    chain=t["chain"],
                    risk_level=t["risk_level"],
                    created_at=t["created_at"],
                    external_id=t.get("external_id"),
                )
                for t in data["transactions"]
            ],
            total=data["total"],
            limit=data["limit"],
            offset=data["offset"],
        )

    def get_audit(self, transaction_id: str) -> AuditRecord:
        """Get the audit record for a specific transaction."""
        data = self._get(f"/v1/transactions/{transaction_id}/audit")
        return AuditRecord(
            transaction_id=data["transaction_id"],
            business_id=data["business_id"],
            from_entity=data["from_entity"],
            to_entity=data["to_entity"],
            wallets=data["wallets"],
            amount=data["amount"],
            asset=data["asset"],
            risk_score=data["risk_score"],
            risk_level=data["risk_level"],
            sanctions_result=data["sanctions_result"],
            travel_rule_status=data["travel_rule_status"],
            reconciliation_status=data["reconciliation_status"],
            timestamp=data["timestamp"],
            approvals=[
                AuditApproval(type=a["type"], result=a["result"], rule_id=a["rule_id"])
                for a in data.get("approvals", [])
            ],
            purpose=data.get("purpose"),
            tx_hash=data.get("tx_hash"),
        )


# ── Payments ──────────────────────────────────────────────────────────────


class Payments(_Resource):
    """client.payments.*"""

    def annotate(
        self,
        *,
        transaction_id: str,
        tx_hash: str,
        executed_at: str,
        provider_refs: Optional[Dict[str, str]] = None,
    ) -> AnnotateResponse:
        """Annotate a transaction with on-chain execution data."""
        body: Dict[str, Any] = {
            "transaction_id": transaction_id,
            "tx_hash": tx_hash,
            "executed_at": executed_at,
        }
        if provider_refs is not None:
            body["provider_refs"] = provider_refs

        data = self._post("/v1/payments/annotate", json=body)
        return AnnotateResponse(
            transaction_id=data["transaction_id"],
            status=data["status"],
            audit_record_id=data["audit_record_id"],
        )


# ── Wallets ───────────────────────────────────────────────────────────────


class Wallets(_Resource):
    """client.wallets.*"""

    def verify(
        self,
        *,
        wallet: str,
        entity_type: str,
        entity_id: str,
        proof_message: str,
        proof_signature: str,
    ) -> WalletVerifyResponse:
        """Verify wallet ownership via signed message."""
        body = {
            "wallet": wallet,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "proof": {
                "type": "signed_message",
                "message": proof_message,
                "signature": proof_signature,
            },
        }
        data = self._post("/v1/wallets/verify", json=body)
        return WalletVerifyResponse(
            wallet_id=data["wallet_id"],
            verification_status=data["verification_status"],
            verified_at=data.get("verified_at"),
            expires_at=data.get("expires_at"),
            error=data.get("error"),
        )


# ── Travel Rule ───────────────────────────────────────────────────────────


class TravelRule(_Resource):
    """client.travel_rule.*"""

    def check(
        self,
        *,
        amount: str,
        originator_jurisdiction: Optional[str] = None,
        beneficiary_jurisdiction: Optional[str] = None,
        originator_entity_type: str = "user",
        beneficiary_entity_type: str = "user",
        involves_self_hosted: bool = False,
    ) -> TravelRuleCheckResponse:
        """Pre-flight check of Travel Rule requirements."""
        params: Dict[str, Any] = {"amount": amount}
        if originator_jurisdiction is not None:
            params["originator_jurisdiction"] = originator_jurisdiction
        if beneficiary_jurisdiction is not None:
            params["beneficiary_jurisdiction"] = beneficiary_jurisdiction
        params["originator_entity_type"] = originator_entity_type
        params["beneficiary_entity_type"] = beneficiary_entity_type
        if involves_self_hosted:
            params["involves_self_hosted"] = "true"

        data = self._get("/v1/travel-rule/check", params=params)
        return TravelRuleCheckResponse(
            status=data["status"],
            threshold_exceeded=data["threshold_exceeded"],
            applicable_threshold=data["applicable_threshold"],
            threshold_currency=data["threshold_currency"],
            jurisdiction=data["jurisdiction"],
            required_actions=data["required_actions"],
            self_hosted_verification_needed=data["self_hosted_verification_needed"],
            notes=data.get("notes"),
            required_data_fields=data.get("required_data_fields"),
        )

    def transmit(
        self,
        *,
        transaction_id: str,
        originator: Dict[str, Any],
        beneficiary: Dict[str, Any],
        beneficiary_vasp: Dict[str, Any],
    ) -> TravelRuleTransmitResponse:
        """Transmit Travel Rule data to counterparty VASP."""
        body = {
            "transaction_id": transaction_id,
            "originator": originator,
            "beneficiary": beneficiary,
            "beneficiary_vasp": beneficiary_vasp,
        }
        data = self._post("/v1/travel-rule/transmit", json=body)
        return TravelRuleTransmitResponse(
            transaction_id=data["transaction_id"],
            travel_rule_status=data["travel_rule_status"],
            proof_id=data.get("proof_id"),
        )

    def jurisdictions(self) -> Dict[str, Any]:
        """List all supported jurisdictions with their Travel Rule requirements."""
        return self._get("/v1/travel-rule/jurisdictions")


# ── Reports ───────────────────────────────────────────────────────────────


class Reports(_Resource):
    """client.reports.*"""

    def export_json(
        self,
        *,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> ReportExportResponse:
        """Export audit records as typed JSON."""
        params: Dict[str, Any] = {"format": "json"}
        if from_date is not None:
            params["from_date"] = from_date
        if to_date is not None:
            params["to_date"] = to_date

        data = self._get("/v1/reports/export", params=params)
        return ReportExportResponse(
            records=data["records"],
            count=data["count"],
        )

    def export_csv(
        self,
        *,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> bytes:
        """Export audit records as raw CSV bytes."""
        params: Dict[str, Any] = {"format": "csv"}
        if from_date is not None:
            params["from_date"] = from_date
        if to_date is not None:
            params["to_date"] = to_date

        resp = self._client._raw_request("GET", "/v1/reports/export", params=params)
        raise_for_status(resp)
        return resp.content


# ── Client ────────────────────────────────────────────────────────────────


class RadiusClient:
    """Radius API client.

    Usage::

        from getradius import RadiusClient, Entity

        client = RadiusClient(api_key="sk_live_...")
        result = client.transactions.ingest(
            direction="outbound",
            from_entity=Entity(type="business", entity_id="acme"),
            to_entity=Entity(type="user", entity_id="bob", wallet="0x..."),
            amount="100.00", asset="USDC", chain="ethereum",
        )
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": f"getradius-python/{__version__}",
            }
        )
        self._timeout = timeout

        # Resource namespaces
        self.transactions = Transactions(self)
        self.payments = Payments(self)
        self.wallets = Wallets(self)
        self.travel_rule = TravelRule(self)
        self.reports = Reports(self)

    # ── Internal HTTP helpers ─────────────────────────────────────────────

    def _raw_request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Send a request and return the raw response (no status check)."""
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self._timeout)
        return self._session.request(method, url, **kwargs)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        """Send a request, raise on error, return parsed JSON."""
        resp = self._raw_request(method, path, **kwargs)
        raise_for_status(resp)
        return resp.json()

    # ── Top-level convenience ─────────────────────────────────────────────

    def health(self) -> HealthResponse:
        """Check API health status (no auth required)."""
        data = self._request("GET", "/v1/health")
        return HealthResponse(
            status=data["status"],
            version=data["version"],
            environment=data["environment"],
            db_connected=data["db_connected"],
            sanctions_screening=data["sanctions_screening"],
        )
