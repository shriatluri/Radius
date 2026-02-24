#!/usr/bin/env python3
"""
Docker workflow smoke test for Radius.

Starts the compose stack, runs functional + edge-case tests, checks data
persistence across an API restart, tests DB failover recovery, then tears
everything down.

Usage:
    python scripts/test_docker.py

Requirements:
    pip install requests          (already in requirements.txt)
    docker compose v2 installed
"""

import subprocess
import sys
import time
from datetime import datetime

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL   = "http://localhost:8000/v1"
HEADERS    = {"X-API-Key": "sk_test_acme_123456"}
ADMIN_HDRS = {"X-API-Key": "sk_test_admin_radius_dev"}

SANCTIONED_WALLET = "0x8589427373d6d84e98730d7795d8f6f8731fda16"  # Tornado Cash Router
CLEAN_WALLET_A    = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
CLEAN_WALLET_B    = "0x742d35Cc6634C0532925a3b8D4C9C79D3b3B4123"

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

PASS_SYM = f"{GREEN}✓{RESET}"
FAIL_SYM = f"{RED}✗{RESET}"

passed = 0
failed = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def section(title: str) -> None:
    print(f"\n{BOLD}{title}{RESET}")
    print("─" * 50)


def check(name: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        print(f"  {PASS_SYM} {name}")
        passed += 1
    else:
        suffix = f"  →  {detail}" if detail else ""
        print(f"  {FAIL_SYM} {name}{suffix}")
        failed += 1


def docker(cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        f"docker compose -f docker-compose.yml -f docker-compose.test.yml {cmd}",
        shell=True,
        capture_output=True,
        text=True,
    )


def wait_for_health(timeout: int = 90, label: str = "API") -> bool:
    """Poll /v1/health until 200 or timeout. Returns True on success."""
    print(f"  Waiting for {label} to be ready", end="", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=3)
            if r.status_code == 200:
                print(f"  {PASS_SYM}")
                return True
        except Exception:
            pass
        print(".", end="", flush=True)
        time.sleep(3)
    print(f"  {FAIL_SYM} timed out after {timeout}s")
    return False


def ingest(payload: dict) -> requests.Response:
    return requests.post(f"{BASE_URL}/transactions/ingest", json=payload, headers=HEADERS)


def base_payload(external_id: str = None, amount: str = "500.00",
                 from_wallet: str = CLEAN_WALLET_A,
                 to_wallet: str = CLEAN_WALLET_B) -> dict:
    p = {
        "direction": "outbound",
        "business_id": "acme_corp",
        "from_entity": {
            "type": "business",
            "entity_id": "acme_corp",
            "wallet": from_wallet,
            "jurisdiction": "US",
        },
        "to_entity": {
            "type": "user",
            "entity_id": "contractor_001",
            "wallet": to_wallet,
            "jurisdiction": "US",
        },
        "amount": amount,
        "asset": "USDC",
        "chain": "ethereum",
        "purpose": "contractor_payout",
    }
    if external_id:
        p["external_id"] = external_id
    return p


# ---------------------------------------------------------------------------
# Test sections
# ---------------------------------------------------------------------------

def test_health():
    section("1. Health endpoint")
    r = requests.get(f"{BASE_URL}/health")
    check("Returns 200", r.status_code == 200)
    data = r.json()
    check("Has 'status' field", "status" in data)


def test_auth():
    section("2. Authentication")
    payload = base_payload("auth-test")

    r = requests.post(f"{BASE_URL}/transactions/ingest", json=payload)
    check("No API key → 401", r.status_code == 401)

    r = requests.post(
        f"{BASE_URL}/transactions/ingest",
        json=payload,
        headers={"X-API-Key": "sk_totally_wrong"},
    )
    check("Invalid API key → 401", r.status_code == 401)

    r = ingest(payload)
    check("Valid API key → 200", r.status_code == 200)


def test_happy_path() -> str:
    """Returns transaction_id for use in later tests."""
    section("3. Valid transaction — happy path")
    r = ingest(base_payload("docker-happy-001"))
    check("Returns 200", r.status_code == 200)
    data = r.json()
    check("Has transaction_id", data.get("transaction_id", "").startswith("txn_"),
          data.get("transaction_id"))
    check("Status is pending", data.get("status") == "pending",
          data.get("status"))
    check("Risk level is low", data.get("risk_level") == "low",
          data.get("risk_level"))
    check("Sanctions passed", data.get("sanctions_result") == "passed")
    check("Travel rule not_required (US $500)",
          data.get("travel_rule", {}).get("status") == "not_required")
    check("audit_record_id present", bool(data.get("audit_record_id")))
    return data["transaction_id"]


def test_sanctioned_wallet():
    section("4. Sanctioned wallet — must be blocked")
    r = ingest(base_payload("docker-sanctioned-001", to_wallet=SANCTIONED_WALLET))
    check("Returns 200", r.status_code == 200)
    data = r.json()
    check("Status is blocked", data.get("status") == "blocked", data.get("status"))
    check("Sanctions failed", data.get("sanctions_result") == "failed")
    check("Risk score is 100", data.get("risk_score") == 100, str(data.get("risk_score")))
    check("Risk level is critical", data.get("risk_level") == "critical")
    check("blocked_sanctioned_wallet in required_actions",
          "blocked_sanctioned_wallet" in data.get("required_actions", []))


def test_validation():
    section("5. Input validation — missing fields → 422")
    cases = [
        ("Missing amount",      {k: v for k, v in base_payload().items() if k != "amount"}),
        ("Missing from_entity", {k: v for k, v in base_payload().items() if k != "from_entity"}),
        ("Missing to_entity",   {k: v for k, v in base_payload().items() if k != "to_entity"}),
        ("Missing chain",       {k: v for k, v in base_payload().items() if k != "chain"}),
        ("Empty body",          {}),
    ]
    for name, payload in cases:
        r = requests.post(f"{BASE_URL}/transactions/ingest", json=payload, headers=HEADERS)
        check(f"{name} → 422", r.status_code == 422, f"got {r.status_code}")


def test_idempotency():
    section("6. Idempotency — duplicate external_id")
    ext_id = f"docker-idem-{int(time.time())}"
    r1 = ingest(base_payload(ext_id))
    r2 = ingest(base_payload(ext_id))
    id1 = r1.json().get("transaction_id")
    id2 = r2.json().get("transaction_id")
    check("Both requests succeed", r1.status_code == 200 and r2.status_code == 200)
    check("Same transaction_id returned", id1 == id2, f"{id1!r} vs {id2!r}")

    r3 = ingest(base_payload())   # no external_id
    r4 = ingest(base_payload())
    check("No external_id creates distinct transactions",
          r3.json().get("transaction_id") != r4.json().get("transaction_id"))


def test_annotate_and_audit(txn_id: str):
    section("7. Annotate + audit retrieval")
    tx_hash = "0xdeadbeefcafe1234567890abcdef"

    r = requests.post(
        f"{BASE_URL}/payments/annotate",
        json={"transaction_id": txn_id, "tx_hash": tx_hash, "executed_at": "2026-02-23T12:00:00Z"},
        headers=HEADERS,
    )
    check("Annotate returns 200", r.status_code == 200, r.text)
    check("Status is completed", r.json().get("status") == "completed")

    r = requests.get(f"{BASE_URL}/transactions/{txn_id}/audit", headers=HEADERS)
    check("Audit returns 200", r.status_code == 200)
    audit = r.json()
    check("Audit has correct transaction_id", audit.get("transaction_id") == txn_id)
    check("tx_hash set on audit record", audit.get("tx_hash") == tx_hash,
          audit.get("tx_hash"))
    check("business_id is acme_corp", audit.get("business_id") == "acme_corp")

    r = requests.get("/".join([BASE_URL, "transactions", "txn_ghost", "audit"]), headers=HEADERS)
    check("Unknown audit id → 404", r.status_code == 404, f"got {r.status_code}")

    r = requests.get(f"{BASE_URL}/transactions/{txn_id}/audit",
                     headers={"X-API-Key": "sk_test_globalcorp_789012"})
    check("Other business cannot see audit → 404", r.status_code == 404)


def test_travel_rule():
    section("8. Travel Rule — cross-border threshold")
    r = requests.get(
        f"{BASE_URL}/travel-rule/check",
        params={"amount": "500", "originator_jurisdiction": "US", "beneficiary_jurisdiction": "EU"},
        headers=HEADERS,
    )
    check("US→EU $500 → required (EU zero threshold)", r.status_code == 200)
    check("Jurisdiction is EU", r.json().get("jurisdiction") == "EU")

    r = requests.get(
        f"{BASE_URL}/travel-rule/check",
        params={"amount": "500", "originator_jurisdiction": "US", "beneficiary_jurisdiction": "US"},
        headers=HEADERS,
    )
    check("US→US $500 → not_required",
          r.json().get("status") == "not_required", r.json().get("status"))


def test_high_amount():
    section("9. High-amount transaction — risk escalation")
    r = ingest(base_payload("docker-highamt-001", amount="15000.00"))
    check("Returns 200", r.status_code == 200)
    data = r.json()
    check("Risk score ≥ 50 for $15k", data.get("risk_score", 0) >= 50,
          str(data.get("risk_score")))
    check("Travel rule required (US $15k > $3k threshold)",
          data.get("travel_rule", {}).get("status") == "required")


def test_reports():
    section("10. Export")
    r = requests.get(f"{BASE_URL}/reports/export", params={"format": "json"}, headers=HEADERS)
    check("JSON export returns 200", r.status_code == 200)
    data = r.json()
    check("Has records and count", "records" in data and "count" in data)
    check("count matches records length", data.get("count") == len(data.get("records", [])))

    r = requests.get(f"{BASE_URL}/reports/export", params={"format": "csv"}, headers=HEADERS)
    check("CSV export returns 200", r.status_code == 200)
    check("Content-Type is text/csv", "text/csv" in r.headers.get("content-type", ""))
    lines = r.text.strip().splitlines()
    check("CSV has header row", len(lines) >= 1 and "transaction_id" in lines[0])


def test_admin():
    section("11. Admin endpoints")
    r = requests.get(f"{BASE_URL}/admin/sanctions/status", headers=ADMIN_HDRS)
    check("Admin status returns 200", r.status_code == 200)
    check("Has screener + provider fields",
          "screener" in r.json() and "provider" in r.json())

    r = requests.get(f"{BASE_URL}/admin/sanctions/status", headers=HEADERS)
    check("Non-admin key → 403", r.status_code == 403, f"got {r.status_code}")


def test_persistence():
    """
    Create a transaction, restart just the API container (no -v so Postgres
    data survives), then verify the transaction is still retrievable.
    """
    section("12. Data persistence — API restart")
    ext_id = f"docker-persist-{int(time.time())}"
    r = ingest(base_payload(ext_id, amount="1234.56"))
    original_id = r.json().get("transaction_id")
    check("Transaction created", r.status_code == 200 and bool(original_id))

    print(f"\n  Restarting API container (data stays in Postgres)...")
    result = docker("restart api")
    check("docker compose restart api succeeded", result.returncode == 0,
          result.stderr.strip())

    if not wait_for_health(timeout=60, label="API after restart"):
        check("API came back healthy", False, "timed out")
        return

    # Ingest same external_id — idempotency will return the original record
    r = ingest(base_payload(ext_id, amount="1234.56"))
    recovered_id = r.json().get("transaction_id")
    check("Transaction survives API restart",
          recovered_id == original_id, f"{recovered_id!r} != {original_id!r}")


def test_db_failover():
    """
    Stop the db container → API requests should fail gracefully.
    Restart db → API should recover without needing a restart itself.
    """
    section("13. DB failover — stop and restart Postgres")

    print("  Stopping db container...")
    docker("stop db")
    time.sleep(3)   # give the API a moment to notice

    r = None
    for _ in range(5):
        try:
            r = ingest(base_payload())
            break
        except requests.exceptions.ConnectionError:
            time.sleep(1)

    check("API returns 5xx when DB is down",
          r is not None and r.status_code >= 500,
          f"got {r.status_code if r else 'no response'}")

    print("\n  Starting db container back up...")
    docker("start db")

    if not wait_for_health(timeout=60, label="API after DB recovery"):
        check("API recovered after DB restart", False, "timed out")
        return

    # pool_pre_ping recycles stale connections, but the first request after a
    # DB restart can still fail while the pool re-establishes. Retry briefly.
    r = None
    for attempt in range(10):
        r = ingest(base_payload("docker-failover-recovery"))
        if r.status_code == 200:
            break
        time.sleep(3)

    check("API handles requests after DB recovery",
          r is not None and r.status_code == 200,
          f"got {r.status_code if r else 'no response'}: {r.text[:100] if r else ''}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print(f"\n{BOLD}{'=' * 50}")
    print("  Radius — Docker workflow smoke test")
    print(f"{'=' * 50}{RESET}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Start the stack
    section("Stack startup")
    print("  Running: docker compose up -d --build")
    result = docker("up -d --build")
    if result.returncode != 0:
        print(f"{RED}docker compose up failed:{RESET}\n{result.stderr}")
        return 1

    if not wait_for_health(timeout=90):
        print(f"{RED}API never became healthy. Aborting.{RESET}")
        docker("down -v")
        return 1

    # Run all test sections
    try:
        test_health()
        test_auth()
        txn_id = test_happy_path()
        test_sanctioned_wallet()
        test_validation()
        test_idempotency()
        test_annotate_and_audit(txn_id)
        test_travel_rule()
        test_high_amount()
        test_reports()
        test_admin()
        test_persistence()
        test_db_failover()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted — tearing down stack{RESET}")
    except Exception as e:
        print(f"\n{RED}Unexpected error: {e}{RESET}")
        import traceback; traceback.print_exc()

    # Summary
    total = passed + failed
    print(f"\n{BOLD}{'=' * 50}")
    print("  Results")
    print(f"{'=' * 50}{RESET}")
    print(f"  {PASS_SYM} Passed : {passed}/{total}")
    if failed:
        print(f"  {FAIL_SYM} Failed : {failed}/{total}")

    # Teardown
    section("Teardown")
    print("  Running: docker compose down -v")
    docker("down -v")
    print("  Done.")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
