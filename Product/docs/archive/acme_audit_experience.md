# Acme Corp Audit Experience - Radius Compliance Dashboard

## Overview

This document explains the compliance audit experience from Acme Corp's perspective when using the Radius platform to prepare for financial audits.

---

## The Audit Challenge

When Acme Corp uses stablecoins for payments (payroll, vendor payments, contractor payouts), they face annual audits where they must demonstrate:

1. **Transaction Compliance**: Every payment was screened for sanctions/AML risks
2. **Risk Management**: High-risk transactions were appropriately flagged and reviewed
3. **Regulatory Compliance**: Travel Rule requirements were met for applicable transactions
4. **Reconciliation**: On-chain transactions match internal records
5. **Complete Audit Trail**: Who authorized what, when, and why

Without Radius, this requires:
- Manual tracking of every transaction
- Spreadsheet hell (dozens of CSV exports from multiple systems)
- Weeks of preparation time
- Risk of missing transactions or incomplete documentation

---

## How Radius Solves This

### 1. Automatic Multi-Tenancy (Data Isolation)

**What it means:**
- Each Radius customer (Acme, GlobalCorp, etc.) has their own `business_id`
- API keys are automatically linked to a specific business
- When Acme logs in, they ONLY see their transactions - never anyone else's

**Implementation:**
```
API Key: sk_test_acme_123456
    ↓
Automatically scoped to: business_id = "acme_corp"
    ↓
All API calls filter by business_id = "acme_corp"
```

**Security:**
- Even if Acme tries to request another business's data, they get 404
- The business_id is extracted from the authenticated API key
- No way to see or modify other customers' data

### 2. The Dashboard Experience

When Acme's compliance team opens the dashboard:

#### **Header**
```
┌────────────────────────────────────────────────────┐
│  Acme Corp                      Powered by         │
│  Compliance Audit Dashboard        Radius          │
└────────────────────────────────────────────────────┘
```

Shows:
- Company name (Acme Corp)
- Purpose (Audit Dashboard, not generic "transactions")
- Branding (powered by Radius)

#### **Summary Metrics** (Audit-Focused Stats)

