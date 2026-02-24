"""
Targeted integration tests for endpoints not covered by other test files:
  GET  /v1/transactions             — list with filtering and pagination
  POST /v1/transactions/{id}/annotate — transactions-router annotate (path param)
  GET  /v1/admin/sanctions/status   — admin: screener state
  POST /v1/admin/sanctions/refresh  — admin: trigger background refresh
  GET  /v1/health                   — health check

These tests exist primarily to push coverage above 80% for the endpoints
that are exercised in USE_DATABASE=true mode but weren't reached by the
main integration test files.
"""

from unittest.mock import patch, AsyncMock

INGEST_URL = "/v1/transactions/ingest"

# ---------------------------------------------------------------------------
# GET /v1/transactions — list endpoint
# ---------------------------------------------------------------------------


class TestListTransactions:

    def _ingest(self, client, auth_headers, sample_transaction, external_id=None):
        payload = dict(sample_transaction)
        if external_id:
            payload["external_id"] = external_id
        resp = client.post(INGEST_URL, json=payload, headers=auth_headers)
        assert resp.status_code == 200
        return resp.json()

    def test_empty_list_returns_200(self, client, auth_headers):
        resp = client.get("/v1/transactions", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["transactions"] == []
        assert data["total"] == 0

    def test_list_returns_ingested_transaction(self, client, auth_headers, sample_transaction):
        self._ingest(client, auth_headers, sample_transaction)
        resp = client.get("/v1/transactions", headers=auth_headers)
        data = resp.json()
        assert data["total"] == 1
        assert len(data["transactions"]) == 1
        txn = data["transactions"][0]
        assert txn["risk_level"] == "low"
        assert txn["asset"] == "USDC"

    def test_list_multiple_transactions(self, client, auth_headers, sample_transaction):
        self._ingest(client, auth_headers, sample_transaction, external_id="list-001")
        payload2 = dict(sample_transaction)
        payload2["external_id"] = "list-002"
        client.post(INGEST_URL, json=payload2, headers=auth_headers)
        resp = client.get("/v1/transactions", headers=auth_headers)
        assert resp.json()["total"] == 2

    def test_list_scoped_to_authenticated_business(
        self, client, auth_headers, sample_transaction
    ):
        """acme_corp transactions must not be visible to globalcorp."""
        self._ingest(client, auth_headers, sample_transaction)
        other = {"X-API-Key": "sk_test_globalcorp_789012"}
        resp = client.get("/v1/transactions", headers=other)
        assert resp.json()["total"] == 0

    def test_list_requires_auth(self, client):
        resp = client.get("/v1/transactions")
        assert resp.status_code == 401

    def test_list_status_filter(self, client, auth_headers, sample_transaction):
        self._ingest(client, auth_headers, sample_transaction)
        pending = client.get(
            "/v1/transactions", params={"status": "pending"}, headers=auth_headers
        )
        blocked = client.get(
            "/v1/transactions", params={"status": "blocked"}, headers=auth_headers
        )
        # Sample transaction is low risk → pending
        assert pending.json()["total"] == 1
        assert blocked.json()["total"] == 0

    def test_list_risk_level_filter(self, client, auth_headers, sample_transaction):
        self._ingest(client, auth_headers, sample_transaction)
        low = client.get(
            "/v1/transactions", params={"risk_level": "low"}, headers=auth_headers
        )
        high = client.get(
            "/v1/transactions", params={"risk_level": "high"}, headers=auth_headers
        )
        assert low.json()["total"] == 1
        assert high.json()["total"] == 0

    def test_list_pagination(self, client, auth_headers, sample_transaction):
        for i in range(3):
            p = dict(sample_transaction)
            p["external_id"] = f"page-{i}"
            client.post(INGEST_URL, json=p, headers=auth_headers)
        page1 = client.get(
            "/v1/transactions", params={"limit": 2, "offset": 0}, headers=auth_headers
        )
        page2 = client.get(
            "/v1/transactions", params={"limit": 2, "offset": 2}, headers=auth_headers
        )
        assert len(page1.json()["transactions"]) == 2
        assert len(page2.json()["transactions"]) == 1
        assert page1.json()["total"] == 3


# ---------------------------------------------------------------------------
# POST /v1/transactions/{id}/annotate — transactions-router annotate
# ---------------------------------------------------------------------------


class TestTransactionAnnotate:
    """The transactions router also exposes an annotate endpoint at
    POST /v1/transactions/{id}/annotate (separate from POST /v1/payments/annotate).
    """

    def test_annotate_via_transactions_router(self, client, auth_headers, sample_transaction):
        ingest = client.post(INGEST_URL, json=sample_transaction, headers=auth_headers)
        txn_id = ingest.json()["transaction_id"]

        payload = {"transaction_id": txn_id, "tx_hash": "0xabcdef1234", "executed_at": "2026-02-23T10:00:00Z"}
        resp = client.post(
            f"/v1/transactions/{txn_id}/annotate", json=payload, headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    def test_annotate_unknown_id_returns_404(self, client, auth_headers):
        payload = {
            "transaction_id": "txn_ghost",
            "tx_hash": "0xdeadbeef",
            "executed_at": "2026-02-23T10:00:00Z",
        }
        resp = client.post(
            "/v1/transactions/txn_ghost/annotate", json=payload, headers=auth_headers
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


class TestAdminSanctionsStatus:

    def test_status_returns_200(self, client, admin_headers):
        resp = client.get("/v1/admin/sanctions/status", headers=admin_headers)
        assert resp.status_code == 200

    def test_status_contains_screener_key(self, client, admin_headers):
        data = client.get("/v1/admin/sanctions/status", headers=admin_headers).json()
        assert "screener" in data
        assert "provider" in data

    def test_status_requires_admin_scope(self, client, auth_headers):
        """Regular key (no admin:all scope) must get 403."""
        resp = client.get("/v1/admin/sanctions/status", headers=auth_headers)
        assert resp.status_code == 403

    def test_status_requires_auth(self, client):
        resp = client.get("/v1/admin/sanctions/status")
        assert resp.status_code == 401


class TestAdminSanctionsRefresh:

    def test_refresh_returns_202(self, client, admin_headers):
        with patch(
            "app.api.admin.asyncio.create_task",
            return_value=None,
        ):
            resp = client.post("/v1/admin/sanctions/refresh", headers=admin_headers)
        assert resp.status_code == 202

    def test_refresh_requires_admin_scope(self, client, auth_headers):
        resp = client.post("/v1/admin/sanctions/refresh", headers=auth_headers)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /v1/health
# ---------------------------------------------------------------------------


class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        resp = client.get("/v1/health")
        assert resp.status_code == 200

    def test_health_contains_status(self, client):
        data = client.get("/v1/health").json()
        assert "status" in data
