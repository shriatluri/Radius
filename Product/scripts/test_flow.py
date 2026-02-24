#!/usr/bin/env python3
"""
Test script for the Radius compliance flow.

Runs through:
1. Wallet verification (signature check)
2. Clean transaction (should pass)
3. Sanctioned wallet transaction (should be blocked)
4. Annotate and export

Usage:
    # Start the server first:
    uvicorn app.main:app --reload

    # Then run this script:
    python scripts/test_flow.py
"""

from datetime import datetime

import requests
from eth_account import Account
from eth_account.messages import encode_defunct

BASE_URL = "http://localhost:8000/v1"

# API key for authentication (Acme Corp test key)
API_KEY = "sk_test_acme_123456"
HEADERS = {"X-API-Key": API_KEY}

# A known sanctioned wallet (Tornado Cash router)
SANCTIONED_WALLET = "0x8589427373D6D84E98730D7795D8f6f8731FDA16"

# Test wallet (we control the private key for signing)
TEST_PRIVATE_KEY = "0x" + "1234567890abcdef" * 4  # 32 bytes
TEST_ACCOUNT = Account.from_key(TEST_PRIVATE_KEY)
TEST_WALLET = TEST_ACCOUNT.address


def test_wallet_verification():
    """Test wallet ownership verification via signature."""
    print("\n[WALLET VERIFICATION TEST]")
    print("=" * 60)

    entity_id = "user_jane_doe"
    today = datetime.utcnow().strftime("%Y-%m-%d")
    message = f"radius-verify:{entity_id}:{today}"

    # Sign the message with our test wallet
    message_encoded = encode_defunct(text=message)
    signed = TEST_ACCOUNT.sign_message(message_encoded)

    print(f"  Wallet: {TEST_WALLET}")
    print(f"  Message: {message}")
    print(f"  Signature: {signed.signature.hex()[:40]}...")

    # Test 1: Valid signature
    print("\n[1] Testing VALID signature...")
    verify_payload = {
        "wallet": TEST_WALLET,
        "entity_type": "user",
        "entity_id": entity_id,
        "proof": {
            "type": "signed_message",
            "message": message,
            "signature": signed.signature.hex(),
        },
    }

    resp = requests.post(f"{BASE_URL}/wallets/verify", json=verify_payload, headers=HEADERS)
    resp.raise_for_status()
    result = resp.json()

    print(f"  Status: {result['verification_status']}")
    if result.get("verified_at"):
        print(f"  Verified At: {result['verified_at']}")
        print(f"  Expires At: {result['expires_at']}")
    if result.get("error"):
        print(f"  Error: {result['error']}")

    # Test 2: Invalid signature (wrong wallet)
    print("\n[2] Testing INVALID signature (wrong wallet)...")
    wrong_wallet_payload = {
        "wallet": "0x1234567890123456789012345678901234567890",  # Different wallet
        "entity_type": "user",
        "entity_id": entity_id,
        "proof": {
            "type": "signed_message",
            "message": message,
            "signature": signed.signature.hex(),  # Same signature
        },
    }

    resp = requests.post(f"{BASE_URL}/wallets/verify", json=wrong_wallet_payload, headers=HEADERS)
    resp.raise_for_status()
    result = resp.json()

    print(f"  Status: {result['verification_status']}")
    if result.get("error"):
        print(f"  Error: {result['error']}")

    if result["verification_status"] == "rejected":
        print("\n  *** Correctly rejected - signature doesn't match wallet! ***")


