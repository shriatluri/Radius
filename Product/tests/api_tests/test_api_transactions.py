"""
Integration tests for POST /v1/transactions/ingest.

Uses a real FastAPI TestClient backed by an in-memory SQLite database.
The OFAC screener is pre-seeded with an empty index (via the autouse
seed_ofac_screener fixture in conftest.py), so:
  - clean wallets pass through without any download
  - wallets in KNOWN_SANCTIONED_WALLETS are caught by the hardcoded fallback

All tests use the fixtures defined in conftest.py:
  client          — TestClient with a fresh DB per test
  auth_headers    — X-API-Key: sk_test_acme_123456 (transactions:write+read)
  sample_transaction — $500 USDC, ethereum, US→US, clean wallets → low/pending
"""

# Tornado Cash Router — in KNOWN_SANCTIONED_WALLETS (CYBER2), caught by fallback
SANCTIONED_WALLET = "0x8589427373d6d84e98730d7795d8f6f8731fda16"

URL = "/v1/transactions/ingest"


# ---------------------------------------------------------------------------
# Valid payload — happy path
# ---------------------------------------------------------------------------


class TestIngestValidPayload:
    """Happy-path: well-formed payload returns a 200 compliance result."""

    def test_returns_200(self, client, auth_headers, sample_transaction):
        resp = client.post(URL, json=sample_transaction, headers=auth_headers)
        assert resp.status_code == 200

    def test_response_has_transaction_id(self, client, auth_headers, sample_transaction):
        resp = client.post(URL, json=sample_transaction, headers=auth_headers)
        data = resp.json()
        assert "transaction_id" in data
        assert data["transaction_id"].startswith("txn_")

    def test_low_risk_clean_tx_is_pending(self, client, auth_headers, sample_transaction):
        """$500 clean US→US tx: low risk, sanctions passed, status pending."""
        resp = client.post(URL, json=sample_transaction, headers=auth_headers)
        data = resp.json()
        assert data["status"] == "pending"
        assert data["risk_level"] == "low"
        assert data["sanctions_result"] == "passed"

    def test_travel_rule_not_required_for_small_us_tx(self, client, auth_headers, sample_transaction):
        """$500 US→US is well below the $3,000 BSA threshold."""
        resp = client.post(URL, json=sample_transaction, headers=auth_headers)
        data = resp.json()
        assert data["travel_rule"]["status"] == "not_required"
        assert data["travel_rule"]["threshold_exceeded"] is False

    def test_audit_record_id_is_returned(self, client, auth_headers, sample_transaction):
        resp = client.post(URL, json=sample_transaction, headers=auth_headers)
        data = resp.json()
        assert data.get("audit_record_id")  # present and non-empty

    def test_business_id_is_set_from_api_key(self, client, auth_headers, sample_transaction):
        """
        business_id in the payload is ignored — it is always overridden by the
        authenticated key's business_id (acme_corp for sk_test_acme_123456).
        Verify by supplying a different business_id and checking the transaction
        is still retrievable with the auth key.
        """
        payload = dict(sample_transaction)
        payload["business_id"] = "some_other_corp"
        resp = client.post(URL, json=payload, headers=auth_headers)
        assert resp.status_code == 200
        # If the business_id were not overridden the audit lookup would fail
        data = resp.json()
        txn_id = data["transaction_id"]
        audit_resp = client.get(f"/v1/transactions/{txn_id}/audit", headers=auth_headers)
        assert audit_resp.status_code == 200


# ---------------------------------------------------------------------------
# Sanctioned wallets — must be blocked
# ---------------------------------------------------------------------------


