"""
Integration tests for payments + audit endpoints:
  POST /v1/payments/annotate   — link on-chain tx_hash to a transaction
  GET  /v1/transactions/{id}/audit — retrieve full audit record

Each test class has an _ingest() helper that creates a transaction first
so the subsequent annotate/audit calls have a real transaction_id to work with.
"""

INGEST_URL  = "/v1/transactions/ingest"
ANNOTATE_URL = "/v1/payments/annotate"
TX_HASH = "0xdeadbeefcafe1234567890abcdef"
EXECUTED_AT = "2026-02-23T10:00:00Z"


def _ingest(client, auth_headers, sample_transaction):
    """Ingest a transaction and return the full response dict."""
    resp = client.post(INGEST_URL, json=sample_transaction, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# POST /v1/payments/annotate
# ---------------------------------------------------------------------------


class TestAnnotatePayment:
    """Attaching a tx_hash to an existing transaction."""

    def test_annotate_returns_200(self, client, auth_headers, sample_transaction):
        txn_id = _ingest(client, auth_headers, sample_transaction)["transaction_id"]
        payload = {"transaction_id": txn_id, "tx_hash": TX_HASH, "executed_at": EXECUTED_AT}
        resp = client.post(ANNOTATE_URL, json=payload, headers=auth_headers)
        assert resp.status_code == 200

    def test_annotate_response_status_is_completed(self, client, auth_headers, sample_transaction):
        txn_id = _ingest(client, auth_headers, sample_transaction)["transaction_id"]
        payload = {"transaction_id": txn_id, "tx_hash": TX_HASH, "executed_at": EXECUTED_AT}
        resp = client.post(ANNOTATE_URL, json=payload, headers=auth_headers)
        data = resp.json()
        assert data["status"] == "completed"
        assert data["transaction_id"] == txn_id

    def test_annotate_returns_audit_record_id(self, client, auth_headers, sample_transaction):
        ingest_data = _ingest(client, auth_headers, sample_transaction)
        txn_id = ingest_data["transaction_id"]
        payload = {"transaction_id": txn_id, "tx_hash": TX_HASH, "executed_at": EXECUTED_AT}
        resp = client.post(ANNOTATE_URL, json=payload, headers=auth_headers)
        data = resp.json()
        assert data.get("audit_record_id")  # present and non-empty

    def test_annotate_unknown_transaction_returns_404(self, client, auth_headers):
        payload = {
            "transaction_id": "txn_does_not_exist",
            "tx_hash": TX_HASH,
            "executed_at": EXECUTED_AT,
        }
        resp = client.post(ANNOTATE_URL, json=payload, headers=auth_headers)
        assert resp.status_code == 404

    def test_annotate_missing_tx_hash_returns_422(self, client, auth_headers, sample_transaction):
        txn_id = _ingest(client, auth_headers, sample_transaction)["transaction_id"]
        payload = {"transaction_id": txn_id, "executed_at": EXECUTED_AT}
        resp = client.post(ANNOTATE_URL, json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_annotate_missing_executed_at_returns_422(self, client, auth_headers, sample_transaction):
        txn_id = _ingest(client, auth_headers, sample_transaction)["transaction_id"]
        payload = {"transaction_id": txn_id, "tx_hash": TX_HASH}
        resp = client.post(ANNOTATE_URL, json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_annotate_requires_auth(self, client, auth_headers, sample_transaction):
        txn_id = _ingest(client, auth_headers, sample_transaction)["transaction_id"]
        payload = {"transaction_id": txn_id, "tx_hash": TX_HASH, "executed_at": EXECUTED_AT}
        resp = client.post(ANNOTATE_URL, json=payload)  # no headers
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /v1/transactions/{id}/audit
# ---------------------------------------------------------------------------


class TestGetAuditRecord:
    """Retrieving the full audit record for a transaction."""

    def test_audit_returns_200(self, client, auth_headers, sample_transaction):
        txn_id = _ingest(client, auth_headers, sample_transaction)["transaction_id"]
        resp = client.get(f"/v1/transactions/{txn_id}/audit", headers=auth_headers)
        assert resp.status_code == 200

    def test_audit_contains_correct_transaction_id(self, client, auth_headers, sample_transaction):
        txn_id = _ingest(client, auth_headers, sample_transaction)["transaction_id"]
        resp = client.get(f"/v1/transactions/{txn_id}/audit", headers=auth_headers)
        assert resp.json()["transaction_id"] == txn_id

    def test_audit_contains_correct_business_id(self, client, auth_headers, sample_transaction):
        """business_id should be the key owner's id (acme_corp), not the payload value."""
        txn_id = _ingest(client, auth_headers, sample_transaction)["transaction_id"]
        resp = client.get(f"/v1/transactions/{txn_id}/audit", headers=auth_headers)
        assert resp.json()["business_id"] == "acme_corp"

    def test_audit_contains_risk_and_sanctions_fields(self, client, auth_headers, sample_transaction):
        txn_id = _ingest(client, auth_headers, sample_transaction)["transaction_id"]
        resp = client.get(f"/v1/transactions/{txn_id}/audit", headers=auth_headers)
        audit = resp.json()
        assert audit["risk_level"] == "low"
        assert audit["risk_score"] == 10
        assert audit["sanctions_result"] == "passed"

    def test_audit_amount_and_asset(self, client, auth_headers, sample_transaction):
        from decimal import Decimal
        txn_id = _ingest(client, auth_headers, sample_transaction)["transaction_id"]
        resp = client.get(f"/v1/transactions/{txn_id}/audit", headers=auth_headers)
        audit = resp.json()
        # The DB may serialize Decimal with full precision (e.g. "500.000000000000000000")
        assert Decimal(audit["amount"]) == Decimal("500.00")
        assert audit["asset"] == "USDC"

    def test_audit_tx_hash_is_none_before_annotation(self, client, auth_headers, sample_transaction):
        txn_id = _ingest(client, auth_headers, sample_transaction)["transaction_id"]
        resp = client.get(f"/v1/transactions/{txn_id}/audit", headers=auth_headers)
        assert resp.json()["tx_hash"] is None

    def test_audit_tx_hash_set_after_annotation(self, client, auth_headers, sample_transaction):
        """After annotate, the audit record's tx_hash must reflect the attached hash."""
        txn_id = _ingest(client, auth_headers, sample_transaction)["transaction_id"]

        client.post(
            ANNOTATE_URL,
            json={"transaction_id": txn_id, "tx_hash": TX_HASH, "executed_at": EXECUTED_AT},
            headers=auth_headers,
        )

        resp = client.get(f"/v1/transactions/{txn_id}/audit", headers=auth_headers)
        assert resp.json()["tx_hash"] == TX_HASH

    def test_audit_unknown_id_returns_404(self, client, auth_headers):
        resp = client.get("/v1/transactions/txn_nonexistent/audit", headers=auth_headers)
        assert resp.status_code == 404

    def test_audit_requires_auth(self, client, auth_headers, sample_transaction):
        txn_id = _ingest(client, auth_headers, sample_transaction)["transaction_id"]
        resp = client.get(f"/v1/transactions/{txn_id}/audit")  # no headers
        assert resp.status_code == 401

    def test_audit_scoped_to_authenticated_business(
        self, client, auth_headers, sample_transaction
    ):
        """
        A transaction ingested by acme_corp must not be visible to globalcorp.
        The audit endpoint returns 404 when the business_id doesn't match.
        """
        txn_id = _ingest(client, auth_headers, sample_transaction)["transaction_id"]

        other_headers = {"X-API-Key": "sk_test_globalcorp_789012"}
        resp = client.get(f"/v1/transactions/{txn_id}/audit", headers=other_headers)
        assert resp.status_code == 404
