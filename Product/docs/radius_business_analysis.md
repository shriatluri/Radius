# Radius — Product & GTM Strategy

> **Date:** February 16, 2026
> **Stage:** Pre-seed / Prototype
> **Focus:** Product strategy, customer acquisition, and path to first revenue

---

## Executive Summary

Stablecoin companies fail not because they cannot send payments — they fail because they cannot explain them later.

When a company using stablecoins hits operational maturity (accounting close, bank review, fundraising diligence, international expansion), they face a painful reality: their payment history is a collection of blockchain hashes, not business records.

**Radius solves this by turning every stablecoin transfer into an audit-ready financial record at send-time.**

The regulatory environment (GENIUS Act, MiCA, FATF Travel Rule) creates urgency. The $33 trillion in annual stablecoin volume creates scale. The lack of self-serve compliance infrastructure creates opportunity.

Radius is a payment attestation engine — not just a compliance API. The record is the product. Screening is a feature of that record.

---

## 1. The Problem

### 1.1 The Operational Pain

Companies sending stablecoins today follow this workflow:

```
decide to pay → send via wallet → paste tx hash → spreadsheet
```

This works until they hit operational maturity:

| Trigger Event | What Breaks | Cost of Failure |
|---|---|---|
| **Accounting close** | CFO cannot reconcile stablecoin payments to business purpose | Books don't close, audit delayed |
| **Bank review** | Bank asks for source-of-funds documentation on crypto activity | Account frozen or closed |
| **Fundraising diligence** | Investors request payment controls and compliance program | Deal slows or dies |
| **International expansion** | New jurisdiction requires proof of Travel Rule compliance | Cannot operate legally |

The core problem: **blockchain transactions store movement of money, businesses must store intent of money.**

Reconstructing this history months later is expensive, sometimes impossible, and always painful.

### 1.2 The Regulatory Catalyst

The operational pain exists today. Regulation makes ignoring it existential:

| Regulation | Effective | Enforcement |
|---|---|---|
| **US GENIUS Act** | July 2025 | AML/sanctions obligations. Stablecoin issuers and platforms must screen transfers. |
| **EU MiCA** | January 2025 | Non-compliant stablecoins delisted from EU exchanges. |
| **FATF Travel Rule** | 85 of 117 jurisdictions | VASPs must collect and transmit sender/receiver identity data. |
| **OFAC Sanctions** | Ongoing | 1,245 designated crypto wallets (up 32% YoY). $1.8B in seized crypto (Q1 2025). |

**Recent enforcement actions:**

| Company | Fine | Violation |
|---|---|---|
| **Exodus** | $3.1M | 254 violations — provided services to users in Iran |
| **ShapeShift** | $750K | 17,000+ transactions with sanctioned jurisdictions. **Had no compliance program.** |
| **BitGo** | $98,830 | 183 violations — processed transactions for sanctioned jurisdictions |

> **Key insight:** ShapeShift wasn't fined for intentional misconduct — they were fined for having no systematic compliance checking. This is the exact situation most startups sending stablecoins face today.

### 1.3 Current Options (All Bad)

**Option A: Enterprise tools**
- Chainalysis ($50K-$500K/yr) + Notabene ($24K-$56K/yr) + custom audit trail code
- **Problem:** $75K-$550K/year is overkill for a startup doing 500-5,000 payouts/month

**Option B: Build it yourself**
- $500K-$1M upfront + 12-18 months + $750K/yr maintenance
- **Problem:** Most startups can't afford this and will get it wrong

**Option C: Ignore it**
- $0 upfront
- **Problem:** ShapeShift tried this. Cost them $750K. Exodus tried this. Cost them $3.1M.

**Radius is Option D:** One API, pay per transaction, set up in hours.

---

## 2. The Solution: Payment Attestation Infrastructure

### 2.1 Product Definition

Radius is not a payment processor. Radius is not a legal oracle.

**Radius is a payment attestation engine.**

Before sending funds:
```
company → Radius.check(payment)
```

