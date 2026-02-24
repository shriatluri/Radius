"""
Integration tests for POST /v1/wallets/verify.

Uses eth_account (already a project dependency) to generate real Ethereum
signatures for the happy-path test. Rejection paths (expired message, bad
signature) exercise the service logic directly through the endpoint without
needing valid crypto material.

Test wallet (Hardhat #0 — well-known public test key, never used in production):
  Private key : 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
  Address     : 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
"""

from datetime import datetime, timedelta

from eth_account import Account
from eth_account.messages import encode_defunct

VERIFY_URL = "/v1/wallets/verify"

# Well-known Hardhat test key — public, safe to use in tests
TEST_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
TEST_WALLET = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"


def _sign(message: str, private_key: str = TEST_PRIVATE_KEY) -> str:
    """Sign a message with the given private key, returning a hex signature."""
    account = Account.from_key(private_key)
    msg = encode_defunct(text=message)
    signed = account.sign_message(msg)
    return signed.signature.hex()


def _today() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def _days_ago(n: int) -> str:
    return (datetime.utcnow() - timedelta(days=n)).strftime("%Y-%m-%d")


def _valid_payload(entity_id: str = "test_entity") -> dict:
    """Build a valid wallet verify payload signed with TEST_WALLET."""
    message = f"radius-verify:{entity_id}:{_today()}"
    return {
        "wallet": TEST_WALLET,
        "entity_type": "user",
        "entity_id": entity_id,
        "proof": {
            "type": "signed_message",
            "message": message,
            "signature": _sign(message),
        },
    }


# ---------------------------------------------------------------------------
# Happy path — valid signature
# ---------------------------------------------------------------------------


class TestVerifyWalletValid:

    def test_valid_signature_returns_200(self, client, auth_headers):
        resp = client.post(VERIFY_URL, json=_valid_payload(), headers=auth_headers)
        assert resp.status_code == 200

    def test_valid_signature_status_is_verified(self, client, auth_headers):
        resp = client.post(VERIFY_URL, json=_valid_payload(), headers=auth_headers)
        data = resp.json()
        assert data["verification_status"] == "verified"

    def test_valid_signature_returns_wallet_id(self, client, auth_headers):
        resp = client.post(VERIFY_URL, json=_valid_payload(), headers=auth_headers)
        data = resp.json()
        assert data.get("wallet_id")

    def test_valid_signature_returns_expiry(self, client, auth_headers):
        resp = client.post(VERIFY_URL, json=_valid_payload(), headers=auth_headers)
        data = resp.json()
        assert data.get("verified_at")
        assert data.get("expires_at")


# ---------------------------------------------------------------------------
# Rejection paths
# ---------------------------------------------------------------------------


class TestVerifyWalletRejected:

    def test_expired_message_returns_rejected(self, client, auth_headers):
        """Message signed 8 days ago is beyond the 7-day expiry window."""
        old_date = _days_ago(8)
        message = f"radius-verify:test_entity:{old_date}"
        payload = {
            "wallet": TEST_WALLET,
            "entity_type": "user",
            "entity_id": "test_entity",
            "proof": {
                "type": "signed_message",
                "message": message,
                "signature": _sign(message),
            },
        }
        resp = client.post(VERIFY_URL, json=payload, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["verification_status"] == "rejected"
        assert "expired" in data["error"].lower()

    def test_wrong_wallet_signature_returns_rejected(self, client, auth_headers):
        """Signature from TEST_WALLET presented as a different wallet → rejected."""
        message = f"radius-verify:test_entity:{_today()}"
        wrong_wallet = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"  # Hardhat #1
        payload = {
            "wallet": wrong_wallet,  # different from who actually signed
            "entity_type": "user",
            "entity_id": "test_entity",
            "proof": {
                "type": "signed_message",
                "message": message,
                "signature": _sign(message),  # signed by TEST_WALLET key
            },
        }
        resp = client.post(VERIFY_URL, json=payload, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["verification_status"] == "rejected"

    def test_garbage_signature_returns_rejected(self, client, auth_headers):
        """A completely invalid signature string → rejected, not 500."""
        message = f"radius-verify:test_entity:{_today()}"
        payload = {
            "wallet": TEST_WALLET,
            "entity_type": "user",
            "entity_id": "test_entity",
            "proof": {
                "type": "signed_message",
                "message": message,
                "signature": "0xnotavalidsignatureatall",
            },
        }
        resp = client.post(VERIFY_URL, json=payload, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["verification_status"] == "rejected"


# ---------------------------------------------------------------------------
# Auth + validation
# ---------------------------------------------------------------------------


class TestVerifyWalletAuth:

    def test_requires_auth(self, client):
        resp = client.post(VERIFY_URL, json=_valid_payload())
        assert resp.status_code == 401

    def test_missing_wallet_returns_422(self, client, auth_headers):
        payload = _valid_payload()
        del payload["wallet"]
        resp = client.post(VERIFY_URL, json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_missing_proof_returns_422(self, client, auth_headers):
        payload = _valid_payload()
        del payload["proof"]
        resp = client.post(VERIFY_URL, json=payload, headers=auth_headers)
        assert resp.status_code == 422
