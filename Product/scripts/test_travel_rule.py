#!/usr/bin/env python3
"""
Test script for Travel Rule threshold logic.

Demonstrates various scenarios:
1. US transaction below threshold ($2,000) - not required
2. US transaction above threshold ($5,000) - required
3. EU transaction (any amount) - required (zero threshold)
4. Cross-border US->EU - uses stricter EU rules
5. Self-hosted wallet with EU jurisdiction - verification required
6. Singapore transaction at threshold boundary
"""

import requests
import json
from decimal import Decimal

BASE_URL = "http://localhost:8000"
API_KEY = "sk_test_demo_000000"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
}


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)


def test_travel_rule_check():
    """Test the /v1/travel-rule/check endpoint."""
    print_section("Travel Rule Pre-flight Check Endpoint")

    scenarios = [
        {
            "name": "US domestic $2,000 (below threshold)",
            "params": {
                "amount": "2000",
                "originator_jurisdiction": "US",
                "beneficiary_jurisdiction": "US",
            },
            "expected_status": "not_required",
        },
        {
            "name": "US domestic $5,000 (above threshold)",
            "params": {
                "amount": "5000",
                "originator_jurisdiction": "US",
                "beneficiary_jurisdiction": "US",
            },
            "expected_status": "required",
        },
        {
            "name": "EU domestic $100 (zero threshold)",
            "params": {
                "amount": "100",
                "originator_jurisdiction": "DE",
                "beneficiary_jurisdiction": "FR",
            },
            "expected_status": "required",
        },
        {
            "name": "US->EU $1,000 (uses stricter EU rules)",
            "params": {
                "amount": "1000",
                "originator_jurisdiction": "US",
                "beneficiary_jurisdiction": "DE",
            },
            "expected_status": "required",
        },
        {
            "name": "EU with self-hosted wallet >€1,000",
            "params": {
                "amount": "1500",
                "originator_jurisdiction": "DE",
                "beneficiary_jurisdiction": "DE",
                "involves_self_hosted": "true",
            },
            "expected_status": "verification_required",
        },
        {
            "name": "Singapore $1,000 (below SGD 1,500 threshold)",
            "params": {
                "amount": "1000",
                "originator_jurisdiction": "SG",
                "beneficiary_jurisdiction": "SG",
            },
            "expected_status": "not_required",
        },
        {
            "name": "Singapore $1,200 (above threshold)",
            "params": {
                "amount": "1200",
                "originator_jurisdiction": "SG",
                "beneficiary_jurisdiction": "SG",
            },
            "expected_status": "required",
        },
        {
            "name": "Japan $50 (zero threshold)",
            "params": {
                "amount": "50",
                "originator_jurisdiction": "JP",
                "beneficiary_jurisdiction": "JP",
            },
            "expected_status": "required",
        },
        {
            "name": "UK $1,500 (above £1,000 threshold)",
            "params": {
                "amount": "1500",
                "originator_jurisdiction": "UK",
                "beneficiary_jurisdiction": "UK",
            },
            "expected_status": "required",
        },
        {
            "name": "Unknown jurisdiction (FATF default $1,000)",
            "params": {
                "amount": "500",
                "originator_jurisdiction": "XX",
                "beneficiary_jurisdiction": "XX",
            },
            "expected_status": "not_required",
        },
    ]

    for scenario in scenarios:
        resp = requests.get(
            f"{BASE_URL}/v1/travel-rule/check",
            headers=HEADERS,
            params=scenario["params"],
        )

        if resp.status_code == 200:
            result = resp.json()
            status_match = "✓" if result["status"] == scenario["expected_status"] else "✗"
            print(f"\n{status_match} {scenario['name']}")
            print(f"  Status: {result['status']}")
            print(f"  Threshold: {result['applicable_threshold']} {result['threshold_currency']}")
            print(f"  Jurisdiction: {result['jurisdiction']}")
            if result['required_actions']:
                print(f"  Required actions: {', '.join(result['required_actions'])}")
            if result['self_hosted_verification_needed']:
                print(f"  Self-hosted verification: REQUIRED")
        else:
            print(f"✗ {scenario['name']}: {resp.status_code} - {resp.text}")


