"""
Seed script to populate the database with mock transactions for testing.

Run this script to add sample data to the Radius database.
"""

import sys
import random
import json
from datetime import datetime, timedelta

# Add backend to path so we can import app modules
sys.path.insert(0, '/Users/shriatluri/sc-compliance/sc-compliance/backend')

from app.db.database import SessionLocal
from app.db.models import Transaction, AuditRecord

# Sample data
BUSINESS_IDS = [
    "acme_corp",
    "globalcorp",
    "techstartup_inc",
    "fintech_solutions",
    "marketplace_platform",
]

ENTITIES = {
    "companies": ["Acme Corporation", "Global Corp Ltd", "TechStartup Inc", "Fintech Solutions", "Marketplace Platform"],
    "people": ["Alice Smith", "Bob Johnson", "Carol Martinez", "David Chen", "Emma Wilson", "Frank Brown", "Grace Lee", "Henry Taylor"]
}

ENTITY_IDS = {
    "companies": ["biz_acme", "biz_global", "biz_techstart", "biz_fintech", "biz_marketplace"],
    "people": ["user_alice", "user_bob", "user_carol", "user_david", "user_emma", "user_frank", "user_grace", "user_henry"]
}

WALLET_ADDRESSES = [
    "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
    "0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199",
    "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    "0x514910771AF9Ca656af840dff83E8264EcF986CA",
    "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
    "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
    "0xC18360217D8F7Ab5e7c516566761Ea12Ce7F9D72",
]

ASSETS = ["USDC", "USDT", "DAI", "PYUSD"]
CHAINS = ["ethereum", "polygon", "base", "arbitrum"]

PURPOSES = [
    "Payroll payment",
    "Vendor payment",
    "Contractor payout",
    "Customer refund",
    "Marketplace settlement",
    "Subscription payment",
    "Invoice payment",
    "Bonus payment",
    "Commission payment",
    "Service payment",
]

STATUSES = ["pending", "approved", "blocked"]
RISK_LEVELS = ["low", "medium", "high", "critical"]
SANCTIONS_RESULTS = ["clear", "flagged", "blocked"]
TRAVEL_RULE_STATUSES = ["compliant", "pending", "exempt", "not_required"]


def generate_transaction_id():
    """Generate a unique transaction ID."""
    import uuid
    return f"txn_{str(uuid.uuid4())[:12]}"


def generate_audit_id():
    """Generate a unique audit record ID."""
    import uuid
    return f"aud_{str(uuid.uuid4())[:12]}"


def generate_external_id():
    """Generate an external payment ID."""
    return f"pay_{random.randint(100000, 999999)}"


def generate_mock_transaction_pair(days_ago=0):
    """Generate a Transaction and AuditRecord pair."""
    # Randomize timestamp
    created_at = datetime.now() - timedelta(
        days=days_ago,
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )

    # Pick random data
    business_id = random.choice(BUSINESS_IDS)

    # From is typically a company, To is typically a person (for payouts)
    from_entity_type = "business"
    from_entity_idx = random.randint(0, len(ENTITIES["companies"]) - 1)
    from_entity_name = ENTITIES["companies"][from_entity_idx]
    from_entity_id = ENTITY_IDS["companies"][from_entity_idx]

    to_entity_type = "individual"
    to_entity_idx = random.randint(0, len(ENTITIES["people"]) - 1)
    to_entity_name = ENTITIES["people"][to_entity_idx]
    to_entity_id = ENTITY_IDS["people"][to_entity_idx]

    from_wallet = random.choice(WALLET_ADDRESSES)
    to_wallet = random.choice(WALLET_ADDRESSES)
    while to_wallet == from_wallet:
        to_wallet = random.choice(WALLET_ADDRESSES)

    amount = round(random.uniform(100, 50000), 2)
    asset = random.choice(ASSETS)
    chain = random.choice(CHAINS)
    purpose = random.choice(PURPOSES)

    # Risk correlation: higher amounts = higher risk chance
    if amount > 20000:
        risk_level = random.choices(RISK_LEVELS, weights=[20, 30, 30, 20])[0]
    elif amount > 10000:
        risk_level = random.choices(RISK_LEVELS, weights=[30, 40, 20, 10])[0]
    else:
        risk_level = random.choices(RISK_LEVELS, weights=[60, 30, 8, 2])[0]

    # Risk score based on level
    risk_score_ranges = {
        "low": (0, 30),
        "medium": (31, 60),
        "high": (61, 85),
        "critical": (86, 100),
    }
    risk_score = random.randint(*risk_score_ranges[risk_level])

    # Status based on risk
    if risk_level == "critical":
        status = random.choices(STATUSES, weights=[10, 20, 70])[0]
    elif risk_level == "high":
        status = random.choices(STATUSES, weights=[20, 50, 30])[0]
    elif risk_level == "medium":
        status = random.choices(STATUSES, weights=[30, 60, 10])[0]
    else:
        status = random.choices(STATUSES, weights=[10, 88, 2])[0]

    # Sanctions result based on status
    if status == "blocked":
        sanctions_result = random.choice(["flagged", "blocked"])
    elif risk_level in ["high", "critical"]:
        sanctions_result = random.choices(SANCTIONS_RESULTS, weights=[50, 40, 10])[0]
    else:
        sanctions_result = random.choices(SANCTIONS_RESULTS, weights=[95, 4, 1])[0]

    # Travel rule status
    if amount > 1000:
        travel_rule_status = random.choices(TRAVEL_RULE_STATUSES, weights=[70, 15, 10, 5])[0]
    else:
        travel_rule_status = "not_required"

    # Generate transaction hash for approved transactions
    tx_hash = None
    executed_at = None
    if status == "approved":
        tx_hash = f"0x{''.join(random.choices('0123456789abcdef', k=64))}"
        executed_at = created_at + timedelta(minutes=random.randint(1, 30))

    # Generate IDs
    transaction_id = generate_transaction_id()
    external_id = generate_external_id()

    # Create Transaction
    transaction = Transaction(
        id=transaction_id,
        external_id=external_id,
        business_id=business_id,
        direction="outbound",
        from_entity_type=from_entity_type,
        from_entity_id=from_entity_id,
        from_wallet=from_wallet,
        from_jurisdiction="US",
        to_entity_type=to_entity_type,
        to_entity_id=to_entity_id,
        to_wallet=to_wallet,
        to_jurisdiction="US",
        amount=str(amount),
        asset=asset,
        chain=chain,
        purpose=purpose,
        status=status,
        risk_score=risk_score,
        risk_level=risk_level,
        sanctions_result=sanctions_result,
        travel_rule_status=travel_rule_status,
        tx_hash=tx_hash,
        executed_at=executed_at,
        created_at=created_at,
        updated_at=created_at,
    )

    # Create AuditRecord
    approvals = []
    if status == "approved":
        approvals = [{"type": "policy", "result": "approved", "rule_id": f"rule_{risk_level}_risk"}]
    elif status == "blocked":
        approvals = [{"type": "policy", "result": "blocked", "rule_id": "rule_high_risk_block", "reason": sanctions_result}]

    audit_record = AuditRecord(
        id=generate_audit_id(),
        transaction_id=transaction_id,
        business_id=business_id,
        from_entity=from_entity_name,
        to_entity=to_entity_name,
        from_wallet=from_wallet,
        to_wallet=to_wallet,
        amount=str(amount),
        asset=asset,
        purpose=purpose,
        risk_score=risk_score,
        risk_level=risk_level,
        sanctions_result=sanctions_result,
        travel_rule_status=travel_rule_status,
        tx_hash=tx_hash,
        reconciliation_status="matched" if status == "approved" else "unmatched",
        approvals=json.dumps(approvals) if approvals else None,
        timestamp=created_at,
    )

    return transaction, audit_record


