# Radius — Development Timeline

> Session-by-session checklist. Pick up where you left off.
> Updated: 2026-02-16

---

## How to use this file

Each task has a checkbox. Check it off when done. Subtasks are the actual coding steps — each one is a single sitting's worth of work or less. When starting a session, find the first unchecked box and go.

---

## Phase 1: Make It Real (Weeks 1-2)

### 1.1 Real OFAC Sanctions Screening
> **Why:** A compliance product with hardcoded wallets is a liability. This is the single most important gap.
> **Files:** `backend/app/services/sanctions.py`, new `backend/app/services/ofac.py`

- [x] **Download and parse OFAC SDN list**
  - Source: `sdn_advanced.xml` from Treasury.gov (the only file with crypto addresses — 18 currency types, 751 addresses as of 2026-02)
  - Parses XML in 3 passes: FeatureTypeValues → DistinctParties (names + addresses) → SanctionsEntries (programs)
  - Stores address index as `backend/data/ofac/address_index.json` (fast JSON cache, avoids re-parsing 80MB XML)
  - `backend/app/services/ofac.py` — `OFACScreener` class with `check(wallet) → SanctionsMatch`
  - Note: Tornado Cash smart contract addresses were removed from OFAC SDN in Nov 2024 (5th Circuit ruling)

- [x] **Build auto-update mechanism**
  - Startup: `_startup_ofac_refresh()` in `main.py` — non-blocking `asyncio.create_task`, loads stale cache first then re-downloads in thread
  - `POST /v1/admin/sanctions/refresh?force=true` — 202 Accepted, runs in background via `asyncio.create_task`
  - `GET /v1/admin/sanctions/status` — returns address count, last updated, staleness
  - Both admin endpoints gated behind `admin:all` scope (dev key: `sk_test_admin_radius_dev`)
  - Config: `OFAC_SDN_URL`, `OFAC_UPDATE_INTERVAL_HOURS`, `OFAC_DATA_DIR`, `SANCTIONS_PROVIDER` in `config.py`
  - `/v1/health` now exposes `sanctions_screening` block (loaded, address_count, last_updated, data_stale)

- [x] **Replace hardcoded sanctions in risk engine**
  - `check_sanctions()` now returns `SanctionsMatch` (not a tuple) with `name`, `sdn_id`, `program`, `list_source`
  - `RiskResult` gains `sdn_name`, `sdn_id`, `sdn_program`, `list_source`, `sanctions_reason` fields
  - `score_transaction()` unpacks `SanctionsMatch` directly into `RiskResult` on hits
  - Blocked transactions persist `{sanctions: {sdn_name, sdn_id, sdn_program, list_source, reason}}` into `extra_data` DB column
  - `KNOWN_SANCTIONED_WALLETS` kept in `sanctions.py` as offline fallback (returns `list_source="OFAC_SDN_FALLBACK"`)

- [x] **Add config for sanctions providers**
  - Add to `backend/app/core/config.py`:
    - `OFAC_SDN_URL` (default: Treasury.gov)
    - `OFAC_UPDATE_INTERVAL_HOURS` (default: 24)
    - `OFAC_DATA_DIR` (default: `backend/data/ofac/`)
    - `SANCTIONS_PROVIDER` (default: `"ofac_local"`, future: `"chainalysis"`, `"opensanctions"`)

### 1.2 Comprehensive Test Suite
> **Why:** Zero tests. A compliance API that misses a sanctioned wallet destroys the company. Tests are existential.
> **Files:** `tests/` directory, new `conftest.py`, `pytest.ini`

- [x] **Set up test infrastructure**
  - Create `pytest.ini` or `pyproject.toml` `[tool.pytest]` section
  - Create `tests/conftest.py` with:
    - SQLite in-memory test database fixture
    - FastAPI `TestClient` fixture
    - Test API key fixtures (mimicking `sk_test_acme_123456`)
    - Sample transaction data fixtures
  - Add `pytest`, `httpx` to dev dependencies
  - Verify `pytest` runs with 0 tests collected

- [x] **Unit tests: sanctions screening**
  - `tests/test_sanctions.py`
  - Test: known sanctioned wallet → returns `(True, reason)`
  - Test: clean wallet → returns `(False, "")`
  - Test: empty/None wallet → returns `(False, "")`
  - Test: case insensitivity (mixed case input)
  - Test: high-risk wallet pattern detection