Radius returns:
- Sanctions result (OFAC/EU/UN screening)
- Risk classification (0-100 score, low/medium/high/critical)
- Regulatory obligations (Travel Rule requirements)
- Structured metadata record (who, what, when, why, risk, compliance status)

After sending:
```
company → attach tx_hash to record
```

**Result:** Every transfer becomes a complete financial object, not just a blockchain event.

### 2.2 What Makes It Valuable

**Primary value:** Companies never reconstruct financial history again.
- Accountants get structured payment records, not tx hashes
- Banks get source-of-funds documentation on demand
- Investors get proof of payment controls
- Auditors get regulator-ready compliance records

**Secondary value:** Companies can block risky transactions when desired.

The record is the product. Enforcement is a feature.

### 2.3 What Radius Does NOT Do

- ❌ Does not hold, move, or custody funds
- ❌ Does not do KYC/identity verification (that's the business's job)
- ❌ Does not monitor blockchain in real-time
- ❌ Does not replace legal counsel

Radius is a compliance checkpoint, not a payment processor. This means no money transmitter license required, minimal PII handling, smaller regulatory surface area.

### 2.4 Technical Status

| Component | Status |
|---|---|
| API framework (FastAPI) | ✅ Production-ready (15+ endpoints, auth, rate limiting) |
| Risk scoring engine | ✅ Working (amount, chain, wallet pattern analysis) |
| Sanctions screening | ⚠️ Demo only (hardcoded addresses — needs real OFAC integration) |
| Travel Rule engine | ✅ Working (30+ jurisdictions, FATF R.16 compliant) |
| Audit trail + export | ✅ Working (CSV/JSON export, immutable records) |
| Tests | ❌ None (zero unit or integration tests) |
| Production infra | ❌ None (no Docker, CI/CD, monitoring) |

**Gap to production:** Real sanctions data + comprehensive tests + deployment infrastructure.

---

## 3. Market Validation

### 3.1 Stablecoin Volume

| Metric | Value | Source |
|---|---|---|
| **Total stablecoin volume (2025)** | **$33 trillion** (72% YoY growth) | Binance/KuCoin |
| **"Real" user payments** | $9 trillion (87% YoY growth) — **5x PayPal, >50% of Visa** | IndexBox 2025 |
| **B2B stablecoin payments** | $3B/month (30x increase in 2 years) | The Block |
| **Remittances via stablecoins** | 30% of global remittances | RiseWorks 2025 |

Every one of these transfers needs an audit trail. Every one is a potential Radius transaction.

### 3.2 Market Signal: Stripe Acquires Bridge for $1.1B

In February 2025, Stripe acquired Bridge (stablecoin payments API) for $1.1 billion.

Bridge handles the **payment rails**. Nobody is handling the **compliance rails** at the same tier.

The largest payments company in the world just validated developer-first stablecoin infrastructure. The compliance layer for those same payments doesn't exist yet at the SMB segment.

### 3.3 Market Size

```
TAM: Crypto Compliance & Blockchain Analytics
$2.9B (2025) → $14.6B (2032) | 26% CAGR

SAM: Stablecoin-Specific Compliance
~$500M-$800M
Companies sending stablecoins that need sanctions + Travel Rule + audit trail

SOM: Self-Serve SMB Segment (Year 1-2)
~$20M-$50M
Startups and mid-market fintechs priced out of enterprise tools
```

---

## 4. Customer Acquisition Strategy

### 4.1 Target Customer Profile

**Not regulated enterprises. Not crypto-native companies that already have compliance teams.**

Target: Companies crossing operational maturity threshold.

| Attribute | Description |
|---|---|
| **Stage** | Series A-B ($5M-$30M raised) |
| **Team size** | 10-50 employees, 5-15 engineers |
| **Stablecoin volume** | $1M-$20M/month in payments |
| **Compliance status** | Knows they need it, hasn't bought enterprise tools yet |
| **Decision maker** | CTO or Head of Engineering (no CISO yet) |
| **Geography** | US or EU (under GENIUS Act / MiCA pressure) |

### 4.2 Customer Personas & Acquisition Channels

