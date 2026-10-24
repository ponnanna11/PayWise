# PayWise — Policy Engine & Rule Reference Guide

## 1. Executive Summary

PayWise enforces financial safety prior to execution using a deterministic policy engine:

$$\mathcal{R} = g(\mathcal{S}, \mathcal{S}', \mathcal{A}, \mathcal{P})$$

Where:
- $\mathcal{S}$ is the current persistent ledger state (account balances, reserve floors, invoice statuses).
- $\mathcal{S}'$ is the projected virtual ledger state calculated by the simulation engine $f(\mathcal{S}, \mathcal{A})$.
- $\mathcal{A}$ is the proposed action or batch of transactions.
- $\mathcal{P}$ is the active set of policies and threshold configurations.
- $\mathcal{R}$ is the ordered list of structured findings.

---

## 2. Policy Severity Levels

Every policy finding produces one of three distinct severity levels:

| Severity | Lifecycle Impact | User Interface Presentation | Action Required |
| :--- | :--- | :--- | :--- |
| **`BLOCK`** | **Halts execution.** The proposal cannot proceed to approval or commit under any circumstances. | Red banner, warning icons, and disabled commit buttons. | The operator must amend or delete violating transactions or deposit funds. |
| **`REQUIRE_APPROVAL`** | **Escalates to authorized officer.** Cannot be committed without valid, signed approval. | Amber highlight badge with direct routing to Approvals console. | Designated manager (CFO / Finance Manager) must sign off with audit justification. |
| **`WARN`** | **Informational caution.** Highlights potential operational or compliance anomalies. | Blue notification banner. | Operator reviews warning context. Proceeding is allowed. |

---

## 3. Policy Classification Matrix: Mandatory vs. Configurable

PayWise separates **Mandatory Safety Guards** from **Configurable Business Rules**.

### A. Mandatory Safety Guards
Mandatory safety guards represent core financial invariants. They **cannot be deactivated or bypassed**, even by administrators:
- **`POL-001` (Insufficient Funds)**: Enforces that account balances never turn negative.
- **`POL-002` (Reserve Balance Protection)**: Protects the statutory and operational reserve floor.
- **`POL-003` (Duplicate Invoice Payment)**: Precludes paying the same vendor invoice multiple times.
- **`POL-004` (Settled/Cancelled Invoice Protection)**: Rejects disbursements targeting non-payable invoice states.
- **`POL-006` (Exact Invoice Amount Match)**: Rejects payment sums that deviate from legal billed invoices.
- **`POL-011` (Stale Proposal Revalidation)**: Rejects commit if ledger balance drifted after preview.
- **`POL-012` (Post-Approval Tamper Protection)**: Invalidates approval immediately if transactions were modified.
- **`POL-013` (Mandatory Authorization Enforcement)**: Blocks unapproved commits for threshold-exceeding proposals.
- **`POL-014` (Active Policy Consistency)**: Halts execution if policies were reconfigured during approval.

### B. Configurable Business Rules
Configurable rules reflect operational policies, departmental limits, and compliance preferences. Their thresholds can be customized and their activation toggled:
- **`POL-005` (Approved Vendor Compliance)**: Restricts payouts to vendors with `APPROVED` KYC standing.
- **`POL-007` (Payment Batch Aggregate Ceiling)**: Escalates batches exceeding budget limit (default: ₹5,00,000.00).
- **`POL-008` (Discretionary Single Payment Threshold)**: Flags single payments > ₹50,000.00 for manager sign-off.
- **`POL-009` (Structured Split Payment Evasion)**: Detects structured payments to identical vendors evading single thresholds.
- **`POL-010` (Disbursement Banking Schedule)**: Flags payments scheduled on non-banking weekend dates or in the past.
- **`POL-015` (Anomalous & High-Risk Payee Surveillance)**: Warns when transacting with high-risk vendor tiers.

---

## 4. Comprehensive Rule Specification

### Rule 1: Insufficient Available Funds (`POL-001`)
- **Rule Type**: `INSUFFICIENT_FUNDS`
- **Severity**: `BLOCK`
- **Mandatory**: Yes
- **Evaluation**: Triggered if projected balance $\mathcal{S}'.balance < 0$ or total proposal outflow exceeds account liquid available funds.
- **Remediation**: Deposit funds or downsize disbursement batch.

### Rule 2: Minimum Reserve Balance Breach (`POL-002`)
- **Rule Type**: `MINIMUM_RESERVE_BREACH`
- **Severity**: `BLOCK`
- **Mandatory**: Yes
- **Evaluation**: Triggered if projected balance $\mathcal{S}'.balance < \mathcal{S}.reserved\_balance$.
- **Remediation**: Reduce payment outflow to retain protected reserve.

### Rule 3: Duplicate Invoice Payment (`POL-003`)
- **Rule Type**: `DUPLICATE_INVOICE_PAYMENT`
- **Severity**: `BLOCK`
- **Mandatory**: Yes
- **Evaluation**: Triggered if two or more transaction entries in the proposal reference identical `invoice_id`.
- **Remediation**: Remove redundant line items.

### Rule 4: Settled or Cancelled Invoice Protection (`POL-004`)
- **Rule Type**: `CANCELLED_OR_PAID_INVOICE`
- **Severity**: `BLOCK`
- **Mandatory**: Yes
- **Evaluation**: Triggered if matching invoice status is `PAID`, `CANCELLED`, or `DISPUTED`.
- **Remediation**: Drop settled or cancelled invoice from payout batch.

### Rule 5: Approved Vendor Compliance (`POL-005`)
- **Rule Type**: `UNAPPROVED_SUPPLIER`
- **Severity**: `BLOCK`
- **Mandatory**: No (Configurable)
- **Evaluation**: Triggered if payee vendor status is not `APPROVED` (e.g. `SUSPENDED`, `PENDING_VERIFICATION`).
- **Remediation**: Complete vendor compliance review before releasing funds.

### Rule 6: Exact Invoice Amount Reconciliation (`POL-006`)
- **Rule Type**: `AMOUNT_MISMATCH`
- **Severity**: `BLOCK`
- **Mandatory**: Yes
- **Parameters**: `tolerance_amount` (default: 0.0)
- **Evaluation**: Triggered if $|tx.amount - invoice.amount| > tolerance$.
- **Remediation**: Reconcile payment figure with vendor invoice.

### Rule 7: Payment Batch Aggregate Ceiling (`POL-007`)
- **Rule Type**: `BATCH_BUDGET_EXCEEDED`
- **Severity**: `REQUIRE_APPROVAL`
- **Mandatory**: No (Configurable)
- **Parameters**: `max_batch_amount` (default: 500,000.0 INR)
- **Evaluation**: Triggered if $\sum tx.amount > max\_batch\_amount$.
- **Remediation**: Obtain executive sign-off.

### Rule 8: Discretionary Single Payment Threshold (`POL-008`)
- **Rule Type**: `APPROVAL_THRESHOLD_EXCEEDED`
- **Severity**: `REQUIRE_APPROVAL`
- **Mandatory**: No (Configurable)
- **Parameters**: `threshold_amount` (default: 50,000.0 INR)
- **Evaluation**: Triggered if any single transaction $> threshold\_amount$.
- **Remediation**: Route to Finance Manager for authorization.

### Rule 9: Structured Split Payment Evasion Detector (`POL-009`)
- **Rule Type**: `SPLIT_PAYMENT_DETECTION`
- **Severity**: `REQUIRE_APPROVAL`
- **Mandatory**: No (Configurable)
- **Parameters**: `threshold_amount` (50,000.0), `window_days` (3)
- **Evaluation**: Detects multiple transactions to same payee where each transaction $\le 50,000$ but their sum $> 50,000$.
- **Remediation**: Consolidate payments into single authorized voucher.

### Rule 10: Disbursement Schedule Compliance (`POL-010`)
- **Rule Type**: `PAYMENT_DATE_SCHEDULING`
- **Severity**: `WARN`
- **Mandatory**: No (Configurable)
- **Parameters**: `allow_past_dates` (False), `allow_weekends` (False), `max_advance_days` (60)
- **Evaluation**: Flags past execution dates, Saturday/Sunday banking holidays, or distant dates.
- **Remediation**: Adjust execution date to active banking day.

### Rule 11: Stale State Revalidation Guard (`POL-011`)
- **Rule Type**: `STALE_PROPOSAL`
- **Severity**: `BLOCK`
- **Mandatory**: Yes
- **Evaluation**: Triggered during commit-time revalidation if ledger hash or invoice version changed since simulation preview.
- **Remediation**: Re-run simulation preview and re-approve.

### Rule 12: Post-Approval Tamper Protection (`POL-012`)
- **Rule Type**: `MODIFIED_AFTER_APPROVAL`
- **Severity**: `BLOCK`
- **Mandatory**: Yes
- **Evaluation**: Triggered if proposal content hash $\ne$ approved proposal hash.
- **Remediation**: Re-submit modified proposal for authorization.

### Rule 13: Mandatory Authorization Enforcement (`POL-013`)
- **Rule Type**: `UNAUTHORIZED_COMMIT_ATTEMPT`
- **Severity**: `BLOCK`
- **Mandatory**: Yes
- **Evaluation**: Triggered if a proposal requiring approval is submitted for commit without an approved, valid sign-off.
- **Remediation**: Obtain authorized approver sign-off.

### Rule 14: Active Policy Version Consistency (`POL-014`)
- **Rule Type**: `POLICY_CHANGED_SINCE_PREVIEW`
- **Severity**: `BLOCK`
- **Mandatory**: Yes
- **Evaluation**: Triggered if active policy set hash changed between preview approval and commit.
- **Remediation**: Re-simulate against the newly activated policy configuration.

### Rule 15: Anomalous & High-Risk Payee Surveillance (`POL-015`)
- **Rule Type**: `UNUSUAL_PAYMENT_ACTIVITY`
- **Severity**: `WARN`
- **Mandatory**: No (Configurable)
- **Parameters**: `high_risk_tier_flag` (True), `unusual_amount_multiplier` (2.5)
- **Evaluation**: Flags vendors with HIGH risk tier or amounts exceeding typical baseline.
- **Remediation**: Secondary verification of vendor bank account details.
