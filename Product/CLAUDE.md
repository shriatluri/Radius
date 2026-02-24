# Radius

## One-liner
Payment attestation infrastructure for stablecoin transfers.
Turn every stablecoin transaction into an audit-ready financial record.

---

## Problem

Companies fail not because they cannot send stablecoin payments — they fail because they cannot explain them later.

When a company hits operational maturity (accounting close, bank review, fundraising diligence, international expansion), they face a painful reality: their payment history is a collection of blockchain hashes, not business records.

**Blockchain transactions store movement of money. Businesses must store intent of money.**

Current pain points:
- wallet identity unknown
- Travel Rule complexity
- AML/sanctions risk
- messy reconciliation
- auditors hate on-chain data
- accounting + ERP integration missing
- requires compliance team + crypto expertise

Result:
Stablecoins are technically useful but operationally unusable.

---

## Value Proposition

We make stablecoin payments as easy and safe as Stripe makes card payments.

**Primary value:** Companies never reconstruct financial history again.
- Accountants get structured payment records, not tx hashes
- Banks get source-of-funds documentation on demand
- Investors get proof of payment controls
- Auditors get regulator-ready compliance records

**Secondary value:** Companies can block risky transactions when desired.

**The record is the product. Enforcement is a feature.**

Outcome:
Ship stablecoin features in days instead of months.

---

## Product

Radius is a **payment attestation engine** — not a payment processor.

A middleware layer that sits between:

```
wallets / custodians / payment providers
↓
RADIUS (observe, verify, enrich, record, export)
↓
business apps (payroll, marketplaces, fintechs)
```

We DO NOT custody funds.
We DO NOT move money.

We:
- observe transactions
- verify wallets
- enrich with compliance data
- record in audit-ready format
- export for accounting/reporting

---

## Core Features

### 1. Transaction Attestation
For every transfer, create a structured record:
- sender & receiver identity
- sanctions screening (OFAC/EU/UN)
- AML risk score
- jurisdiction checks
- Travel Rule requirements
- timestamp & approval chain

### 2. Wallet Identity Verification
- proof of ownership (signed message)
- KYC/KYB binding
- counterparty attestation
- risk tiering

### 3. Travel Rule Automation
- attach originator/beneficiary metadata
- detect jurisdiction thresholds (30+ jurisdictions)
- transmit to counterparty VASP
- store proof of delivery
- regulator-ready logs

### 4. Audit-Ready Records
Each transaction becomes structured:

```json
{
  "payment_id": "pay_123",
  "business_id": "biz_456",
  "from_entity": "Acme Inc",
  "to_entity": "Contractor LLC",
  "amount": "1000.00",
  "asset": "USDC",
  "purpose": "contractor_payout",
  "risk_score": 15,
  "risk_level": "low",
  "sanctions_result": "passed",
  "travel_rule_status": "not_required",
  "tx_hash": "0xabc...",
  "timestamp": "2026-02-16T12:00:00Z",
  "approvals": [...],
  "reconciliation_status": "matched"
}
```

No raw hashes for accountants.

### 5. Accounting + ERP Export
- CSV/JSON export
- NetSuite (roadmap)
- QuickBooks (roadmap)
- SAP (roadmap)

Auto journal entries.

### 6. Unified Dashboard
- transaction list with filtering
- risk monitoring
- audit record viewer
- CSV export
- compliance alerts (roadmap)

---

## Target Customers

Primary:
- payroll platforms (Rise, Deel, Bitwage)
- B2B settlement companies (BVNK, MuralPay)
- crypto on/off ramps (emerging players)
- marketplaces with crypto payouts
- cross-border fintechs

Ideal profile:
- $1M-$20M/month stablecoin volume
- 10-50 employees, no compliance officer
- Series A-B stage
- Facing trigger event: accounting friction, bank review, fundraising diligence, or international expansion

---

## What We Are NOT

❌ wallet
❌ exchange
❌ bank
❌ custody provider
❌ payment processor

We are:
**payment attestation infrastructure**