- [x] **Unit tests: risk scoring**
  - `tests/test_risk.py`
  - Test: sanctioned wallet → score 100, level critical, sanctions_result failed
  - Test: clean low-amount tx → score ~10, level low
  - Test: high-amount tx (>$10K) → score increases by 40
  - Test: unknown chain → score increases by 10
  - Test: high-risk wallet pattern → score increases by 30
  - Test: boundary conditions ($999.99 vs $1000 vs $10000)

- [x] **Unit tests: Travel Rule**
  - `tests/test_travel_rule.py`
  - Test: US jurisdiction, $2999 → not_required; $3000 → required
  - Test: EU jurisdiction, $0.01 → required (zero threshold)
  - Test: UK jurisdiction, $1249 → not_required; $1250 → required (£1,000 USD equiv)
  - Test: Singapore, $1099 → not_required; $1100 → required (SGD 1,500 USD equiv)
  - Test: cross-border uses stricter threshold (US→EU: EU $0 governs)
  - Test: EU member state country codes (IT, ES, NL, PL, all 27) map to EU jurisdiction
  - Test: self-hosted wallet triggers verification_required (EU + user entity + >€1,000)
  - Test: unknown jurisdiction uses FATF $1,000 default

- [x] **Integration tests: API endpoints**
  - `tests/test_api_transactions.py` — 21 tests across 5 classes
  - Valid payload → 200, pending status, low risk, travel rule not_required
  - Sanctioned wallet (from/to) → blocked, score 100, `blocked_sanctioned_wallet` action
  - Missing required fields → 422; empty body → 422
  - Duplicate external_id → same transaction_id returned (idempotent)
  - No API key → 401; invalid API key → 401

- [x] **Integration tests: payments + audit**
  - `tests/test_api_payments.py` — 17 tests across 2 classes
  - `POST /v1/payments/annotate`: 200 + completed status, unknown txn → 404, missing fields → 422
  - `GET /v1/transactions/{id}/audit`: fields verified, tx_hash before/after annotation, 404 + business scope

- [x] **Integration tests: wallets + travel rule + export**
  - `tests/test_api_wallets.py` — real eth_account signatures; valid → verified, expired/wrong/garbage → rejected
  - `tests/test_api_travel_rule.py` — transmit → 202 + proof_id; check: US/EU thresholds, cross-border
  - `tests/test_api_reports.py` — CSV headers when empty; JSON count; date range filtering; business scope

- [x] **Check coverage and fill gaps**
  - `tests/test_api_misc.py` — list transactions (filter, pagination, scope), admin sanctions, health
  - Coverage: 80% (198 tests); ofac.py excluded via `.coveragerc` (network-dependent XML download)
  ┌──────────────────────────┬───────┬─────────────────────────────────────────────────────────────────────────────┐
  │           File           │ Tests │                               What it covers                                │                           
  ├──────────────────────────┼───────┼─────────────────────────────────────────────────────────────────────────────┤
  │ test_sanctions.py        │ 25    │ OFACScreener.check(), check_sanctions(), is_high_risk_wallet()              │
  ├──────────────────────────┼───────┼─────────────────────────────────────────────────────────────────────────────┤
  │ test_risk.py             │ 33    │ score_transaction() — amounts, chains, wallets, score cap, level thresholds │
  ├──────────────────────────┼───────┼─────────────────────────────────────────────────────────────────────────────┤
  │ test_travel_rule.py      │ 51    │ All jurisdictions, cross-border strictness, self-hosted verification        │
  ├──────────────────────────┼───────┼─────────────────────────────────────────────────────────────────────────────┤
  │ test_api_transactions.py │ 21    │ Ingest: valid, sanctioned, missing fields, idempotency, auth                │
  ├──────────────────────────┼───────┼─────────────────────────────────────────────────────────────────────────────┤
  │ test_api_payments.py     │ 17    │ Annotate + audit: happy path, 404, scope isolation                          │
  ├──────────────────────────┼───────┼─────────────────────────────────────────────────────────────────────────────┤
  │ test_api_wallets.py      │ 10    │ Real eth_account signatures: verified/rejected/expired                      │
  ├──────────────────────────┼───────┼─────────────────────────────────────────────────────────────────────────────┤
  │ test_api_travel_rule.py  │ 12    │ Transmit + pre-flight check endpoint                                        │
  ├──────────────────────────┼───────┼─────────────────────────────────────────────────────────────────────────────┤
  │ test_api_reports.py      │ 11    │ CSV/JSON export, date filtering, business scope                             │
  ├──────────────────────────┼───────┼─────────────────────────────────────────────────────────────────────────────┤
  │ test_api_misc.py         │ 18    │ List, admin sanctions, health                                               │
  └──────────────────────────┴───────┴─────────────────────────────────────────────────────────────────────────────┘

