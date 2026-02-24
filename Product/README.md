# Radius

Payment attestation infrastructure for stablecoin transfers.

Turn every stablecoin transaction into an audit-ready financial record — automatically.

---

## Overview

Companies fail not because they cannot send stablecoin payments, but because they **cannot explain them later**.

When accounting needs to close books, when banks ask for source-of-funds documentation, when investors request payment controls, or when expanding to new jurisdictions — the payment history must be more than blockchain hashes.

**Radius creates a structured, permanent record at send-time.**

### What we do:
- Transaction attestation (sanctions screening, risk scoring, Travel Rule)
- Wallet identity verification
- Audit-ready record generation
- CSV/JSON export for accounting
- Web dashboard for compliance teams

### What we don't do:
- ❌ We don't custody funds
- ❌ We don't move money
- ❌ We don't provide wallets

**We observe, verify, enrich, record, and export.**

---

## Quick Start

### Prerequisites

- **Backend**: Python 3.12+
- **Frontend**: Node.js 18+

### Installation

**1. Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**2. Frontend:**
```bash
cd frontend
npm install
```

### Running the Application

**Development Mode (recommended):**

Terminal 1 - Backend API:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

Access: **http://localhost:5173**

**Production Mode:**
```bash
# Build frontend
cd frontend
npm run build

# Start backend (serves API + UI)
cd ../backend
uvicorn app.main:app --port 8000
```

Access: **http://localhost:8000**

---

## API Usage

### Authentication

All API requests require an API key via the `X-API-Key` header.

**Demo API Key:** `sk_test_acme_123456`

### Example: Ingest Transaction

```bash
curl -X POST http://localhost:8000/v1/transactions/ingest \
  -H "X-API-Key: sk_test_acme_123456" \
  -H "Content-Type: application/json" \
  -d '{
    "external_id": "pay_123",
    "direction": "outbound",
    "business_id": "acme_corp",
    "from_entity": {
      "type": "business",
      "entity_id": "acme_corp",
      "wallet": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
      "jurisdiction": "US"
    },
    "to_entity": {
      "type": "user",
      "entity_id": "contractor_123",
      "wallet": "0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199",
      "jurisdiction": "DE"
    },
    "amount": "2500.00",
    "asset": "USDC",
    "chain": "ethereum",
    "purpose": "contractor_payout"
  }'
```

### Response

```json
{
  "transaction_id": "txn_abc123",
  "status": "pending",
  "risk_score": 15,
  "risk_level": "low",
  "sanctions_result": "passed",
  "travel_rule": {
    "status": "required",
    "threshold_exceeded": true,
    "applicable_threshold": "1000",
    "threshold_currency": "EUR",
    "jurisdiction": "EU"
  },
  "required_actions": ["collect_originator_data"],
  "audit_record_id": "aud_xyz789"
}
```

### Interactive Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Dashboard Features

The web dashboard provides:

✅ **Transaction List** - View all transactions with filtering
✅ **Risk Monitoring** - Color-coded risk levels
✅ **Audit Records** - Detailed compliance info per transaction
✅ **Filtering** - By status, risk level, business ID
✅ **CSV Export** - Download transaction data
✅ **Stats Overview** - Real-time metrics

**Demo Login:** Use API key `sk_test_acme_123456`

---

## Project Structure

```
radius/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core logic (auth, errors, config)
│   │   ├── db/           # Database models & repositories
│   │   ├── services/     # Business logic (risk, sanctions, Travel Rule)
│   │   ├── schemas/      # Pydantic models
│   │   └── main.py       # Entry point
│   ├── exports/          # CSV export files
│   ├── requirements.txt  # Python dependencies
│   └── README.md         # Backend docs
│
├── frontend/             # React dashboard
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── lib/          # API client
│   │   └── App.jsx       # Main app
│   ├── package.json      # npm dependencies
│   └── README.md         # Frontend docs
│
├── docs/                 # Documentation
│   ├── README.md                      # Docs navigation
│   ├── radius_business_analysis.md   # Business strategy
│   ├── mvp_status_assessment.md      # Current status & roadmap
│   ├── api.md                         # API reference
│   ├── architecture.md                # System architecture
│   └── archive/                       # Historical docs
│
├── tests/                # Test suite (TODO)
├── CLAUDE.md             # Project instructions
└── README.md             # This file
```

---

## Core Capabilities

### 1. Payment Attestation

Before sending a stablecoin transfer, Radius creates a structured record that includes:
- Sanctions screening (OFAC/EU/UN)
- Risk scoring (0-100)
- Travel Rule requirements (30+ jurisdictions)
- Audit trail with approvals

**The record is the product. Enforcement is a feature.**

### 2. Wallet Verification

Verify wallet ownership via signed message:
- Cryptographic proof of control
- Bind wallets to KYC'd entities
- Risk tier assignment

### 3. Travel Rule Automation

Automatic detection and handling of Travel Rule obligations:
- 30+ jurisdictions with accurate thresholds
- Self-hosted wallet detection
- FATF Recommendation 16 compliant
- Ready for VASP network integration

### 4. Audit-Ready Records

Every transaction becomes a complete financial object:

```json
{
  "transaction_id": "txn_123",
  "business_id": "acme_corp",
  "from_entity": "Acme Inc",
  "to_entity": "Alice Smith",
  "wallets": {
    "from": "0x742d...",
    "to": "0x8626..."
  },
  "amount": "2500.00",
  "asset": "USDC",
  "purpose": "contractor_payout",
  "risk_score": 15,
  "risk_level": "low",
  "sanctions_result": "passed",
  "travel_rule_status": "required",
  "tx_hash": "0xabc...",
  "timestamp": "2026-02-16T12:00:00Z",
  "approvals": [...],
  "reconciliation_status": "matched"
}
```

