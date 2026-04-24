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

> Reordered to unblock the first customer as fast as possible:
> 3.1 developer signup → 3.2 multi-source sanctions → 3.3 dashboard login → 3.4 SDKs → 3.5 landing page → 3.6 SOC 2
>
> Rationale: nothing else matters if there's no door for a customer to walk through.
> Sanctions expansion unlocks EU/UK market before we invest in SDK/dashboard polish.
> Dashboard login (human auth) comes after sanctions because it's the more complex build.
> SDKs are a multiplier on customers you already have, not a way to get the first one.

### 3.1 Developer Signup — API Key Provisioning
> **Why:** This is the only gap that blocks a real customer from using the product today.
> Without it, every other improvement is invisible — no one can reach it.
> Ship the lightweight path first: signup endpoint + Tally form. Full self-serve UI comes later.

- [x] **Signup endpoint** `POST /v1/signup`
  - Accepts direct JSON `{ business_name, email, intended_use }` or Tally webhook payload
  - Creates a `Business` record (id: biz_xxx, name, email, plan: sandbox) + `sk_sandbox_...` key
  - Returns plaintext key once (only hash stored in DB); 409 on duplicate email
  - Welcome email sent via Resend with key, business_id, and quickstart steps

- [x] **Key types: sandbox vs live**
  - `sk_sandbox_...` — generated at signup, full API access, data isolated by business_id
  - `sk_live_...` — manually provisioned by Radius team after review (Option A)
  - `Business.plan` field: "sandbox" (default) | "live"; `upgrade_to_live()` in BusinessRepository

- [x] **Key rotation endpoint** `POST /v1/api-keys/{key_id}/rotate`
  - Revokes old key, issues new one with same prefix/scopes/name
  - 404 if key doesn't belong to authenticated business (no tenant enumeration)
  - Returns new plaintext key once

- [x] **Wire a Tally/Typeform form to the signup endpoint**
  - Form fields: company name, email, how they plan to use Radius
  - On submit → POST to `/v1/signup` → show the generated key once
  - Tally webhook format auto-detected and normalised — no changes needed to the endpoint
  - This is the "Get API Key" CTA destination for the landing page

### 3.2 Multi-Source Sanctions
> **Why:** OFAC covers US-designated entities. EU and UK customers are legally required
> to screen against the EU consolidated list and UN Security Council list respectively.
> Without these, a "passed" result from Radius is incomplete for non-US deals —
> a liability, not a feature.
> OpenSanctions aggregates 40+ lists in one API so we get coverage without parsing
> three separate XML feeds ourselves.

- [x] **Add OpenSanctions API integration**
  - OpenSanctions aggregates OFAC + EU + UN + 40 other lists in one API
  - Free tier available for startups (self-hosted also available)
  - `services/opensanctions.py`: `check_wallet()` using CryptoWallet schema, 5s timeout, 0.95 min score
  - Fallback chain: OpenSanctions → OFAC local → hardcoded fallback list
  - `SANCTIONS_PROVIDER=opensanctions` + `OPENSANCTIONS_API_KEY` env vars

- [x] **Add EU consolidated sanctions list (direct)**
  - Covered via OpenSanctions `eu_fsf` dataset (no separate XML parser needed)
  - `list_source` field shows "EU_FSF" when EU list is the match source

- [x] **Add UN Security Council list (direct)**
  - Covered via OpenSanctions `un_sc_sanctions` dataset
  - `list_source` field shows "UN_SC" when UN list is the match source

### 3.3 Dashboard Login — Human Auth
> **Why:** Compliance officers, finance teams, and auditors need to log into the dashboard
> with email + password. API keys don't fit this workflow — they're not developers.
> This is the second user type, and it's what unlocks Radius being useful beyond just
> the initial integration.
> Use an auth provider (Clerk recommended) rather than building auth from scratch —
> building auth correctly takes months and introduces serious security risk.