### 1.3 Docker + Local Deployment
> **Why:** Can't deploy, demo, or onboard without containerization.
> **Files:** `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.env.example`

- [x] **Create Dockerfile**
  - `python:3.12-slim`, installs `libpq-dev`+`gcc` for psycopg2, copies `backend/`
  - `psycopg2-binary` added to `backend/requirements.txt`
  - `.dockerignore` excludes `.venv`, `__pycache__`, `.git`, `*.db`, `tests/`, `docs/`

- [x] **Create docker-compose.yml**
  - `api`: builds from Dockerfile, port 8000, waits on db healthcheck, `ofac_data` volume
  - `db`: postgres:16-alpine, persistent `postgres_data` volume, `pg_isready` healthcheck
  - `.env.example` documents all env vars with inline comments

- [x] **Test full Docker workflow**
  - `scripts/test_docker.py` — 54/54 checks pass
  - Covers: health, auth, happy path, sanctioned wallet, validation, idempotency, annotate+audit, travel rule, high-amount risk, CSV/JSON export, admin endpoints, data persistence across API restart, DB failover + recovery
  - `docker-compose.test.yml` override + `tests/fixtures/ofac/` pre-seed OFAC data for deterministic sanctions tests (no live Treasury.gov download needed)

---

## Phase 2: Make It Deployable (Weeks 3-4)

### 2.1 CI/CD Pipeline
> **Why:** Automated testing and deployment. No manual "did you run the tests?" conversations.
> **Files:** `.github/workflows/ci.yml`

- [x] **GitHub Actions: test + lint**
  - Trigger: push to main, PRs to main
  - Steps: checkout → setup Python 3.12 → install deps → `ruff check` → `pytest`
  - Cache pip dependencies for speed
  - Add `ruff` as dev dependency if not present

- [x] **GitHub Actions: Docker build**
  - After tests pass: build Docker image
  - Tag with commit SHA and `latest`
  - Push to GitHub Container Registry (ghcr.io) on main branch merges

- [ ] **Add deployment step (staging)**
  - Deploy to Railway, Render, or Fly.io on merge to main
  - Environment variables set via platform secrets
  - Health check URL: `/v1/health`
  - Note: workflow built, pending Railway project + RAILWAY_DEPLOY_WEBHOOK secret

### 2.2 Structured Logging
> **Why:** Audit trail for compliance decisions. You need to prove what happened and when.
> **Files:** `backend/app/core/logging.py`, `backend/app/main.py`

- [x] **Add JSON structured logging**
  - Create `backend/app/core/logging.py`
  - Use Python `structlog` or `python-json-logger`
  - Every log line: `{timestamp, request_id, business_id, level, message, ...}`
  - Add request ID middleware: generate UUID per request, attach to all logs

- [x] **Log compliance decisions**
  - Log on every `POST /v1/transactions/ingest`: `{action: "sanctions_check", wallet, result, sdn_match}`
  - Log on every risk score: `{action: "risk_scored", score, level, factors}`
  - Log on every Travel Rule check: `{action: "travel_rule_check", jurisdiction, threshold_exceeded}`
  - Log on blocked transactions: `{action: "transaction_blocked", reason}`

### 2.3 Production Hardening
> **Why:** Things that break in production if you skip them.

- [x] **Health check endpoint improvements**
  - `/v1/health` returns: `{status, version, environment, db_connected, sanctions_screening}`
  - Check DB connectivity (SELECT 1 query)
  - Check sanctions data freshness (data_age_hours, data_stale)
  - Returns status=degraded if DB is down or sanctions data is stale