---

## Architecture

```
Business App
    ↓
Radius SDK / API
    ↓
Attestation Engine (sanctions + risk + Travel Rule)
    ↓
Blockchain + wallet providers (Circle, Fireblocks, etc.)
```

Modules:
- ingestion service
- risk engine
- identity service
- travel rule router (30+ jurisdictions)
- ledger normalizer
- reporting/export service

Stateless + API first.

See `docs/architecture.md` for detailed flow.

---

## API Surface (MVP)

Core workflow:
1. Before sending: `POST /v1/transactions/ingest` (get compliance check)
2. After sending: `POST /v1/payments/annotate` (attach tx_hash)
3. For audit: `GET /v1/transactions/:id/audit` (get full record)

Full endpoint list:
- `POST /v1/transactions/ingest` — Create compliance record
- `POST /v1/wallets/verify` — Verify wallet ownership
- `POST /v1/payments/annotate` — Attach on-chain tx hash
- `GET /v1/transactions/:id/audit` — Get audit record
- `GET /v1/reports/export` — Export CSV/JSON
- `POST /v1/travel-rule/transmit` — Send Travel Rule data

SDKs (roadmap):
- Python
- TypeScript/Node.js

See `docs/api.md` for detailed request/response specs.

---

## Differentiation vs Existing Tools

**Chainalysis/Elliptic/TRM:**
- Risk screening only
- Enterprise pricing ($50K-$500K/year)
- No audit trail, no Travel Rule, no accounting export

**Notabene:**
- Travel Rule only
- Missing sanctions screening and risk scoring

**We:**
- Sanctions + risk + Travel Rule + audit trail + accounting export in one API
- Self-serve, developer-first
- Pay per transaction ($99-$499/month + usage)

**Positioning:** "Payment attestation infrastructure" (not just "compliance API")

End-to-end solution, not point tools.

---

## MVP Scope & Current Status

**✅ Phase 1 (Completed):**
- API framework (FastAPI, 15+ endpoints)
- Travel Rule engine (30+ jurisdictions, FATF compliant)
- Wallet verification (signature verification)
- Database layer (SQLAlchemy, PostgreSQL)
- Rate limiting & API key auth
- Audit trail with CSV export
- Web dashboard (React)

**⚠️ Phase 1 (Critical Gaps):**
- Sanctions screening is DEMO ONLY (hardcoded addresses)
- Zero tests
- No Docker/CI/CD
- No production deployment

**📋 Phase 2 (Next 8 weeks):**
- Real OFAC SDN integration
- Comprehensive test suite (>80% coverage)
- Docker + CI/CD
- Cloud deployment (staging + production)
- Self-serve signup flow
- Python & TypeScript SDKs
- SOC 2 Type I prep

**🔮 Phase 3 (Future):**
- ERP integrations (NetSuite, QuickBooks, SAP)
- Workflow approvals
- Multi-user & RBAC
- Travel Rule VASP network integration
- Advanced analytics

See `docs/mvp_status_assessment.md` for detailed roadmap.

---

## Business Model

SaaS pricing:

| Tier | Price | Target |
|---|---|---|
| Free | $0 (100 checks/mo) | Developers |
| Starter | $99/mo + $0.10/check | Seed stage |
| Growth | $499/mo + $0.05/check | Series A |
| Enterprise | Custom | Series B+ |

Target ACV: $2K-$10K+ per customer

Unit economics (10K checks/month on Growth):
- Revenue: $999/month
- Cost: ~$50/month
- Margin: ~95%

---

## Positioning

**Don't say:** "We help you comply with GENIUS Act and Travel Rule"

**Instead say:** "We turn stablecoin transactions into audit-ready financial records automatically"

Compliance becomes a feature of the attestation, not the headline.

**Elevator pitch:**
Stablecoins lack the audit layer that banks have. We provide that missing layer. Use stablecoins without worrying about regulators, audits, or AML.

**Tagline:** Payment attestation infrastructure for stablecoin transfers.
