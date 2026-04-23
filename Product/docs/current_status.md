  ---
  What Is Radius

  Payment attestation infrastructure for stablecoin transfers. Radius is a
  middleware that sits between wallet/custodian providers and business
  applications. It doesn't custody funds or move money — it observes,
  verifies, enriches, records, and exports every stablecoin transaction into
   an audit-ready financial record.

  Target customers: Stablecoin payroll platforms, B2B settlement companies,
  crypto on/off ramps (Series A-B, $1M-$20M/mo volume, no compliance
  officer).

  ---
  Repository Structure

  The repo has two top-level projects:

  ┌───────────────┬──────────────────────────────────────────────────────┐
  │   Directory   │                       Purpose                        │
  ├───────────────┼──────────────────────────────────────────────────────┤
  │ Product/      │ Main application (backend + frontend + tests)        │
  ├───────────────┼──────────────────────────────────────────────────────┤
  │ landing-page/ │ Marketing site (Vite + Tailwind, deployed to Vercel) │
  └───────────────┴──────────────────────────────────────────────────────┘

  ---
  Tech Stack

  ┌────────────┬─────────────────────────────────────────────────────────┐
  │   Layer    │                       Technology                        │
  ├────────────┼─────────────────────────────────────────────────────────┤
  │ Backend    │ Python 3.12, FastAPI, SQLAlchemy, Pydantic              │
  ├────────────┼─────────────────────────────────────────────────────────┤
  │ Database   │ SQLite (dev) / PostgreSQL (prod)                        │
  ├────────────┼─────────────────────────────────────────────────────────┤
  │ Frontend   │ React 18, Vite, Tailwind CSS                            │
  ├────────────┼─────────────────────────────────────────────────────────┤
  │ Auth       │ API keys (hashed, scoped) for API + Clerk for dashboard │
  ├────────────┼─────────────────────────────────────────────────────────┤
  │ Email      │ Resend                                                  │
  ├────────────┼─────────────────────────────────────────────────────────┤
  │ Deployment │ Docker, docker-compose                                  │
  └────────────┴─────────────────────────────────────────────────────────┘

  ---
  Backend Architecture (Product/backend/app/)

  API Layer (api/)

  All routes are under /v1. Key endpoints:
  - POST /v1/transactions/ingest — Core flow: sanctions check → risk scoring
   → Travel Rule check → audit record creation
  - GET /v1/transactions — List transactions (business-scoped)
  - POST /v1/transactions/{id}/annotate — Attach on-chain tx_hash after
  execution
  - GET /v1/transactions/{id}/audit — Get full audit record
  - POST /v1/wallets/verify — Verify wallet ownership via signed message
  - POST /v1/travel-rule/transmit — Send Travel Rule data (stub)
  - GET /v1/reports/export — CSV/JSON export
  - POST /v1/signup — Self-serve signup (supports Tally webhook format)
  - POST /v1/api-keys — API key management + rotation
  - GET /v1/auth/me — Clerk-authenticated user info

  Services Layer (services/)

  - sanctions.py — Multi-provider screening: OpenSanctions API
  (OFAC+EU+UN+40 lists) → OFAC local SDN XML → hardcoded fallback list
  - ofac.py — Downloads/parses OFAC SDN XML, builds address index,
  auto-refreshes every 24h
  - opensanctions.py — OpenSanctions API client (multi-list screening)
  - risk.py — Risk scoring engine (0-100): sanctions check → high-risk
  patterns → amount thresholds → chain risk
  - travel_rule.py — FATF R16 compliance with 30+ jurisdictions, self-hosted
   wallet detection, uses stricter threshold when cross-border
  - wallet.py — Ethereum signature verification (EIP-191)
  - email.py — Welcome emails via Resend

  Database Models (db/models.py)

  7 tables: Business, APIKey, Transaction, AuditRecord, WalletVerification,
  TravelRuleProof, User, RateLimitBucket

  Core (core/)

  - Auth: Dual-path — API key auth (hashed SHA-256, scope-checked) for
  programmatic access + Clerk JWT for dashboard
  - Rate limiting: Token bucket algorithm per API key
  - Structured logging with request IDs and business ID context
  - Config: Settings dataclass loaded from env vars

  ---
  Frontend (Product/frontend/src/)

  A React SPA compliance dashboard with Clerk auth:
  - LoginPage.jsx — Clerk sign-in
  - StatsBar.jsx — Transaction metrics
  - Filters.jsx — Filter by status, risk level, date range
  - TransactionList.jsx — Transaction table
  - TransactionDetail.jsx — Audit record modal
  - lib/api.js — API client using Clerk JWT tokens

  ---
  Tests (Product/tests/)

  11 test files covering:
  - API endpoint tests (transactions, payments, reports, wallets, travel
  rule, misc)
  - Service unit tests (risk scoring, sanctions, travel rule)
  - Shared fixtures in conftest.py

  ---
  Current Status

  Working: API framework (15+ endpoints), Travel Rule engine (30+
  jurisdictions), real OFAC SDN screening, wallet verification, DB layer,
  rate limiting, audit trail + CSV export, React dashboard, self-serve
  signup with Tally integration, Clerk auth, Docker containerization.

  Known gaps: Sanctions screening uses OFAC-only in default mode
  (OpenSanctions requires API key), no CI/CD, no production deployment, no
  SOC 2 controls.

  The fundamental gap: Radius is entirely pull-based.
  Someone must call POST /v1/transactions/ingest for every
  transaction. There's no:
   1. Exchange/wallet connectors — No Coinbase, Circle, Fireblocks, or any
  other integration. You'd need OAuth flows + polling/webhook listeners for
  each provider's API to auto-discover transactions.
  2. Blockchain indexing — No on-chain monitoring. Radius can't watch a
  wallet address and detect transactions autonomously. You'd need something
  like an Alchemy/QuickNode webhook or a custom indexer.
  3. Credential storage for third-party APIs — No way to securely store a
  user's Coinbase API key or OAuth token and poll on their behalf.
  4. Background job infrastructure — No task queue (Celery, etc.) for
  periodic polling, retry logic, or async processing.
  5. Reconciliation engine — The annotate endpoint exists but there's no
  automatic matching of on-chain txs to previously ingested records.