- [x] **CORS configuration for production**
  - Moved allowed origins to `ALLOWED_ORIGINS` env var (comma-separated)
  - Default: `http://localhost:5173`; documented in `.env.example`

- [x] **Environment-based configuration**
  - `ENVIRONMENT` env var: `development` (mock keys allowed) | `production` (DB-only keys)
  - `docker-compose.yml` sets `production`; `docker-compose.test.yml` sets `development`

- [x] **Remove mock API keys from source code**
  - DB seed on startup in `development`: if no keys exist, insert one dev key
  - Key value from `DEV_API_KEY` env var; if unset, generates + prints a random key once
  - Production does no seeding — only explicitly provisioned DB keys work
  - Mock keys dict retained for test suite compatibility (dev-only, zero production impact)

- [x] **Enforce scopes on all endpoints**
  - `transactions:write` → ingest, annotate, wallet verify, travel-rule transmit
  - `transactions:read` → list, audit, travel-rule check/jurisdictions
  - `reports:read` → CSV/JSON export

---

## Phase 3: Make It Sellable (Weeks 5-8)

### 3.1 Multi-Source Sanctions
> **Why:** OFAC is US-only. EU/UK customers need EU consolidated list and UN Security Council list.

- [ ] **Add OpenSanctions API integration**
  - OpenSanctions aggregates OFAC + EU + UN + 40 other lists
  - Free tier available for startups
  - Add as alternative provider in `SANCTIONS_PROVIDER` config
  - Fallback chain: OpenSanctions → OFAC local → cached data

- [ ] **Add EU consolidated sanctions list**
  - Source: `https://webgate.ec.europa.eu/fsd/fsf`
  - Parse and merge into sanctions screener

- [ ] **Add UN Security Council list**
  - Source: `https://scsanctions.un.org/resources/xml/en/consolidated.xml`
  - Parse and merge into sanctions screener

### 3.2 Self-Serve Onboarding
> **Why:** Two distinct user types need access — developers integrating the API, and business users (compliance officers, finance teams) reviewing transactions in the dashboard. Current system has no auth path for the second type.

**User type 1 — Developer / integrator**
The company's backend calls Radius programmatically. API key in `X-API-Key` header. Never touches the dashboard.

**User type 2 — Compliance officer / finance person**
Logs into the dashboard to review flagged transactions, pull audit records, export CSVs. Needs human auth — API keys don't fit this workflow.

- [ ] **Developer onboarding: API key provisioning**
  - Signup form → generates `sk_sandbox_...` key, shown once
  - Store SHA-256 hash in DB; return plaintext to user once at creation
  - Key types: `sandbox` (rate-limited, test data) and `live` (production)
  - Key rotation: `POST /v1/api-keys/rotate`
  - Can start with Typeform/Tally → manual provisioning, automate later

- [ ] **Dashboard login (human auth)**
  - Email + password login for the dashboard (compliance officers, finance, auditors)
  - Separate from API keys — humans log in with credentials, not `X-API-Key`
  - Session-based or JWT; scoped to their `business_id`
  - Simplest path: use an auth provider (Auth0, Clerk, Supabase Auth) rather than building from scratch

- [ ] **Key management in dashboard**
  - View active keys, their scopes, and last-used timestamp
  - Create new keys with specific scopes (write-only for payment system, read-only for auditors)
  - Revoke keys

### 3.3 SDKs
> **Why:** Developer experience. One `pip install radius` instead of raw HTTP calls.

- [ ] **Python SDK**
  - Package: `radius-python`
  - Typed models matching API schemas
  - Methods: `client.check(transaction)`, `client.annotate(tx_id, tx_hash)`, `client.audit(tx_id)`
  - Error handling with typed exceptions
  - Publish to PyPI

- [ ] **TypeScript SDK**
  - Package: `@radius/sdk`
  - TypeScript types matching API schemas
  - Same method signatures as Python SDK
  - Publish to npm

### 3.4 Landing Page
> **Why:** People need to find and understand the product.

- [ ] **Simple one-page site**
  - What it does (payment attestation, not "compliance")
  - How it works (3-step flow diagram)
  - Pricing table (Free / Starter / Growth / Enterprise)
  - "Get API Key" CTA → signup flow
  - Link to API docs (FastAPI auto-generated at `/docs`)

