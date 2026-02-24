# Radius — Business Analysis

**Stage:** Pre-seed
**Category:** Financial infrastructure (payment attestation + compliance)
**Core Idea:** Radius creates a structured, auditable record for every stablecoin payment at the moment it happens.

---

## 1. What Problem Actually Exists

Stablecoin companies do not fail because they *cannot send payments*.
They fail because they cannot **explain payments later**.

When a company grows, four events happen:

1. Accountant cannot close books
2. Bank asks source-of-funds questions
3. Investor diligence requests payment controls
4. Expansion into new jurisdiction requires records

Today their workflow:

send → paste tx hash → spreadsheet → reconstruct history months later

This reconstruction becomes extremely expensive and sometimes impossible.

Radius solves the missing layer:
a permanent payment explanation created at send-time.

---

## 2. Product Definition

Radius is not a payment processor.
Radius is not a legal oracle.

Radius is a **payment attestation engine**.

Before sending funds:

company → Radius.check(payment)

Radius returns:

* sanctions result
* risk classification
* regulatory obligations
* structured metadata record

After sending:
company → attach tx hash

Result:
Every transfer becomes a complete financial object instead of a blockchain event.

---

## 3. Why This Matters

Blockchain transactions store movement of money.
Businesses must store intent of money.

Auditors, banks, and investors care about:

* who approved it
* why it was sent
* whether it was screened
* what rules applied at the time

Radius turns payments into audit-ready records automatically.

---

## 4. Ideal Customer

Not regulated enterprises.

First customers are companies crossing operational maturity:

**Profile**

* 10-50 employees
* engineers sending payouts programmatically
* 100+ stablecoin transfers per month
* no compliance officer

**Trigger events**

* accounting friction
* banking review
* fundraising diligence
* international expansion

They do not want a compliance department.
They want the problem to disappear.

---

## 5. Market Reality

The opportunity is not all crypto payments.

The opportunity is businesses that:

* repeatedly send money
* must justify transactions later
* cannot afford enterprise compliance tooling

Market behaves like:
audit infrastructure / SOC2 automation / tax tooling

Small number of customers
High urgency
High retention

---

## 6. Competitive Landscape

Companies today assemble a stack:

risk analytics + accounting software + spreadsheets

No tool owns the payment lifecycle record.

Radius replaces the manual glue.

Primary alternative:
doing nothing until audit time

Not replacing Chainalysis
Not replacing accounting software
Sits between execution and reporting

---

## 7. Product Value

Radius provides value even if companies never block a payment.

Core benefit:
they never reconstruct financial history again

Secondary benefit:
they can block risky transactions when desired

Primary product = record
Secondary product = enforcement

---

## 8. Moat

Initial moat:
historical financial records embedded in operations

Once a company’s payment history lives in Radius, switching requires rebuilding audit history.

Later moat:
risk models trained on aggregated transaction context

---

## 9. Risks

Key assumption to validate:
companies will depend on Radius in daily workflow

Failure mode:
treated as optional reporting instead of operational infrastructure

Mitigation:
design product so accounting, banking, and diligence workflows rely on Radius output.

---

## 10. Positioning

Not:
stablecoin compliance API

Instead:
financial attestation layer for programmable payments

Stablecoin is the first entry point because:

* developers control transfers
* no incumbent owns the workflow
* compliance expectations exist but tooling does not

Long term expands to all internet-native payment rails.

---

## Summary

Radius is infrastructure that converts blockchain transfers into explainable financial events.

Companies adopt it when they transition from:
moving money → operating a financial system

The business is viable if Radius becomes part of the send flow, not a post-processing report.