### 5. Export & Integration

- CSV export (available now)
- JSON API export (available now)
- NetSuite integration (roadmap)
- QuickBooks integration (roadmap)
- SAP integration (roadmap)

---

## Technology Stack

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy (ORM)
- SQLite (dev) / PostgreSQL (prod)
- Pydantic (validation)

**Frontend:**
- React 18
- Vite (build tool)
- Tailwind CSS

**Deployment (planned):**
- Docker + docker-compose
- GitHub Actions (CI/CD)
- Railway/Render/AWS
- nginx/Caddy (reverse proxy)

---

## Configuration

Environment variables (create `.env` in backend/):

```bash
# Database
DATABASE_URL=sqlite:///./radius_dev.db
USE_DATABASE=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_TOKENS=100

# API
API_VERSION=0.2.0

# For production PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/radius
```

---

## Development Status

### ✅ Implemented (Production-Ready)

- API framework (FastAPI, 15+ endpoints, auth, rate limiting)
- Travel Rule engine (30+ jurisdictions, FATF R.16 compliant)
- Wallet verification (real signature verification)
- Database layer (SQLAlchemy, PostgreSQL support)
- API key authentication with business isolation
- Rate limiting (token bucket algorithm)
- Audit trail with CSV/JSON export
- Web dashboard (React + Tailwind)

### ⚠️ Implemented (Demo/Incomplete)

- **Sanctions screening** - Hardcoded ~10 addresses (needs real OFAC integration)
- **Risk scoring** - Basic heuristics (works but simple)
- **Travel Rule transmit** - Stub only (records locally, doesn't send to VASP network)

### ❌ Not Implemented (Critical Gaps)

- **Tests** - Zero unit or integration tests
- **Docker** - No containerization
- **CI/CD** - No automated testing/deployment
- **Production infra** - No monitoring, logging, or deployment
- **SOC 2** - No compliance controls

**See `docs/mvp_status_assessment.md` for detailed gap analysis and 8-week roadmap.**

---

## Roadmap

### Next 8 Weeks (Production-Ready)

**Weeks 1-2: Make It Real**
- [ ] Integrate real OFAC SDN data
- [ ] Add comprehensive tests (>80% coverage)
- [ ] Dockerize application

**Weeks 3-4: Make It Deployable**
- [ ] Set up CI/CD (GitHub Actions)
- [ ] Deploy to staging (Railway/Render)
- [ ] Add structured logging
- [ ] Create landing page

**Weeks 5-8: Make It Sellable**
- [ ] Add EU/UN sanctions lists
- [ ] Build self-serve signup flow
- [ ] Create Python & TypeScript SDKs
- [ ] Begin SOC 2 Type I
- [ ] Outreach to first customers

### Phase 2 (Months 3-6)

- [ ] First 5-10 paying customers
- [ ] SOC 2 Type I certification
- [ ] Travel Rule VASP network integration
- [ ] Advanced filtering & search

### Phase 3 (Months 6-12)

- [ ] ERP integrations (NetSuite, QuickBooks)
- [ ] Workflow approvals
- [ ] Multi-user & RBAC
- [ ] Advanced analytics

---

## Testing

**Current status:** ❌ Zero tests (critical gap)

**Planned:**
```bash
# Run test suite
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Target: >80% coverage
```

---

## Documentation

### Active Docs
- **[Business Strategy](docs/radius_business_analysis.md)** - Customer acquisition, competitive analysis, GTM plan
- **[MVP Status](docs/mvp_status_assessment.md)** - Current implementation status and roadmap
- **[API Reference](docs/api.md)** - API endpoint specifications
- **[Architecture](docs/architecture.md)** - System design and data flow

### Navigation
See [docs/README.md](docs/README.md) for documentation index.

---

## Target Customers

**Primary:**
- Stablecoin payroll platforms (Rise, Deel, Bitwage)
- Cross-border B2B settlement (BVNK, MuralPay)
- Emerging crypto on/off ramps
- Marketplaces with crypto payouts
- Cross-border fintechs

**Ideal profile:**
- $1M-$20M/month stablecoin volume
- 10-50 employees, no compliance officer
- Series A-B stage
- Facing trigger event (accounting friction, bank review, fundraising diligence, expansion)

---

## Deployment

### Development
```bash
# Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm run dev
```

### Production (when ready)
```bash
# Build frontend
cd frontend
npm run build

# Start backend
cd ../backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker (planned)
```bash
docker build -t radius .
docker run -p 8000:8000 radius
```

---

## Value Proposition

**Primary value:** Companies never reconstruct financial history again.

**Secondary value:** Companies can block risky transactions when desired.

**Outcome:** Ship stablecoin features in days instead of months.

**Customers get:**
- Compliant by default
- Audit-ready transactions
- No crypto expertise needed
- Faster time to market
- Fewer compliance hires

---

## Positioning

**We are:** Payment attestation infrastructure

**Not:** Compliance API, risk tool, or blockchain analytics

**Tagline:** Turn stablecoin transactions into audit-ready financial records.

**The record is the product. Enforcement is a feature.**

---

## Support & Contributing

- **Issues**: GitHub issues
- **Documentation**: See `docs/` folder
- **Project Instructions**: See `CLAUDE.md`

---

## License

Proprietary - Radius Compliance Platform

---

## About

Radius provides the missing audit layer for stablecoin payments — making them as easy and safe to use as traditional payment rails.

**Market validation:** Stripe acquired Bridge (stablecoin payments API) for $1.1B in Feb 2025. Bridge handles the payment rails. Nobody is handling the compliance rails at the same tier.

**We fill that gap.**
