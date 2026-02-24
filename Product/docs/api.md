# API Spec (MVP)

## Overview

Radius is a **payment attestation infrastructure** for stablecoin transfers. Before you send a payment, Radius creates a structured, audit-ready record that includes sanctions screening, risk assessment, and regulatory compliance checks.

**The record is the product. Enforcement is a feature.**

This spec describes the minimal endpoints required to turn stablecoin transfers into explainable financial events. The API is designed to be:
- opinionated and simple to integrate
- provider-agnostic (risk/KYT via external vendors)
- audit-first (every decision leaves a structured trail)

All endpoints are versioned under `/v1`.

## Conventions

- `id` values are opaque strings (e.g. `txn_123`).
- Timestamps are ISO-8601 UTC strings (e.g. `2026-02-06T21:41:00Z`).
- Amounts are decimal strings to avoid float errors.
- `risk_score` is a numeric 0-100.
- `risk_level` is one of: `low`, `medium`, `high`, `critical`.

## 1. Ingest Transaction

Create or update a transaction record. This is called when a payout is requested or when an on-chain transfer is detected.

`POST /v1/transactions/ingest`

Request:
```json
{
  "external_id": "payout_987",
  "direction": "outbound",
  "business_id": "biz_123",
  "from_entity": {
    "type": "business",
    "entity_id": "biz_123",
    "wallet": "0xaaa..."
  },
  "to_entity": {
    "type": "user",
    "entity_id": "u_456",
    "wallet": "0xbbb..."
  },
  "amount": "50.00",
  "asset": "USDC",
  "chain": "ethereum",
  "purpose": "contractor_payout",
  "metadata": {
    "country": "US",
    "invoice_id": "inv_1001"
  }
}
```

Response:
```json
{
  "transaction_id": "txn_123",
  "status": "pending",
  "risk_score": 12,
  "risk_level": "low",
  "sanctions_result": "passed",
  "required_actions": [],
  "audit_record_id": "aud_456"
}
```

## 2. Verify Wallet

Bind a wallet to a verified person or business.

`POST /v1/wallets/verify`

Request:
```json
{
  "wallet": "0xbbb...",
  "entity_type": "user",
  "entity_id": "u_456",
  "proof": {
    "type": "signed_message",
    "message": "radius-verify:u_456:2026-02-06",
    "signature": "0x123..."
  }
}
```

Response:
```json
{
  "wallet_id": "wal_789",
  "verification_status": "verified",
  "verified_at": "2026-02-06T21:41:00Z"
}
```

## 3. Annotate Payment

Attach compliance metadata after a transfer executes (e.g., tx hash).

`POST /v1/payments/annotate`

Request:
```json
{
  "transaction_id": "txn_123",
  "tx_hash": "0x999...",
  "executed_at": "2026-02-06T21:41:00Z",
  "provider_refs": {
    "custodian": "fireblocks",
    "custodian_tx_id": "fb_001"
  }
}
```

Response:
```json
{
  "transaction_id": "txn_123",
  "status": "completed",
  "audit_record_id": "aud_456"
}
```

## 4. Fetch Audit Record

`GET /v1/transactions/{id}/audit`

Response:
```json
{
  "transaction_id": "txn_123",
  "business_id": "biz_123",
  "from_entity": "biz_123",
  "to_entity": "u_456",
  "wallets": {
    "from": "0xaaa...",
    "to": "0xbbb..."
  },
  "amount": "50.00",
  "asset": "USDC",
  "purpose": "contractor_payout",
  "risk_score": 12,
  "risk_level": "low",
  "sanctions_result": "passed",
  "travel_rule_status": "not_required",
  "tx_hash": "0x999...",
  "timestamp": "2026-02-06T21:41:00Z",
  "approvals": [
    {
      "type": "policy",
      "result": "approved",
      "rule_id": "rule_low_risk_auto"
    }
  ],
  "reconciliation_status": "matched"
}
```

## 5. Export Report

`GET /v1/reports/export?format=csv&from=2026-02-01&to=2026-02-06`

Response:
```json
{
  "report_id": "rep_321",
  "status": "ready",
  "download_url": "https://example.com/reports/rep_321.csv",
  "expires_at": "2026-02-07T00:00:00Z"
}
```

## 6. Travel Rule Transmit

`POST /v1/travel-rule/transmit`

Request:
```json
{
  "transaction_id": "txn_123",
  "originator": {
    "name": "Acme Inc",
    "country": "US",
    "identifier": "biz_123"
  },
  "beneficiary": {
    "name": "John Doe",
    "country": "US",
    "identifier": "u_456"
  },
  "beneficiary_vasp": {
    "name": "ExampleVASP",
    "vasp_id": "vasp_999"
  }
}
```

Response:
```json
{
  "transaction_id": "txn_123",
  "travel_rule_status": "sent",
  "proof_id": "trp_555"
}
```
