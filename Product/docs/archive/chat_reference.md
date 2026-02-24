# Radius MVP - Chat Reference

## What's Been Built

### Core Features (All Working)

1. **API Authentication** (`app/auth.py`)
   - X-API-Key header required on all endpoints (except /v1/health)
   - Mock keys: `sk_test_acme_123456`, `sk_test_globex_789012`, `sk_test_demo_000000`
   - Keys map to business_id with scopes

2. **Wallet Ownership Verification** (`app/wallet.py`)
   - Uses `eth-account` library to verify signatures
   - Message format: `radius-verify:{entity_id}:{YYYY-MM-DD}`
   - Messages expire after 7 days, verifications expire after 90 days
   - Rejects if recovered address doesn't match claimed wallet

3. **Transaction Ingestion + Risk Scoring** (`app/risk.py`, `app/main.py`)
   - POST /v1/transactions/ingest
   - Returns risk_score (0-100), risk_level (low/medium/high/critical)
   - Amount-based and chain-based risk factors
   - Idempotency via external_id

4. **Sanctions Screening** (`app/sanctions.py`)
   - Checks wallets against local blocklist
   - Includes real OFAC addresses (Tornado Cash, Lazarus Group, Garantex)
   - Returns `sanctions_result: "failed"` and blocks transaction

5. **Audit Records** (`app/models.py`, `app/storage.py`)
   - Complete structured record per transaction
   - Links business context to on-chain tx hash
   - Tracks approvals, reconciliation status

6. **CSV/JSON Export** (`app/main.py`)
   - GET /v1/reports/export?format=csv|json
   - Filterable by date range and business_id
   - Saves to `exports/latest_audit_export.csv`

### API Endpoints

```
GET  /v1/health                          # Public health check
POST /v1/transactions/ingest             # Submit transaction for compliance
GET  /v1/transactions                    # List transactions (filterable)
GET  /v1/transactions/{id}/audit         # Get audit record
POST /v1/wallets/verify                  # Verify wallet ownership
POST /v1/payments/annotate               # Add tx_hash after execution
GET  /v1/reports/export                  # Export audit records
POST /v1/travel-rule/transmit            # Transmit Travel Rule data
GET  /v1/travel-rule/check               # Pre-flight Travel Rule check
GET  /v1/travel-rule/jurisdictions       # List supported jurisdictions
```

### Key Files

```
app/
├── main.py          # FastAPI app, all endpoints
├── auth.py          # API key authentication
├── database.py      # SQLAlchemy database config
├── db_models.py     # Database table models
├── models.py        # Pydantic API models
├── repositories.py  # Data access layer
├── risk.py          # Risk scoring logic
├── sanctions.py     # OFAC blocklist
├── storage.py       # In-memory store (fallback)
├── travel_rule.py   # Travel Rule threshold logic (24+ jurisdictions)
├── wallet.py        # Signature verification

scripts/
├── demo.py              # Full demo script (run this to showcase)
├── test_flow.py         # Quick test script
├── test_travel_rule.py  # Travel Rule threshold testing

docs/
├── gaps.md          # Tracking what's done/remaining
├── api.md           # API spec
├── architecture.md  # System design

exports/
└── latest_audit_export.csv  # Most recent export
```

---

## What's Remaining (from gaps.md)

### Medium Priority

1. **Travel Rule Threshold Logic** ✅ DONE
   - Implements FATF Recommendation 16 for 24+ jurisdictions
   - US: $3,000 threshold, EU: €0 (all transactions), UK: £1,000, SG: SGD 1,500
   - Self-hosted wallet verification for EU/UK/CH amounts >€1,000
   - Cross-border uses stricter jurisdiction's rules
   - New endpoints: GET /v1/travel-rule/check, GET /v1/travel-rule/jurisdictions

2. **PostgreSQL Persistence** ✅ DONE
   - SQLAlchemy ORM with PostgreSQL support
   - SQLite fallback for local development (no setup required)
   - 6 database tables for all entities
   - Repository pattern for clean data access
   - Set DATABASE_URL env var for PostgreSQL

### Low Priority (Post-MVP)

- KYC/KYB provider integration (Persona, Jumio)
- Real Travel Rule transmission (Notabene, Sygna)
- ERP integrations (NetSuite, QuickBooks)
- Dashboard UI
- Webhook notifications
- Rate limiting
- Multi-tenancy isolation

---

## Running the App

```bash
# Install dependencies
pip install fastapi uvicorn eth-account requests

# Start server
uvicorn app.main:app --reload

# Run demo
python scripts/demo.py

# Quick test
python scripts/test_flow.py
```

---

## Demo Script Output

The demo (`scripts/demo.py`) walks through:

1. Health check (public endpoint)
2. Auth required (401 without key, 200 with key)
3. Wallet verification (valid sig accepted, wrong wallet rejected)
4. Clean transaction flow (ingest → annotate → audit record)
5. Sanctions blocking (Tornado Cash wallet blocked)
6. CSV/JSON export

Takes ~15 seconds to run. Good for investor/customer demos.

---

## Next Steps to Finish MVP

### Option A: Minimal MVP (Demo-Ready)
What you have now is demo-ready. You can show:
- The full compliance flow works
- Sanctions screening blocks bad wallets
- Wallet verification proves ownership
- Audit records are exportable

**Recommendation:** Start showing to potential customers now and gather feedback.

### Option B: Production-Ready MVP
Add these before real customers:

1. **PostgreSQL persistence** - So data survives restarts
2. **Real API key generation** - Database-backed, not hardcoded
3. **Travel Rule thresholds** - Flag large transactions
4. **Basic rate limiting** - Prevent abuse

### Option C: Integration-Ready MVP
Add real provider integrations:

1. **Chainalysis/TRM/Elliptic** - Real-time wallet risk scoring
2. **Notabene/Sygna** - Travel Rule transmission
3. **Persona/Jumio** - KYC verification

---

## Architecture Reminder

```
Business App (customer)
    ↓
Radius SDK / API
    ↓
Compliance Engine (this codebase)
    ↓
Blockchain + Wallet Providers (Circle, Fireblocks, etc.)
```

Radius does NOT:
- Custody funds
- Move money
- Hold private keys

Radius DOES:
- Observe transactions
- Verify identities
- Screen for sanctions
- Create audit records
- Export reports

---

## Business Context

**Problem:** Companies want to use stablecoins but avoid it because of compliance complexity.

**Solution:** One API call makes any stablecoin payment compliant and audit-ready.

**Target Customers:**
- Marketplaces paying sellers
- Payroll platforms paying contractors
- Fintechs with cross-border payments
- Any company moving >$1M/month in stablecoins

**Pricing Model:**
- Per-transaction fee, or
- Monthly volume tiers
- Target: $2K-$10K+/month per customer