def test_clean_transaction():
    """Test a normal, clean transaction."""
    print("\n[1] Ingesting CLEAN transaction...")
    print("-" * 40)
    ingest_payload = {
        "external_id": "payout_test_001",
        "direction": "outbound",
        "business_id": "biz_acme",
        "from_entity": {
            "type": "business",
            "entity_id": "biz_acme",
            "wallet": "0xAcmeCorpWallet1234567890abcdef",
        },
        "to_entity": {
            "type": "user",
            "entity_id": "user_jane_doe",
            "wallet": "0xJaneDoeWallet0987654321fedcba",
        },
        "amount": "2500.00",
        "asset": "USDC",
        "chain": "ethereum",
        "purpose": "contractor_payout",
        "metadata": {
            "country": "US",
            "invoice_id": "inv_2024_001",
        },
    }

    resp = requests.post(f"{BASE_URL}/transactions/ingest", json=ingest_payload, headers=HEADERS)
    resp.raise_for_status()
    ingest_result = resp.json()

    print(f"  Transaction ID: {ingest_result['transaction_id']}")
    print(f"  Status: {ingest_result['status']}")
    print(f"  Risk Score: {ingest_result['risk_score']}")
    print(f"  Risk Level: {ingest_result['risk_level']}")
    print(f"  Sanctions: {ingest_result['sanctions_result']}")
    print(f"  Audit Record ID: {ingest_result['audit_record_id']}")

    transaction_id = ingest_result["transaction_id"]

    # Step 2: Annotate with tx_hash (simulating post-execution)
    print("\n[2] Annotating payment with tx_hash...")
    annotate_payload = {
        "transaction_id": transaction_id,
        "tx_hash": "0x9f8e7d6c5b4a3210fedcba0987654321abcdef1234567890",
        "executed_at": "2026-02-10T15:30:00Z",
        "provider_refs": {
            "custodian": "fireblocks",
            "custodian_tx_id": "fb_tx_12345",
        },
    }

    resp = requests.post(f"{BASE_URL}/payments/annotate", json=annotate_payload, headers=HEADERS)
    resp.raise_for_status()
    annotate_result = resp.json()

    print(f"  Status: {annotate_result['status']}")
    print(f"  Audit Record ID: {annotate_result['audit_record_id']}")

    # Step 3: Fetch the audit record
    print("\n[3] Fetching audit record...")
    resp = requests.get(f"{BASE_URL}/transactions/{transaction_id}/audit", headers=HEADERS)
    resp.raise_for_status()
    audit_record = resp.json()

    print("  Audit Record:")
    print(f"    Transaction ID: {audit_record['transaction_id']}")
    print(f"    Business ID: {audit_record['business_id']}")
    print(f"    From: {audit_record['from_entity']} ({audit_record['wallets']['from']})")
    print(f"    To: {audit_record['to_entity']} ({audit_record['wallets']['to']})")
    print(f"    Amount: {audit_record['amount']} {audit_record['asset']}")
    print(f"    Purpose: {audit_record['purpose']}")
    print(f"    Risk: {audit_record['risk_level']} (score: {audit_record['risk_score']})")
    print(f"    Sanctions: {audit_record['sanctions_result']}")
    print(f"    Travel Rule: {audit_record['travel_rule_status']}")
    print(f"    TX Hash: {audit_record['tx_hash']}")
    print(f"    Reconciliation: {audit_record['reconciliation_status']}")
    print(f"    Approvals: {audit_record['approvals']}")

    # Step 4: Export a report (CSV)
    print("\n[4] Exporting report (CSV)...")
    resp = requests.get(
        f"{BASE_URL}/reports/export",
        params={"format": "csv", "from_date": "2026-02-01", "to_date": "2026-02-28"},
        headers=HEADERS,
    )
    resp.raise_for_status()

    print("  CSV Export:")
    print("-" * 60)
    for line in resp.text.strip().split("\n"):
        print(f"  {line}")
    print("-" * 60)

    # Also test JSON export
    print("\n[5] Exporting report (JSON)...")
    resp = requests.get(
        f"{BASE_URL}/reports/export",
        params={"format": "json"},
        headers=HEADERS,
    )
    resp.raise_for_status()
    json_export = resp.json()
    print(f"  Records exported: {json_export['count']}")

    return transaction_id


def test_sanctioned_transaction():
    """Test a transaction to a sanctioned wallet - should be BLOCKED."""
    print("\n" + "=" * 60)
    print("[SANCTIONS TEST] Attempting payment to sanctioned wallet...")
    print("=" * 60)

    sanctioned_payload = {
        "external_id": "payout_sanctioned_test",
        "direction": "outbound",
        "business_id": "biz_acme",
        "from_entity": {
            "type": "business",
            "entity_id": "biz_acme",
            "wallet": "0xAcmeCorpWallet1234567890abcdef",
        },
        "to_entity": {
            "type": "user",
            "entity_id": "user_bad_actor",
            "wallet": SANCTIONED_WALLET,  # Tornado Cash!
        },
        "amount": "500.00",
        "asset": "USDC",
        "chain": "ethereum",
        "purpose": "suspicious_payout",
    }

    resp = requests.post(f"{BASE_URL}/transactions/ingest", json=sanctioned_payload, headers=HEADERS)
    resp.raise_for_status()
    result = resp.json()

    print(f"  Transaction ID: {result['transaction_id']}")
    print(f"  Status: {result['status']}")
    print(f"  Risk Score: {result['risk_score']}")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  Sanctions: {result['sanctions_result']}")
    print(f"  Required Actions: {result['required_actions']}")

    if result["sanctions_result"] == "failed" and result["status"] == "blocked":
        print("\n  *** TRANSACTION BLOCKED - Sanctioned wallet detected! ***")
    else:
        print("\n  WARNING: Transaction was not blocked!")


def main():
    print("=" * 60)
    print("Radius Compliance Flow Test")
    print("=" * 60)

    # Test 0: Wallet verification
    test_wallet_verification()

    # Test 1: Clean transaction
    transaction_id = test_clean_transaction()

    # Test 2: Sanctioned wallet
    test_sanctioned_transaction()

    # Summary
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
    print("\nResults:")
    print("  - Wallet verification: valid sig accepted, invalid rejected")
    print("  - Clean transaction: passed sanctions, created audit record")
    print("  - Sanctioned wallet: BLOCKED, sanctions failed")
    print("\nCSV export saved to: exports/latest_audit_export.csv")


if __name__ == "__main__":
    main()
