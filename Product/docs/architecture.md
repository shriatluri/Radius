# Architecture (MVP)

## Core Concept

Radius is a **payment attestation engine** that converts blockchain transfers into explainable financial events.

Companies fail not because they cannot send stablecoin payments — they fail because they cannot explain them later. When accounting needs to close books, when banks ask source-of-funds questions, when investors request payment controls, or when expanding to new jurisdictions, the payment history must be more than a collection of transaction hashes.

**Radius creates a structured, permanent record at send-time.**

The key principle: **Radius never moves funds. It only observes, verifies, and records.**

## High-Level Flow

Business App
  ->
Radius SDK/API (Payment Attestation)
  ->
Compliance Engine (Sanctions + Risk + Travel Rule)
  ->
Risk Provider + Chain Data

## Services

- Ingestion Service
  - Accepts transaction intents or on-chain transfers.
  - Normalizes fields into a canonical transaction shape.

- Risk Engine
  - Calls external KYT/AML/sanctions providers.
  - Produces `risk_score`, `risk_level`, and `sanctions_result`.

- Identity Service
  - Binds wallets to known entities.
  - Stores verification proofs and timestamps.

- Travel Rule Router
  - Packages originator/beneficiary metadata.
  - Sends to counterparty VASPs and stores proof.

- Ledger Normalizer
  - Ensures every transaction is represented in an audit-ready format.
  - Correlates with on-chain execution (tx hash).

- Reporting/Export Service
  - Generates CSV/API reports.
  - Supports accounting and audit workflows.

## End-to-End Example (How It Works)

1. A business requests a payout and calls:
   - `POST /v1/transactions/ingest`
2. Radius runs sanctions and AML checks and returns:
   - `risk_score`, `risk_level`, `sanctions_result`
3. If the payout is approved, the business executes the transfer externally.
4. After execution, the business posts:
   - `POST /v1/payments/annotate` (with `tx_hash`)
5. The audit team (or finance) retrieves the record:
   - `GET /v1/transactions/{id}/audit`
6. For reconciliation or audits, the business exports:
   - `GET /v1/reports/export`

This flow keeps Radius out of the money movement path while still creating an audit-ready record for every transfer.
