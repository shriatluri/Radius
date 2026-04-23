# getradius

Python SDK for [Radius](https://getradius.com) — payment attestation infrastructure for stablecoin transfers.

Turn every stablecoin transaction into an audit-ready financial record.

## Install

```bash
pip install getradius
```

## Quick Start

```python
from getradius import RadiusClient, Entity

client = RadiusClient(api_key="sk_live_...")

# 1. Ingest a transaction for compliance checking
result = client.transactions.ingest(
    direction="outbound",
    from_entity=Entity(type="business", entity_id="acme"),
    to_entity=Entity(type="user", entity_id="bob", wallet="0x1234..."),
    amount="100.00",
    asset="USDC",
    chain="ethereum",
)
print(result.status, result.risk_level, result.sanctions_result)

# 2. Annotate with on-chain data after execution
client.payments.annotate(
    transaction_id=result.transaction_id,
    tx_hash="0xabc...",
    executed_at="2026-04-23T12:00:00Z",
)

# 3. Retrieve the audit record
audit = client.transactions.get_audit(result.transaction_id)
print(audit.reconciliation_status)  # "matched"
```

## Configuration

```python
client = RadiusClient(
    api_key="sk_live_...",
    base_url="http://localhost:8000",  # default: https://api.getradius.com
    timeout=30.0,                     # request timeout in seconds
)
```

## All Methods

### Transactions

```python
# Ingest a transaction for compliance checking
result = client.transactions.ingest(
    direction="outbound",           # "outbound" | "inbound"
    from_entity=Entity(type="business", entity_id="acme"),
    to_entity=Entity(type="user", entity_id="bob", wallet="0x..."),
    amount="100.00",
    asset="USDC",
    chain="ethereum",
    purpose="contractor_payout",    # optional
    external_id="inv_123",          # optional, for idempotency
    metadata={"invoice": "INV-42"}, # optional
)
# Returns: IngestResponse with transaction_id, status, risk_score, risk_level,
#          sanctions_result, travel_rule, required_actions, audit_record_id

# List transactions
page = client.transactions.list(status="pending", risk_level="low", limit=50, offset=0)
# Returns: TransactionListResponse with transactions[], total, limit, offset

# Get audit record
audit = client.transactions.get_audit("txn_abc123")
# Returns: AuditRecord with full compliance details
```

### Payments

```python
# Annotate a transaction with on-chain execution data
resp = client.payments.annotate(
    transaction_id="txn_abc123",
    tx_hash="0xabc...",
    executed_at="2026-04-23T12:00:00Z",
    provider_refs={"circle": "ref_123"},  # optional
)
# Returns: AnnotateResponse with transaction_id, status, audit_record_id
```

### Wallets

```python
# Verify wallet ownership via signed message
resp = client.wallets.verify(
    wallet="0x1234...",
    entity_type="user",
    entity_id="bob",
    proof_message="radius-verify:bob:2026-04-23",
    proof_signature="0xsig...",
)
# Returns: WalletVerifyResponse with wallet_id, verification_status
```

### Travel Rule

```python
# Pre-flight check
check = client.travel_rule.check(
    amount="5000",
    originator_jurisdiction="US",
    beneficiary_jurisdiction="DE",
)
# Returns: TravelRuleCheckResponse with status, threshold_exceeded, required_actions

# Transmit Travel Rule data
resp = client.travel_rule.transmit(
    transaction_id="txn_abc123",
    originator={"name": "Acme Inc", "account": "..."},
    beneficiary={"name": "Bob", "account": "..."},
    beneficiary_vasp={"name": "VASP Co", "lei": "..."},
)
# Returns: TravelRuleTransmitResponse with travel_rule_status, proof_id

# List supported jurisdictions
data = client.travel_rule.jurisdictions()
```

### Reports

```python
# Export as typed JSON
report = client.reports.export_json(from_date="2026-01-01", to_date="2026-04-01")
print(report.count, report.records)

# Export as raw CSV bytes
csv_bytes = client.reports.export_csv(from_date="2026-01-01")
with open("audit.csv", "wb") as f:
    f.write(csv_bytes)
```

### Health

```python
health = client.health()
print(health.status, health.version)
```

## Error Handling

All API errors raise typed exceptions:

```python
from getradius import (
    RadiusError,        # base class
    BadRequestError,    # 400
    AuthenticationError,# 401
    ForbiddenError,     # 403
    NotFoundError,      # 404
    RateLimitError,     # 429
    ServerError,        # 5xx
)

try:
    client.transactions.get_audit("txn_nonexistent")
except NotFoundError as e:
    print(e.code, e.message, e.status_code)
except RadiusError as e:
    print(f"API error: {e}")
```

`RateLimitError` includes a `retry_after` attribute with the server's suggested wait time.

## License

MIT