def test_transaction_ingest_with_travel_rule():
    """Test transaction ingest with Travel Rule info in response."""
    print_section("Transaction Ingest with Travel Rule")

    # US transaction above threshold
    payload = {
        "direction": "outbound",
        "business_id": "biz_acme",
        "from_entity": {
            "type": "business",
            "entity_id": "acme_corp",
            "wallet": "0x1234567890abcdef1234567890abcdef12345678",
            "jurisdiction": "US",
        },
        "to_entity": {
            "type": "user",
            "entity_id": "user_alice",
            "wallet": "0xabcdef1234567890abcdef1234567890abcdef12",
            "jurisdiction": "US",
        },
        "amount": "5000.00",
        "asset": "USDC",
        "chain": "ethereum",
        "purpose": "contractor_payment",
        "external_id": "test_travel_rule_001",
    }

    resp = requests.post(
        f"{BASE_URL}/v1/transactions/ingest",
        headers=HEADERS,
        json=payload,
    )

    print(f"\nUS Transaction $5,000:")
    if resp.status_code == 200:
        result = resp.json()
        print(f"  Transaction ID: {result['transaction_id']}")
        print(f"  Status: {result['status']}")
        print(f"  Risk Level: {result['risk_level']}")
        if 'travel_rule' in result:
            print(f"  Travel Rule Status: {result['travel_rule']['status']}")
            print(f"  Travel Rule Threshold: {result['travel_rule']['applicable_threshold']} {result['travel_rule']['threshold_currency']}")
            print(f"  Travel Rule Jurisdiction: {result['travel_rule']['jurisdiction']}")
        print(f"  Required Actions: {', '.join(result['required_actions'])}")
    else:
        print(f"  Error: {resp.status_code} - {resp.text}")

    # EU transaction (zero threshold)
    payload_eu = {
        "direction": "outbound",
        "business_id": "biz_acme",
        "from_entity": {
            "type": "business",
            "entity_id": "acme_eu",
            "wallet": "0x1234567890abcdef1234567890abcdef12345678",
            "jurisdiction": "DE",
        },
        "to_entity": {
            "type": "user",
            "entity_id": "user_hans",
            "wallet": "0xabcdef1234567890abcdef1234567890abcdef12",
            "jurisdiction": "FR",
        },
        "amount": "100.00",
        "asset": "USDC",
        "chain": "polygon",
        "purpose": "payment",
        "external_id": "test_travel_rule_eu_001",
    }

    resp = requests.post(
        f"{BASE_URL}/v1/transactions/ingest",
        headers=HEADERS,
        json=payload_eu,
    )

    print(f"\nEU Transaction €100 (DE->FR):")
    if resp.status_code == 200:
        result = resp.json()
        print(f"  Transaction ID: {result['transaction_id']}")
        if 'travel_rule' in result:
            print(f"  Travel Rule Status: {result['travel_rule']['status']}")
            print(f"  Travel Rule Notes: {result['travel_rule']['notes']}")
        print(f"  Required Actions: {', '.join(result['required_actions'])}")
    else:
        print(f"  Error: {resp.status_code} - {resp.text}")


def test_jurisdictions_endpoint():
    """Test the jurisdictions listing endpoint."""
    print_section("Jurisdictions Endpoint")

    resp = requests.get(
        f"{BASE_URL}/v1/travel-rule/jurisdictions",
        headers=HEADERS,
    )

    if resp.status_code == 200:
        result = resp.json()
        print(f"\nSupported jurisdictions: {result['total']}")
        print(f"\nSample jurisdictions:")
        for j in result['jurisdictions'][:5]:
            print(f"  {j['code']}: {j['threshold_amount']} {j['threshold_currency']}")
            if j['requires_self_hosted_verification']:
                print(f"       Self-hosted verification required")
    else:
        print(f"Error: {resp.status_code} - {resp.text}")


def main():
    print("\n" + "="*60)
    print(" RADIUS - Travel Rule Threshold Testing")
    print("="*60)

    # Check server is running
    try:
        resp = requests.get(f"{BASE_URL}/v1/health")
        if resp.status_code != 200:
            print("Error: Server not responding correctly")
            return
        print(f"Server: {resp.json()['status']}")
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to server. Run: uvicorn app.main:app --reload")
        return

    test_travel_rule_check()
    test_transaction_ingest_with_travel_rule()
    test_jurisdictions_endpoint()

    print("\n" + "="*60)
    print(" Testing Complete")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