- [x] **Integrate Clerk (or Auth0/Supabase Auth)**
  - Clerk handles: Google OAuth + email/password login, session management, JWT issuance
  - Dual auth model: Clerk JWT for dashboard users, API keys for programmatic access
  - Both resolve to `business_id` — endpoints don't care which auth method was used

  **Backend — foundation:**
  - Add `User` model to `backend/app/db/models.py` (`clerk_user_id` → `business_id` mapping, `email`, `role`)
  - Add `UserRepository` to `backend/app/db/repositories.py` (`get_by_clerk_id`, `create`, `list_by_business`)
  - Add Clerk config to `backend/app/core/config.py` (`CLERK_SECRET_KEY`, `CLERK_JWKS_URL` env vars)
  - Add `PyJWT[crypto]>=2.8` to `backend/requirements.txt`

  **Backend — Clerk JWT verification:**
  - New `backend/app/core/clerk.py`: fetch + cache JWKS keys, verify RS256 JWT, extract `sub` (Clerk user ID)
  - JWKS URL derived from Clerk publishable key (base64-encoded Frontend API domain)
  - 1-hour key cache with auto-refresh

  **Backend — unified auth dependency:**
  - Add `AuthInfo` dataclass to `backend/app/core/auth.py` (`business_id`, `auth_type`, `scopes`, `user_id`, `key_id`)
  - Add `require_auth()` dependency: checks `Authorization: Bearer <jwt>` first, then `X-API-Key` fallback
  - Clerk users get `dashboard:all` scope (read access to transactions, audit, reports)
  - Export `AuthInfo` + `require_auth` from `backend/app/core/__init__.py`

  **Backend — endpoints:**
  - New `backend/app/api/auth.py` with `GET /v1/auth/me` (returns business name, email, auth type)
  - Auto-provisioning on first Clerk login: match email → existing Business, or create new Business + User
  - Switch read endpoints to `require_auth`: `GET /v1/transactions`, `GET /v1/transactions/{id}/audit`, `GET /v1/reports/export`
  - Write endpoints stay `require_api_key`-only: `POST /ingest`, `/annotate`, `/verify`, `/transmit`

  **Frontend — Clerk integration:**
  - `npm install @clerk/clerk-react` in `frontend/`
  - Add `VITE_CLERK_PUBLISHABLE_KEY` to `frontend/.env.local`
  - Wrap app with `<ClerkProvider>` in `frontend/src/main.jsx`
  - Replace `ApiKeyInput.jsx` with new `LoginPage.jsx` using Clerk's `<SignIn />` component
  - Rewrite `App.jsx`: use `useUser()` + `useAuth()` hooks, `<SignedIn>`/`<SignedOut>` gating
  - Update `api.js`: replace localStorage `X-API-Key` with `Authorization: Bearer` token from `getToken()`
  - Update `Filters.jsx` logout button to use Clerk's `signOut()`
  - Show business name in header via `/v1/auth/me` endpoint

- [x] **Scope dashboard access to business_id**
  - After login, user can only see their own business's transactions
  - Already enforced at the data layer — just needs the auth layer wired up
  - `require_auth()` extracts `business_id` from User record (Clerk) or APIKey record (API key)

- [x] **Key management UI in dashboard**
  - View active API keys, their scopes, and last-used timestamp
  - Create new keys with specific scopes (write-only for payment system, read-only for auditors)
  - Revoke keys

### 3.4 SDKs
> **Why:** Reduces developer integration time from days to hours.
> A `pip install radius-python` is a much lower barrier than reading API docs and
> writing HTTP calls from scratch. SDKs are a multiplier on customers you already have.
> Build only after the API is stable — changing an endpoint after publishing breaks SDK consumers.

- [x] **Python SDK** (`getradius`)
  - `Product/sdks/python/` — `pip install getradius`, single dep: `requests>=2.28`
  - Resource-based client: `client.transactions.ingest()`, `.payments.annotate()`, `.wallets.verify()`, `.travel_rule.check()`, `.reports.export_json()`
  - Stdlib dataclass models: Entity, IngestResponse, AuditRecord, etc.
  - Typed exception hierarchy: RadiusError → BadRequestError, AuthenticationError, NotFoundError, RateLimitError, ServerError
  - `User-Agent: getradius-python/0.1.0` on all requests
  - Publish to PyPI

- [x] **TypeScript SDK** (`@getradius/sdk`)
  - `Product/sdks/typescript/` — `npm install @getradius/sdk`, zero runtime deps (native `fetch`)
  - Resource-based client: `client.transactions.ingest()`, `.payments.annotate()`, `.wallets.verify()`, `.travelRule.check()`, `.reports.exportJson()`
  - Full TypeScript interfaces for all API responses
  - Typed exception hierarchy matching Python SDK
  - `User-Agent: getradius-ts/0.1.0` on all requests; Node.js >= 18
  - Publish to npm

### 3.5 Landing Page
> **Why:** The landing page exists and is deployed. The missing pieces are the pricing
> table and the "Get API Key" CTA — the CTA was blocked on 3.1 (signup endpoint),
> which is now done. Wire it up.

- [ ] **Add pricing table**
  - Free / Starter ($99/mo) / Growth ($499/mo) / Enterprise (custom)
  - Show per-check pricing and monthly caps per tier

- [ ] **Wire "Get API Key" CTA to signup flow**
  - Button links to Tally form (built in 3.1) or the hosted signup page
  - Remove any placeholder CTAs

- [ ] **Link to API docs**
  - FastAPI auto-generates docs at `/docs` — just needs a visible link

### 3.6 SOC 2 Prep
> **Why:** Enterprise customers (>$20M/month stablecoin volume) require SOC 2 Type I
> before signing a contract. The audit takes 3-6 months from engagement to report.
> Starting now means you could have it in hand when you close your first enterprise deal.
> This runs in parallel with 3.1-3.5 — it's mostly vendor engagement + process docs, not code.

- [ ] **Engage SOC 2 auditor**
  - Get quotes from Vanta, Drata, or Secureframe (automated compliance platforms)
  - Typical cost: $10K-$30K for Type I
  - Vanta/Drata dramatically reduce prep time by auto-collecting evidence from GitHub, AWS, etc.

- [ ] **Implement required controls**
  - Access management: who can access production, MFA required for all team members
  - Encryption: data at rest (DB encryption), in transit (HTTPS only — enforced by Railway/Vercel)
  - Incident response plan (documented procedure in Notion or Google Docs)
  - Change management: all production changes via CI/CD (already done in 2.1), no manual deploys
  - Audit logging: `audit_records` table already exists — verify completeness of coverage

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
