# @getradius/sdk

TypeScript SDK for [Radius](https://getradius.com) — payment attestation infrastructure for stablecoin transfers.

Turn every stablecoin transaction into an audit-ready financial record.

## Install

```bash
npm install @getradius/sdk
```

## Quick Start

```typescript
import { RadiusClient, type Entity } from "@getradius/sdk";

const client = new RadiusClient({ apiKey: "sk_live_..." });

// 1. Ingest a transaction for compliance checking
const result = await client.transactions.ingest({
  direction: "outbound",
  from_entity: { type: "business", entity_id: "acme" },
  to_entity: { type: "user", entity_id: "bob", wallet: "0x1234..." },
  amount: "100.00",
  asset: "USDC",
  chain: "ethereum",
});
console.log(result.status, result.risk_level, result.sanctions_result);

// 2. Annotate with on-chain data after execution
await client.payments.annotate({
  transaction_id: result.transaction_id,
  tx_hash: "0xabc...",
  executed_at: "2026-04-23T12:00:00Z",
});

// 3. Retrieve the audit record
const audit = await client.transactions.getAudit(result.transaction_id);
console.log(audit.reconciliation_status); // "matched"
```

## Configuration

```typescript
const client = new RadiusClient({
  apiKey: "sk_live_...",
  baseUrl: "http://localhost:8000", // default: https://api.getradius.com
  timeout: 30_000,                 // request timeout in ms
});
```

## All Methods

### Transactions

```typescript
// Ingest a transaction for compliance checking
const result = await client.transactions.ingest({
  direction: "outbound",           // "outbound" | "inbound"
  from_entity: { type: "business", entity_id: "acme" },
  to_entity: { type: "user", entity_id: "bob", wallet: "0x..." },
  amount: "100.00",
  asset: "USDC",
  chain: "ethereum",
  purpose: "contractor_payout",    // optional
  external_id: "inv_123",          // optional, for idempotency
  metadata: { invoice: "INV-42" }, // optional
});
// Returns: IngestResponse

// List transactions
const page = await client.transactions.list({
  status: "pending",
  risk_level: "low",
  limit: 50,
  offset: 0,
});
// Returns: TransactionListResponse

// Get audit record
const audit = await client.transactions.getAudit("txn_abc123");
// Returns: AuditRecord
```

### Payments

```typescript
// Annotate a transaction with on-chain execution data
const resp = await client.payments.annotate({
  transaction_id: "txn_abc123",
  tx_hash: "0xabc...",
  executed_at: "2026-04-23T12:00:00Z",
  provider_refs: { circle: "ref_123" }, // optional
});
// Returns: AnnotateResponse
```

### Wallets

```typescript
// Verify wallet ownership via signed message
const resp = await client.wallets.verify({
  wallet: "0x1234...",
  entity_type: "user",
  entity_id: "bob",
  proof_message: "radius-verify:bob:2026-04-23",
  proof_signature: "0xsig...",
});
// Returns: WalletVerifyResponse
```

### Travel Rule

```typescript
// Pre-flight check
const check = await client.travelRule.check({
  amount: "5000",
  originator_jurisdiction: "US",
  beneficiary_jurisdiction: "DE",
});
// Returns: TravelRuleCheckResponse

// Transmit Travel Rule data
const resp = await client.travelRule.transmit({
  transaction_id: "txn_abc123",
  originator: { name: "Acme Inc", account: "..." },
  beneficiary: { name: "Bob", account: "..." },
  beneficiary_vasp: { name: "VASP Co", lei: "..." },
});
// Returns: TravelRuleTransmitResponse

// List supported jurisdictions
const data = await client.travelRule.jurisdictions();
```

### Reports

```typescript
// Export as typed JSON
const report = await client.reports.exportJson({
  from_date: "2026-01-01",
  to_date: "2026-04-01",
});
console.log(report.count, report.records);

// Export as raw CSV
const csvBuffer = await client.reports.exportCsv({ from_date: "2026-01-01" });
// csvBuffer is an ArrayBuffer — write to file or process as needed
```

### Health

```typescript
const health = await client.health();
console.log(health.status, health.version);
```

## Error Handling

All API errors throw typed exceptions:

```typescript
import {
  RadiusError,        // base class
  BadRequestError,    // 400
  AuthenticationError,// 401
  ForbiddenError,     // 403
  NotFoundError,      // 404
  RateLimitError,     // 429
  ServerError,        // 5xx
} from "@getradius/sdk";

try {
  await client.transactions.getAudit("txn_nonexistent");
} catch (e) {
  if (e instanceof NotFoundError) {
    console.log(e.code, e.message, e.statusCode);
  } else if (e instanceof RateLimitError) {
    console.log("Retry after:", e.retryAfter);
  } else if (e instanceof RadiusError) {
    console.log("API error:", e);
  }
}
```

## Requirements

- Node.js >= 18 (uses native `fetch`)
- Zero runtime dependencies

## License

MIT