```
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│ Total Txns      │ Compliance Rate │ Sanctions Screen│ Flagged         │
│ 61              │ 49.2%          │ 100%            │ 15              │
│ $732,450 volume │ 30 approved     │ 61/61 cleared   │ 15 pending/block│
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

What this tells an auditor:
- **Total Transactions**: Complete count of all payments
- **Compliance Rate**: % of transactions that passed all checks
- **Sanctions Screening**: 100% coverage proves every payment was screened
- **Flagged for Review**: Transactions needing manual review (good governance)

#### **Filters** (Audit Query Tools)

```
┌────────────────────────────────────────────────────────────────────┐
│ Compliance Status: [All Transactions ▼]                            │
│ Risk Level:        [All Risk Levels ▼]                             │
│ From Date:         [2024-01-01]                                    │
│ To Date:           [2024-12-31]                                    │
│                                    [Export Audit Report] [Logout]  │
└────────────────────────────────────────────────────────────────────┘
```

**For auditors, this means:**
- "Show me all blocked transactions in Q4 2024"
- "Show me all high-risk payments this fiscal year"
- "Export everything from January to March for the auditor"

**Note:** No business_id filter - Acme only sees their data automatically

#### **Transaction Table** (Audit Record View)

| Date | Transaction ID | Amount | Asset | Risk | Sanctions | Status |
|------|---------------|--------|-------|------|-----------|---------|
| Jan 15, 2024 | `txn_abc123` | $5,000 | USDC | **LOW** | ✓ Clear | APPROVED |
| Jan 20, 2024 | `txn_def456` | $25,000 | USDT | **HIGH** | ✓ Clear | PENDING |
| Jan 22, 2024 | `txn_ghi789` | $50,000 | USDC | **CRITICAL** | ⚠ Flagged | BLOCKED |

**Audit-friendly features:**
- Date first (chronological audit trail)
- Risk level highlighted (critical = bold red)
- Sanctions result with visual indicators (✓ ⚠ ✕)
- Compliance status clearly shown

**Click any row** → Opens detailed audit record modal

#### **Audit Record Modal** (Complete Compliance Documentation)

```
┌─────────────────────────────────────────────────────────────┐
│  Transaction Audit Record                             [X]   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  BASIC INFORMATION                                           │
│  Transaction ID:  txn_abc123                                 │
│  Amount:          $5,000.00                                  │
│  Asset:           USDC                                       │
│  Purpose:         Contractor payment                         │
│  Created:         2024-01-15 10:30:00 UTC                    │
│                                                              │
│  ENTITIES                                                    │
│  From Entity:     Acme Corporation                           │
│  From Wallet:     0x742d35Cc6634C0532925a3b844Bc454e4438f44e│
│  To Entity:       Alice Smith                                │
│  To Wallet:       0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199│
│                                                              │
│  COMPLIANCE                                                  │
│  Risk Score:      15                                         │
│  Risk Level:      low                                        │
│  Sanctions:       clear                                      │
│  Travel Rule:     compliant                                  │
│  Status:          approved                                   │
│                                                              │
│  BLOCKCHAIN                                                  │
│  TX Hash:         0xabc...def123                             │
│                                                              │
│  APPROVALS                                                   │
│  - Policy: approved (rule_low_risk_auto)                     │
│                                                              │
│  RECONCILIATION                                              │
│  Status:          matched                                    │
│                                                              │
│                               [Close]                        │
└─────────────────────────────────────────────────────────────┘
```

**What this provides:**
- **Complete documentation** for a single transaction
- **Compliance proof**: All checks passed, risk assessed, approved
- **Blockchain proof**: On-chain transaction hash
- **Approval trail**: Who/what approved it (policy engine, manual review, etc.)
- **Reconciliation**: Confirms on-chain tx matches internal records

### 3. CSV Export for Auditors

**Button:** "Export Audit Report"

**What it does:**
1. Generates CSV with all filtered transactions
2. Includes ALL compliance fields
3. Filename: `acme_corp_compliance_audit_2024-01-01_to_2024-12-31.csv`

**CSV Format** (optimized for accountants/auditors):

```csv
timestamp,transaction_id,from_entity,to_entity,amount,asset,purpose,risk_score,risk_level,sanctions_result,travel_rule_status,reconciliation_status,from_wallet,to_wallet,tx_hash,business_id
2024-01-15T10:30:00Z,txn_abc123,Acme Corporation,Alice Smith,5000.00,USDC,Contractor payment,15,low,clear,compliant,matched,0x742d35...,0x8626f6...,0xabc...def123,acme_corp
2024-01-20T14:20:00Z,txn_def456,Acme Corporation,Bob Johnson,25000.00,USDT,Vendor payment,65,high,clear,compliant,matched,0x742d35...,0xdAC17F...,0x123...abc456,acme_corp
```

**Why this matters for audits:**
- **Import into Excel/Google Sheets** for analysis
- **Pivot tables**: Group by risk level, sanctions result, date
- **Proof of coverage**: Every payment has compliance data
- **Paper trail**: Can be printed and filed

---

## Real-World Audit Scenario

### Scenario: Acme's 2024 Annual Audit

**Auditor asks:** "How do you ensure all stablecoin payments comply with OFAC sanctions and AML regulations?"

**Without Radius:**
- "We... have a process where we manually check wallets"
- "Here's a spreadsheet we maintain"
- Auditor finds missing data, incomplete records
- **Result**: Qualified opinion or audit finding

**With Radius:**
1. **Log into dashboard** with API key
2. **Set date range**: January 1, 2024 - December 31, 2024
3. **View summary**:
   - 100% sanctions screening coverage
   - 98% compliance rate
   - 12 high-risk transactions, all reviewed
4. **Export full audit report**: `acme_corp_compliance_audit_2024-01-01_to_2024-12-31.csv`
5. **Hand to auditor**

**Auditor sees:**
- Every transaction screened ✓
- Risk scores documented ✓
- High-risk items flagged and reviewed ✓
- On-chain proof (tx hashes) ✓
- Complete audit trail ✓

**Result**: Clean audit opinion

---

## What Acme Controls vs. What Radius Provides

### Acme Controls (Their Inputs):

When Acme makes a payment through their system:

```javascript
// Acme's payment system calls Radius API
POST /v1/transactions/ingest
{
  "from_wallet": "0x742d35...",     // Acme's wallet
  "to_wallet": "0x8626f6...",       // Contractor's wallet
  "amount": "5000.00",              // How much
  "asset": "USDC",                  // Which stablecoin
  "purpose": "March 2024 payroll",  // Why (optional)
  "to_entity": "Alice Smith"        // Who (optional)
}
```

Acme decides:
- **Who** to pay (recipient wallet, entity name)
- **How much** ($5,000)
- **What asset** (USDC, USDT, DAI, etc.)
- **Why** (payroll, vendor payment, etc.)

### Radius Provides (Automatic Enrichment):

Radius automatically adds compliance data:

```json
{
  "transaction_id": "txn_abc123",
  "status": "approved",              // ← Radius decision
  "risk_score": 15,                  // ← Radius calculation
  "risk_level": "low",               // ← Radius assessment
  "sanctions_result": "clear",       // ← Radius screening
  "travel_rule_status": "compliant", // ← Radius compliance check
  "created_at": "2024-01-15T10:30:00Z"
}
```

Radius provides:
- **Risk scoring**: Analyzes wallet behavior, transaction patterns
- **Sanctions screening**: Checks against OFAC, EU sanctions lists
- **Travel Rule compliance**: Determines if originator/beneficiary data transmission required
- **Approval workflow**: Auto-approves low risk, flags high risk for review
- **Audit trail**: Immutable record with timestamp, approvals

### Combined Result:

Acme's payment intent + Radius compliance = Complete audit-ready record

---

## Multi-Tenancy Security

### How it works:

1. **Sign Up**:
   - Acme Corp signs up for Radius
   - Gets API key: `sk_test_acme_123456`
   - This key is linked to `business_id = "acme_corp"`

2. **Every API Call**:
   - Header: `X-API-Key: sk_test_acme_123456`
   - Radius extracts: `business_id = "acme_corp"`
   - All queries automatically filter: `WHERE business_id = 'acme_corp'`

3. **Data Isolation**:
   - Acme CANNOT see GlobalCorp's transactions
   - GlobalCorp CANNOT see Acme's transactions
   - Even if Acme tries to hack the API, they get 404 (not found)

4. **Dashboard View**:
   - No business_id selector
   - No way to "switch" businesses
   - Only shows your data, automatically

### Database Structure:

```
transactions table:
┌────────────────┬──────────────┬────────┬───────┐
│ transaction_id │ business_id  │ amount │ ...   │
├────────────────┼──────────────┼────────┼───────┤
│ txn_001        │ acme_corp    │ 5000   │ ...   │  ← Acme sees this
│ txn_002        │ globalcorp   │ 3000   │ ...   │  ← Acme CANNOT see
│ txn_003        │ acme_corp    │ 7500   │ ...   │  ← Acme sees this
│ txn_004        │ techstartup  │ 2000   │ ...   │  ← Acme CANNOT see
└────────────────┴──────────────┴────────┴───────┘
```

When Acme queries: `SELECT * FROM transactions WHERE business_id = 'acme_corp'`
- Returns: txn_001, txn_003
- Never returns: txn_002, txn_004

---

## Benefits for Acme's Audit Preparation

### Time Savings:
- **Before**: 2-3 weeks compiling transaction records
- **After**: 5 minutes to export complete audit report

### Completeness:
- **Before**: Risk of missing transactions, incomplete data
- **After**: 100% coverage, every transaction documented

### Auditor Confidence:
- **Before**: "Let me verify your manual process..."
- **After**: "This is a comprehensive compliance system, looks good"

### Regulatory Confidence:
- **Before**: Hope we're compliant, fingers crossed
- **After**: Know we're compliant, have proof

### Cost Savings:
- Fewer compliance staff hours
- Faster audit completion (lower audit fees)
- Reduced risk of audit findings/penalties

---

## Demo Walkthrough

### Step 1: Login

1. Open http://localhost:8000
2. Enter API key: `sk_test_acme_123456`
3. Click "Continue"

You now see:
- "Acme Corp - Compliance Audit Dashboard"
- Only Acme's 61 transactions (not the full 61 from all businesses)

### Step 2: Review Summary

Top cards show:
- **Total Transactions**: How many payments Acme made
- **Compliance Rate**: % that passed all checks
- **Sanctions Screening**: 100% coverage
- **Flagged for Review**: Items needing attention

### Step 3: Filter Transactions

Try:
- **Status**: "Blocked/Flagged" - See problematic transactions
- **Risk Level**: "High Risk" - See transactions that needed extra review
- **Date Range**: Pick Q4 2023 - See last quarter's payments

### Step 4: Investigate a Transaction

Click any row to see:
- Full payment details
- Compliance assessment (risk, sanctions, travel rule)
- Blockchain proof (tx hash)
- Approval trail
- Reconciliation status

### Step 5: Export for Auditor

1. Set filters for the audit period (e.g., "2024-01-01" to "2024-12-31")
2. Click "Export Audit Report"
3. Receive: `acme_corp_compliance_audit_2024-01-01_to_2024-12-31.csv`
4. Send to auditor

Done! Complete audit trail in 5 minutes.

---

## Technical Implementation Summary

### Backend Changes:
1. ✅ API keys linked to business_id (`sk_test_acme_123456` → `acme_corp`)
2. ✅ All endpoints filter by authenticated business_id
3. ✅ Security checks prevent cross-business data access
4. ✅ CSV export includes all compliance fields, audit-friendly filename

### Frontend Changes:
1. ✅ Removed business_id filter (not needed, auto-scoped)
2. ✅ Added date range filtering
3. ✅ Audit-focused labels ("Compliance Status" not "Status")
4. ✅ Summary metrics for auditors (compliance rate, sanctions coverage)
5. ✅ Company branding (shows "Acme Corp")
6. ✅ Improved transaction table (date first, better column labels)
7. ✅ Export button labeled "Export Audit Report"

### Result:
- Production-ready multi-tenant compliance dashboard
- Audit-focused UX designed for compliance teams
- Complete data isolation between businesses
- One-click audit report generation

---

## Conclusion

Radius transforms stablecoin payments from "operationally unusable" to "audit-ready by default."

For Acme Corp, this means:
- Make stablecoin payments with confidence
- Know every payment is compliant
- Prepare for audits in minutes, not weeks
- Have complete documentation for regulators

The dashboard provides exactly what compliance teams and auditors need:
- Complete transaction history
- Risk assessment for every payment
- Sanctions screening proof
- One-click export for audit review

**Next time an auditor asks "How do you ensure compliance?"**
**Acme's answer:** "We use Radius. Here's the report."