**Persona 1: Stablecoin Payroll Platform**

| | |
|---|---|
| **Examples** | Rise, Deel, Bitwage, Remote, Toku, Papaya Global |
| **What they do** | Pay thousands of contractors globally in USDC/USDT |
| **Volume** | 1,000-50,000 payouts/month |
| **Current state** | Manual spot-checking or nothing |
| **Trigger event** | Board asks about compliance. Bank questions crypto activity. Fundraising diligence flags payment controls. |
| **Pain intensity** | 🔥🔥🔥 Every payout is unscreened sanctions risk. One bad payout = $3M Exodus-style fine. |
| **Willingness to pay** | $800-$4,000/month (trivial vs. $300K-$5M/month in payouts) |
| **Acquisition channel** | Direct outreach to CTOs. Content: "How to make USDC payroll GENIUS Act compliant in 30 minutes" |
| **Integration pattern** | API call before each payout disbursement |

**Persona 2: Cross-Border B2B Settlement**

| | |
|---|---|
| **Examples** | BVNK, MuralPay, Triple-A, Ivy |
| **What they do** | Settle B2B invoices in USDC across borders |
| **Volume** | 500-10,000 settlements/month |
| **Current state** | Chainalysis ($100K+/yr) or nothing |
| **Trigger event** | Expanding to EU (MiCA compliance required). Bank threatens account closure. Customer asks for Travel Rule compliance proof. |
| **Pain intensity** | 🔥🔥 Need Travel Rule compliance across multiple jurisdictions. Building in-house would cost $500K+ and 12-18 months. |
| **Willingness to pay** | $2,000-$8,000/month |
| **Acquisition channel** | Partnerships with Circle, Fireblocks (they know who's doing B2B volume). Content syndication in fintech newsletters. |
| **Integration pattern** | Travel Rule pre-check → ingest → transmit → annotate |

**Persona 3: Emerging Crypto On/Off Ramp**

| | |
|---|---|
| **Examples** | Smaller competitors to MoonPay, Ramp, Transak |
| **What they do** | Convert fiat ↔ stablecoin for end users |
| **Volume** | 1,000-20,000 conversions/month |
| **Current state** | Nothing (too small for Chainalysis pricing) |
| **Trigger event** | Hit volume threshold where manual screening breaks. Customer gets sanctioned address, causes incident. |
| **Pain intensity** | 🔥 Scaling compliance is blocking growth. |
| **Willingness to pay** | $500-$3,000/month |
| **Acquisition channel** | Developer communities (Ethereum Discord, DeFi forums). Free tier + open-source SDK. |
| **Integration pattern** | Wallet screening + sanctions check on every conversion |

### 4.3 Acquisition Strategy by Phase

**Phase 1: Developer Adoption (Months 1-3)**
**Goal:** 50 developers using free tier

- Open-source SDK (Python, TypeScript)
- Launch on Product Hunt, Hacker News
- Content: "GENIUS Act compliance for developers", "Travel Rule automation guide"
- Free tier: 100 checks/month, no credit card
- Target: Ethereum dev communities, crypto Twitter, DeFi Discord servers

**Phase 2: First Paying Customers (Months 3-6)**
**Goal:** 5-10 paying customers, $5K-$15K MRR

- Direct outreach to 20 target companies (CTOs at stablecoin payroll platforms)
- Offer: 90-day free pilot for first 5 integrations
- Build case study from first customer
- Begin SOC 2 Type I engagement
- Pricing: Start with $99-$499/month tiers

**Phase 3: Growth (Months 6-12)**
**Goal:** 50+ paying customers, $50K+ MRR

- SOC 2 Type I certification complete
- Travel Rule network partnerships (Notabene/TRP interop)
- Co-marketing partnerships (Bridge/Stripe, Circle, Fireblocks)
- Dedicated outbound sales for mid-market accounts ($2K-$10K/month)
- Content marketing: case studies, compliance guides, webinars

### 4.4 Why They'll Buy

Customers adopt Radius when they transition from **moving money** → **operating a financial system**.

The business is viable if Radius becomes part of the send flow, not a post-processing report.

**Key positioning:** "Financial attestation layer for programmable payments" (not just "stablecoin compliance API").

---

## 5. Competitive Position

### 5.1 Competitive Landscape

| Company | Focus | Pricing | Weakness |
|---|---|---|---|
| **Chainalysis** | Blockchain analytics, KYT | $50K-$500K/yr | Enterprise-only, sales-driven, overkill for SMBs |
| **TRM Labs** | Wallet screening | $25K-$100K/yr | Enterprise-only |
| **Elliptic** | Blockchain analytics | $30K-$200K/yr | Enterprise-only |
| **Notabene** | Travel Rule only | $24K-$56K/yr | Doesn't do sanctions or risk scoring |
| **Sardine** | Fraud + compliance | Usage-based | Focuses on fraud, not stablecoin-specific |
| **Sumsub** | KYC/AML + Travel Rule | Usage-based | Broad identity verification, not payment-specific |

### 5.2 Where Radius Fits

```
                  COVERAGE BREADTH
        Narrow (focused)  ──────  Wide (full stack)
      ┌────────────────────────────────────────┐
Enter │ Notabene        │ Chainalysis Elliptic│
prise │ (Travel Rule)   │ TRM Labs            │
>$50K │                 │                     │
      ├─────────────────┼─────────────────────┤
Mid   │                 │ Sardine   Sumsub    │
$10-  │                 │ (fraud + KYC)       │
$50K  │                 │                     │
      ├─────────────────┼─────────────────────┤
Self  │  ★ RADIUS ★     │                     │
-serve│  Stablecoin-    │     (nobody)        │
<$10K │  native:        │                     │
      │  sanctions +    │                     │
      │  Travel Rule +  │                     │
      │  risk + audit   │                     │
      └─────────────────┴─────────────────────┘
```

**Radius's wedge:** Only self-serve, all-in-one compliance API priced for SMB stablecoin companies.

**Compete on:**
- Ease of integration (one API call vs. assembling a stack)
- Price (10x cheaper than enterprise tools)
- Bundling (sanctions + Travel Rule + audit in one)

**Don't compete on:**
- Data depth (Chainalysis has 10 years of blockchain data)
- Brand (they have government contracts and Fortune 500 logos)

### 5.3 Moat Building

| Moat Type | Current | Path to Strengthen |
|---|---|---|
| **Network effects** | ❌ None | Travel Rule creates natural network — VASPs using Radius for data exchange create a network |
| **Switching costs** | 🟡 Low-medium | Once audit records are in Radius, migrating is painful. Compliance records are permanent. |
| **Data advantage** | ❌ None | Anonymized risk data from transaction screening builds proprietary risk model over time |
| **Regulatory moat** | 🟡 Medium | SOC 2 + audit-ready records = trust. Once approved by compliance officer, switching carries re-audit risk |
| **Developer ecosystem** | 🟡 Early | SDKs, plugins for Bridge/Fireblocks/Circle |

**Honest assessment:** No moat today. Moat builds through (1) Travel Rule network effects, (2) compliance record switching costs, (3) SOC 2 certification trust barrier.

---

## 6. Product Roadmap

### 6.1 90-Day Sprint to Production

**Weeks 1-2: Make It Real**

| Task | Why P0 |
|---|---|
| Integrate OFAC SDN list (Treasury.gov SLS API) | Without real sanctions data, the product claim is fake |
| Add comprehensive tests (>80% coverage) | A compliance product with zero tests is a liability |
| Dockerize application | Cannot deploy or demo without this |

**Weeks 3-4: Make It Deployable**

| Task | Why P0 |
|---|---|
| CI/CD (GitHub Actions) | Automated testing and deployment |
| Structured logging (JSON, request IDs) | Audit trail for compliance decisions |
| Deploy to cloud (Railway/Render/AWS) | Production PostgreSQL, HTTPS, monitoring |
| Landing page | What it does, pricing, "Get API Key" button |

**Weeks 5-8: Make It Sellable**

| Task | Why P0 |
|---|---|
| Expand sanctions sources (EU, UN lists) | Multi-jurisdiction coverage |
| Self-serve onboarding flow | Sign up → API key → sandbox → live |
| SDKs (Python, TypeScript) | Developer experience |
| Demo video (3 min) | Show full compliance flow |
| Begin SOC 2 Type I | Required for enterprise sales |

**Weeks 9-12: Get First Customer**

| Task | Why P0 |
|---|---|
| Outreach to 20 target companies | Direct sales to CTOs at stablecoin payroll platforms |
| Offer free 90-day pilot | Remove friction for first integrations |
| Travel Rule interop research | Partnership with Notabene/TRP for real data exchange |
| Iterate on feedback | First customers will reveal what's missing |

---

## 7. Pricing & Economics

| Tier | Price | Includes | Target |
|---|---|---|---|
| **Free** | $0 | 100 checks/month, mock sanctions data | Developers evaluating |
| **Starter** | $99/month + $0.10/check | Real OFAC screening, Travel Rule, audit export | Seed-stage startups |
| **Growth** | $499/month + $0.05/check | Everything + priority support, JSON/CSV API | Series A companies |
| **Enterprise** | Custom | Dedicated instance, SLA, SOC 2 report | Series B+ / regulated entities |

**Unit economics at scale:**
- Company doing 10,000 checks/month on Growth tier = $499 + $500 = **$999/month**
- Cost to serve: ~$50/month (compute + OFAC API calls)
- **Gross margin: ~95%**
- **Compare:** They'd pay $4,000-$40,000/month for Chainalysis + Notabene

---

## 8. Risks

### 8.1 Existential Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| **Stripe/Bridge adds compliance** | High (12-24 mo) | Be payment-rail agnostic. Integrate with Circle, Fireblocks, etc. Stripe can't own compliance for non-Stripe payments. |
| **Chainalysis launches self-serve tier** | Medium (18-36 mo) | Win on bundling and speed. Self-serve requires different org culture they may not build. |
| **Single false negative** | Any time | Real sanctions data, comprehensive tests, SOC 2 are P0. A compliance API that misses a sanctioned wallet destroys the company. |

### 8.2 Execution Risks

| Risk | Mitigation |
|---|---|
| **Can't get first customer** | Start free tier. Target dev communities. Open-source SDK. |
| **SOC 2 takes too long (6-12 mo)** | Target customers who need "something" over "nothing" pre-SOC 2. Begin process immediately. |
| **Product treated as optional reporting** | Design so accounting, banking, diligence workflows rely on Radius output. Embed in send flow. |

---

## 9. The Decision

**Is this a real business?**

**Yes, if:**
- The 90-day sprint ships real sanctions data, tests, and production infrastructure
- First customer pilots validate that companies will use Radius in daily workflow
- Product becomes operational infrastructure, not just a reporting tool

**Market validation:**
- $33T in stablecoin volume needs compliance checking
- 85 jurisdictions enforcing Travel Rule
- OFAC fining companies millions for missing sanctions screening
- Stripe paid $1.1B for stablecoin payment API — compliance layer doesn't exist at SMB tier
- Building in-house costs $500K-$1M+ and 12-18 months

**Product exists but isn't ready:**
- API design is sound
- Travel Rule engine (30+ jurisdictions) is valuable
- Sanctions data is fake, tests are missing, no production infra

**The gap:**

```
TODAY                           90 DAYS
┌──────────────────┐            ┌─────────────────────┐
│ Working prototype│ ────────►  │ Deployable product  │
│ Fake sanctions   │  90-day    │ Real OFAC screening │
│ No tests         │  sprint    │ 80%+ test coverage  │
│ No deployment    │            │ Cloud + CI/CD       │
│ No customers     │            │ 3-5 pilot customers │
└──────────────────┘            └─────────────────────┘
```

**The honest answer:** Radius is a real opportunity backed by market data, regulatory pressure, and customer pain. The 90-day sprint is what separates it from a side project.

The question isn't whether the market exists — it does, and it's growing at 26% CAGR.

**The question is: are you going to ship?**
