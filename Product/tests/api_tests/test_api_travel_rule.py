"""
Integration tests for Travel Rule endpoints:
  POST /v1/travel-rule/transmit — send Travel Rule data to counterparty VASP
  GET  /v1/travel-rule/check   — pre-flight jurisdiction + threshold check
"""

TRANSMIT_URL = "/v1/travel-rule/transmit"
CHECK_URL    = "/v1/travel-rule/check"


# ---------------------------------------------------------------------------
# POST /v1/travel-rule/transmit
# ---------------------------------------------------------------------------


class TestTravelRuleTransmit:
    """Transmit Travel Rule data to a counterparty VASP."""

    PAYLOAD = {
        "transaction_id": "txn_test_travel_rule_001",
        "originator": {
            "name": "Acme Corp",
            "wallet": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        },
        "beneficiary": {
            "name": "Contractor LLC",
            "wallet": "0x742d35Cc6634C0532925a3b8D4C9C79D3b3B4123",
        },
        "beneficiary_vasp": {
            "name": "Example VASP",
            "lei": "EXAMPLEVASP1234567890",
        },
    }

    def test_transmit_returns_200(self, client, auth_headers):
        resp = client.post(TRANSMIT_URL, json=self.PAYLOAD, headers=auth_headers)
        assert resp.status_code == 200

    def test_transmit_status_is_sent(self, client, auth_headers):
        resp = client.post(TRANSMIT_URL, json=self.PAYLOAD, headers=auth_headers)
        data = resp.json()
        assert data["travel_rule_status"] == "sent"

    def test_transmit_echoes_transaction_id(self, client, auth_headers):
        resp = client.post(TRANSMIT_URL, json=self.PAYLOAD, headers=auth_headers)
        assert resp.json()["transaction_id"] == self.PAYLOAD["transaction_id"]

    def test_transmit_returns_proof_id(self, client, auth_headers):
        resp = client.post(TRANSMIT_URL, json=self.PAYLOAD, headers=auth_headers)
        assert resp.json().get("proof_id")

    def test_transmit_missing_originator_returns_422(self, client, auth_headers):
        payload = {k: v for k, v in self.PAYLOAD.items() if k != "originator"}
        resp = client.post(TRANSMIT_URL, json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_transmit_requires_auth(self, client):
        resp = client.post(TRANSMIT_URL, json=self.PAYLOAD)
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /v1/travel-rule/check
# ---------------------------------------------------------------------------


class TestTravelRuleCheck:
    """Pre-flight check returns jurisdiction thresholds without persisting anything."""

    def test_us_below_threshold_not_required(self, client, auth_headers):
        resp = client.get(
            CHECK_URL,
            params={
                "amount": "500",
                "originator_jurisdiction": "US",
                "beneficiary_jurisdiction": "US",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "not_required"
        assert data["threshold_exceeded"] is False

    def test_us_at_threshold_required(self, client, auth_headers):
        resp = client.get(
            CHECK_URL,
            params={
                "amount": "3000",
                "originator_jurisdiction": "US",
                "beneficiary_jurisdiction": "US",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "required"
        assert data["threshold_exceeded"] is True

    def test_eu_zero_threshold_always_required(self, client, auth_headers):
        """EU's zero threshold means even $0.01 triggers Travel Rule."""
        resp = client.get(
            CHECK_URL,
            params={
                "amount": "0.01",
                "originator_jurisdiction": "EU",
                "beneficiary_jurisdiction": "EU",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "required"

    def test_cross_border_us_to_eu_uses_stricter_eu_threshold(self, client, auth_headers):
        """US→EU: EU ($0) is stricter than US ($3000), so $500 triggers Travel Rule."""
        resp = client.get(
            CHECK_URL,
            params={
                "amount": "500",
                "originator_jurisdiction": "US",
                "beneficiary_jurisdiction": "EU",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "required"
        assert data["jurisdiction"] == "EU"

    def test_check_requires_amount(self, client, auth_headers):
        """Missing required 'amount' query param → 422."""
        resp = client.get(
            CHECK_URL,
            params={"originator_jurisdiction": "US"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_check_requires_auth(self, client):
        resp = client.get(CHECK_URL, params={"amount": "500"})
        assert resp.status_code == 401