def seed_database(num_transactions=50, force=False):
    """Seed the database with mock transactions."""
    db = SessionLocal()

    try:
        # Check if data already exists
        existing_count = db.query(Transaction).count()
        if existing_count > 0 and not force:
            print(f"⚠️  Database already contains {existing_count} transactions.")
            try:
                response = input("Do you want to add more transactions? (y/n): ")
                if response.lower() != 'y':
                    print("❌ Seeding cancelled.")
                    return
            except EOFError:
                # Non-interactive mode, just add more
                print("   Adding more transactions...")

        print(f"🌱 Seeding database with {num_transactions} mock transactions...")

        # Generate transactions spread over the last 30 days
        transactions = []
        audit_records = []
        for i in range(num_transactions):
            days_ago = random.randint(0, 30)
            transaction, audit_record = generate_mock_transaction_pair(days_ago)
            transactions.append(transaction)
            audit_records.append(audit_record)

        # Add to database
        db.add_all(transactions)
        db.add_all(audit_records)
        db.commit()

        # Print summary
        print(f"✅ Successfully added {num_transactions} transactions!")
        print("\n📊 Summary by status:")
        for status in STATUSES:
            count = sum(1 for t in transactions if t.status == status)
            print(f"   {status.capitalize()}: {count}")

        print("\n📊 Summary by risk level:")
        for risk_level in RISK_LEVELS:
            count = sum(1 for t in transactions if t.risk_level == risk_level)
            print(f"   {risk_level.capitalize()}: {count}")

        print("\n🎯 You can now access the dashboard at http://localhost:8000")
        print("   Demo API key: sk_test_acme_123456")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed the database with mock transactions")
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of transactions to generate (default: 50)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before seeding"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force add transactions without prompting"
    )

    args = parser.parse_args()

    if args.clear:
        db = SessionLocal()
        try:
            audit_count = db.query(AuditRecord).count()
            txn_count = db.query(Transaction).count()
            total_count = audit_count + txn_count

            if total_count > 0:
                try:
                    response = input(f"⚠️  This will delete {txn_count} transactions and {audit_count} audit records. Are you sure? (y/n): ")
                    if response.lower() != 'y':
                        print("❌ Clear cancelled.")
                        sys.exit(0)
                except EOFError:
                    print("   Clearing data (non-interactive mode)...")

                # Delete audit records first (they have FK to transactions)
                db.query(AuditRecord).delete()
                db.query(Transaction).delete()
                db.commit()
                print(f"✅ Deleted {txn_count} transactions and {audit_count} audit records.")
        finally:
            db.close()

    seed_database(args.count, force=args.force)