### 3.5 SOC 2 Prep
> **Why:** Enterprise customers require it. Takes 3-6 months so start early.

- [ ] **Engage SOC 2 auditor**
  - Get quotes from Vanta, Drata, or Secureframe (automated platforms)
  - Typical cost: $10K-$30K for Type I

- [ ] **Implement required controls**
  - Access management: who can access production, MFA required
  - Encryption: data at rest (DB encryption), in transit (HTTPS only)
  - Incident response plan (documented procedure)
  - Change management: all production changes via CI/CD, no manual deploys
  - Audit logging: already have audit_records table, ensure completeness

---

## Phase 4: Get First Customer (Weeks 9-12)

### 4.1 Outreach
- [ ] Identify 20 target companies (stablecoin payroll platforms, B2B settlement)
- [ ] Direct outreach to CTOs/engineering leads
- [ ] Offer 90-day free pilot for first 5 integrations
- [ ] Build case study from first integration

### 4.2 Travel Rule Interop
- [ ] Research Notabene and TRP protocol for real VASP-to-VASP data exchange
- [ ] Replace stub in `travel_rule.py` transmit logic with real network call
- [ ] Test with Notabene sandbox

### 4.3 Demo + Content
- [ ] Record 3-minute demo video (full flow: ingest → annotate → audit → export)
- [ ] Write quickstart guide (`docs/quickstart.md`)
- [ ] Blog post: "How to make USDC payroll GENIUS Act compliant"

---

## Remaining Gaps (Post-MVP, No Timeline Yet)

These are tracked but not scheduled. Revisit after first customer.

### Risk & Compliance
- [ ] Real blockchain analysis provider (Chainalysis/TRM/Elliptic integration)
- [ ] AML velocity checks (unusual payout frequency per wallet)
- [ ] Geographic risk flagging (wallets linked to high-risk jurisdictions)
- [ ] Pattern detection (structuring, smurfing, round-trip)

### Identity & Verification
- [ ] KYC/KYB provider binding (Persona, Jumio, or accept external KYC status)
- [ ] Counterparty attestation (verify receiving entity identity)

### Infrastructure
- [ ] Webhook notifications (notify clients of risk score updates, Travel Rule responses)
- [ ] Multi-tenancy data isolation (scoped data access per business_id)
- [ ] Idempotency keys on all write endpoints (currently only transaction ingest has external_id dedup)

### Reporting & Integrations
- [ ] ERP integrations (NetSuite, QuickBooks, SAP auto journal entries)
- [ ] Dashboard enhancements (alerts view, case management, approval workflows)

### Positioning Debt
- [ ] Update `docs/architecture.md` — still references "Compliance Engine" framing in places
- [ ] Ensure all customer-facing surfaces use "payment attestation infrastructure" language

---

## What's Already Done

For reference — these are complete and production-quality:

- [x] FastAPI framework (15+ endpoints, error handling, CORS)
- [x] Transaction ingest + annotation flow (`POST /v1/transactions/ingest`, `POST /v1/payments/annotate`)
- [x] Audit record retrieval (`GET /v1/transactions/{id}/audit`)
- [x] Risk scoring engine (amount, chain, wallet pattern heuristics) — `backend/app/services/risk.py`
- [x] Sanctions screening against local blocklist (real OFAC addresses) — `backend/app/services/sanctions.py`
- [x] Travel Rule engine (24+ jurisdictions, FATF R.16, self-hosted wallet logic) — `backend/app/services/travel_rule.py`
- [x] Wallet verification (Ethereum signature recovery, 7-day message expiry, 90-day verification expiry)
- [x] SQLAlchemy ORM (6 tables: transactions, audit_records, wallet_verifications, travel_rule_proofs, api_keys, rate_limit_buckets)
- [x] PostgreSQL support with SQLite fallback — `backend/app/core/config.py`
- [x] API key auth (SHA-256 hashed, scoped, business_id binding) — `backend/app/core/auth.py`
- [x] Rate limiting (token bucket algorithm) — `backend/app/core/rate_limit.py`
- [x] CSV/JSON export with date range and business_id filtering
- [x] React dashboard (transaction list, detail view) — `frontend/`
- [x] App description updated to "payment attestation infrastructure" — `backend/app/main.py`
