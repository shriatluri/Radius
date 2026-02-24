# Gaps

Tracking what's stubbed, missing, or incomplete in the current implementation.

---

## Risk & Compliance

### Risk Scoring (stub)
- Current: Returns random score based on amount/chain
- Needed: Real blockchain analysis via provider (Chainalysis, TRM, Elliptic)
- Or: Mock wallet history database for demo purposes

### Sanctions Screening ✅ DONE
- Checks wallets against local blocklist (app/sanctions.py)
- Includes real OFAC-sanctioned addresses (Tornado Cash, Lazarus Group, Garantex)
- Returns `sanctions_result: "failed"` and blocks transaction
- High-risk wallet pattern detection (mixers, etc.)

### AML Checks (missing)
- Velocity checks: Flag unusual payout frequency per wallet
- Geographic risk: Flag wallets linked to high-risk jurisdictions
- Pattern detection: Structuring, smurfing, round-trip detection

### Wallet Risk Analysis (missing)
- No blockchain history scanning
- Should flag: mixers (Tornado Cash), known hacks, high-risk exchanges, gambling

---

## Identity & Verification

### Wallet Verification ✅ DONE
- Uses eth-account to recover signer from signature
- Message format: `radius-verify:{entity_id}:{YYYY-MM-DD}`
- Messages expire after 7 days
- Verifications stored with 90-day expiry
- Rejects if recovered address doesn't match claimed wallet

### KYC/KYB Binding (missing)
- No link between wallet verification and actual KYC provider
- Should integrate: Persona, Jumio, or accept external KYC status

### Counterparty Attestation (missing)
- No way to verify the receiving entity's identity
- Needed for Travel Rule compliance with unknown counterparties

---

## Travel Rule

### Travel Rule Transmission (stub)
- Current: Stores payload locally, returns "sent"
- Needed: Actually transmit to counterparty VASP
- Integrate: Notabene, Sygna, or TRISA protocol

### Travel Rule Threshold Logic ✅ DONE
- Jurisdiction-based threshold checking for 24+ countries
- US: $3,000 threshold (FinCEN BSA)
- EU: €0 threshold (TFR 2023/1113 - all transactions)
- UK: £1,000 threshold
- Singapore: SGD 1,500 threshold
- Self-hosted wallet verification for EU/UK/CH >€1,000
- Cross-border uses stricter jurisdiction rules
- Returns required_actions and data field requirements

---

## Reporting & Export

### CSV Export ✅ DONE
- Generates real CSV from audit records
- Supports date range filtering (from_date, to_date)
- Supports business_id filtering
- Also supports JSON export format
- Includes: transaction_id, business_id, entities, wallets, amount, asset, purpose, risk_score, risk_level, sanctions_result, travel_rule_status, tx_hash, timestamp, reconciliation_status

### ERP Integration (not started)
- NetSuite, QuickBooks, SAP connectors
- Auto journal entry creation
- Reconciliation sync

### Dashboard (not started)
- Alerts view
- Case management
- Approval workflows
- Audit export UI

---

## Data & Storage

### Persistence ✅ DONE
- SQLAlchemy ORM with PostgreSQL support
- SQLite fallback for local development (zero config)
- 6 tables: transactions, audit_records, wallet_verifications, travel_rule_proofs, api_keys, rate_limit_buckets
- Repository pattern for clean data access
- Data survives server restarts

### Idempotency (partial)
- Transaction ingest has external_id dedup
- Other endpoints lack idempotency keys

---

## Infrastructure

### Authentication ✅ DONE
- X-API-Key header required on all endpoints (except /v1/health)
- API keys mapped to business_id with scopes
- Mock keys: `sk_test_acme_123456`, `sk_test_globex_789012`, `sk_test_demo_000000`

### Rate Limiting (missing)
- No protection against abuse

### Webhooks (missing)
- No way to notify clients of status changes
- Needed: Risk score updates, Travel Rule responses

### Multi-tenancy (missing)
- No isolation between businesses
- Need: Scoped data access per business_id

---

## Testing

### Integration Tests (missing)
- Only have manual test script
- Need: pytest suite with fixtures

### Provider Mocks (missing)
- No way to simulate different risk provider responses
- Need: Configurable mock mode for demos

---

## Priority for MVP

High:
- [x] Real CSV export
- [x] Mock sanctions blocklist
- [x] Basic API authentication

Medium:
- [x] Wallet signature verification
- [x] Travel Rule threshold logic
- [x] PostgreSQL persistence

Low (post-MVP):
- [ ] ERP integrations
- [ ] Dashboard
- [ ] Webhook notifications