class TestIngestSanctionedWallet:
    """Transactions involving a sanctioned wallet must have status=blocked."""

    def _sanctioned_from_payload(self, sample_transaction):
        payload = {**sample_transaction, "external_id": "test-sanctioned-from"}
        payload["from_entity"] = {**sample_transaction["from_entity"], "wallet": SANCTIONED_WALLET}
        return payload

    def _sanctioned_to_payload(self, sample_transaction):
        payload = {**sample_transaction, "external_id": "test-sanctioned-to"}
        payload["to_entity"] = {**sample_transaction["to_entity"], "wallet": SANCTIONED_WALLET}
        return payload

    def test_sanctioned_from_wallet_is_blocked(self, client, auth_headers, sample_transaction):
        resp = client.post(URL, json=self._sanctioned_from_payload(sample_transaction), headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "blocked"
        assert data["sanctions_result"] == "failed"

    def test_sanctioned_to_wallet_is_blocked(self, client, auth_headers, sample_transaction):
        resp = client.post(URL, json=self._sanctioned_to_payload(sample_transaction), headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "blocked"
        assert data["sanctions_result"] == "failed"

    def test_sanctioned_tx_risk_score_is_100_critical(self, client, auth_headers, sample_transaction):
        resp = client.post(URL, json=self._sanctioned_from_payload(sample_transaction), headers=auth_headers)
        data = resp.json()
        assert data["risk_score"] == 100
        assert data["risk_level"] == "critical"

    def test_sanctioned_tx_required_actions_contains_blocked(self, client, auth_headers, sample_transaction):
        resp = client.post(URL, json=self._sanctioned_from_payload(sample_transaction), headers=auth_headers)
        data = resp.json()
        assert "blocked_sanctioned_wallet" in data["required_actions"]


# ---------------------------------------------------------------------------
# Missing required fields — must return 422
# ---------------------------------------------------------------------------


class TestIngestMissingFields:
    """FastAPI/Pydantic validation errors return 422 Unprocessable Entity."""

    def test_missing_amount(self, client, auth_headers, sample_transaction):
        payload = dict(sample_transaction)
        del payload["amount"]
        resp = client.post(URL, json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_missing_chain(self, client, auth_headers, sample_transaction):
        payload = dict(sample_transaction)
        del payload["chain"]
        resp = client.post(URL, json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_missing_from_entity(self, client, auth_headers, sample_transaction):
        payload = dict(sample_transaction)
        del payload["from_entity"]
        resp = client.post(URL, json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_missing_to_entity(self, client, auth_headers, sample_transaction):
        payload = dict(sample_transaction)
        del payload["to_entity"]
        resp = client.post(URL, json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_empty_body_returns_422(self, client, auth_headers):
        resp = client.post(URL, json={}, headers=auth_headers)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Idempotency — same external_id must return the same transaction
# ---------------------------------------------------------------------------


class TestIngestIdempotency:
    """Submitting the same external_id twice returns the same record."""

    def test_duplicate_returns_same_transaction_id(self, client, auth_headers, sample_transaction):
        resp1 = client.post(URL, json=sample_transaction, headers=auth_headers)
        resp2 = client.post(URL, json=sample_transaction, headers=auth_headers)
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.json()["transaction_id"] == resp2.json()["transaction_id"]

    def test_duplicate_returns_same_status_and_risk(self, client, auth_headers, sample_transaction):
        resp1 = client.post(URL, json=sample_transaction, headers=auth_headers)
        resp2 = client.post(URL, json=sample_transaction, headers=auth_headers)
        d1, d2 = resp1.json(), resp2.json()
        assert d1["status"] == d2["status"]
        assert d1["risk_score"] == d2["risk_score"]

    def test_no_external_id_creates_distinct_transactions(self, client, auth_headers, sample_transaction):
        """Without an external_id, every call creates a fresh transaction."""
        payload = {k: v for k, v in sample_transaction.items() if k != "external_id"}
        resp1 = client.post(URL, json=payload, headers=auth_headers)
        resp2 = client.post(URL, json=payload, headers=auth_headers)
        assert resp1.json()["transaction_id"] != resp2.json()["transaction_id"]


# ---------------------------------------------------------------------------
# Authentication — missing / invalid API key must return 401
# ---------------------------------------------------------------------------


class TestIngestAuth:
    """Auth failures must return 401 before any processing occurs."""

    def test_no_api_key_returns_401(self, client, sample_transaction):
        resp = client.post(URL, json=sample_transaction)
        assert resp.status_code == 401

    def test_invalid_api_key_returns_401(self, client, sample_transaction):
        resp = client.post(
            URL,
            json=sample_transaction,
            headers={"X-API-Key": "sk_invalid_totally_wrong"},
        )
        assert resp.status_code == 401

    def test_valid_key_returns_200(self, client, auth_headers, sample_transaction):
        """Sanity check: the standard test key is accepted."""
        resp = client.post(URL, json=sample_transaction, headers=auth_headers)
        assert resp.status_code == 200
