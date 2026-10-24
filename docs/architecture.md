# PayWise — Architecture & Technical Design Document

## 1. Executive Overview

**PayWise** is a pre-execution safety gateway for AI-assisted financial operations.

In autonomous corporate workflows, generative AI agents can prepare supplier payments, reconcile invoice batches, or organize expense reimbursements. Before any proposed action can affect real ledger balances or initiate bank transfers, PayWise simulates their consequences against a virtual financial ledger, evaluates them against explicit, deterministic policies, presents a clear consequence preview, and enforces role-aware human approval and commit-time revalidation.

### Core Principle
$$\textbf{AI proposes. PayWise simulates. Policies enforce. Humans approve. Revalidation protects.}$$

The system is architected around absolute containment:
1. **The AI agent never modifies the ledger.**
2. **The AI agent cannot bypass the policy engine.**
3. **The AI agent cannot approve its own proposals.**
4. **The AI agent cannot activate or modify active policies.**
5. **No commit is allowed without passing commit-time revalidation.**

---

## 2. Logical Architecture

The logical architecture consists of five distinct, decoupled layers:

```
[ Business User / AI Agent ]
             │
             ▼
[ Presentation Layer: Streamlit UI ]
             │
             ▼
[ Proposal Management & Pydantic Schema Validation ]
             │
             ▼
[ Deterministic Simulation Engine: S' = f(S, A) ]
             │
             ▼
[ Deterministic Policy Engine: R = g(S, S', A, P) ]
             │
             ▼
[ Interactive Consequence Preview & Risk Assessment ]
             │
             ▼
[ Role-Aware Approval Workflow & Hash Binding ]
             │
             ▼
[ Commit-Time Revalidation Guard (10-Step Verification) ]
             │
             ▼
[ Atomic Simulated Commit & Optimistic Concurrency Update (SQLite) ]
             │
             ▼
[ Immutable Tamper-Evident Audit Trail ]
```

---

## 3. Cryptographic State Binding

To prevent **Time-of-Check to Time-of-Use (TOCTOU)** vulnerabilities, stale approvals, or post-approval tampering, PayWise binds every proposal, preview, approval, and commit using SHA-256 canonical hashing:

1. **`proposal_hash`**:
   $$\text{SHA-256}(\text{canonical\_json}(\text{proposal\_id}, \text{version}, \text{account\_id}, \text{sorted\_transactions}))$$
   Any modification to line items, amounts, dates, or accounts immediately alters this hash.

2. **`ledger_state_hash`**:
   $$\text{SHA-256}(\text{canonical\_json}(\text{account\_id}, \text{balance}, \text{reserved}, \text{version}, \text{relevant\_invoices}))$$
   If another concurrent operation deducts funds or settles an invoice, this hash changes.

3. **`policy_set_hash`**:
   $$\text{SHA-256}(\text{canonical\_json}(\text{sorted\_active\_policies}))$$
   If an administrator alters a threshold or activates/deactivates a rule, this hash changes.

4. **`preview_hash`**:
   $$\text{SHA-256}(\text{canonical\_json}(\text{proposal\_hash}, \text{projected\_balance}, \text{outflow}, \text{findings}))$$

When an authorized officer grants approval, the approval record cryptographically captures and seals all four hashes.

---

## 4. Commit-Time Revalidation Protocol

Revalidation is the critical gatekeeper prior to committing any simulated payout. The 10-step protocol is strictly enforced:

1. **Reload Latest Ledger State**: Query current balance, reserve, and version from SQLite.
2. **Reload Latest Active Policies**: Query active policy set from SQLite.
3. **Confirm Proposal Unchanged**: Recompute proposal hash; ensure it matches the stored version.
4. **Confirm Required Approval Present**: If proposal requires approval, verify an approval record exists.
5. **Confirm Approval Decision**: Verify that `approval.decision == APPROVED` and `approval.is_valid == True`.
6. **Verify Proposal Hash Matches Approval**: Ensure `approval.proposal_hash == current_proposal_hash`.
7. **Verify Ledger State Hash Matches Approval**: Ensure `approval.ledger_state_hash == current_ledger_hash` (stale check).
8. **Verify Policy Set Hash Matches Approval**: Ensure `approval.policy_set_hash == current_policy_hash`.
9. **Re-run Simulation**: Compute fresh projected state $S' = f(S, A)$.
10. **Re-run Policy Engine**: Run with `is_commit_check=True`. Stop immediately if any `BLOCK` or unauthorized requirement triggers.

Only after passing all 10 checks is the atomic SQLite transaction initiated.

---

## 5. Database Schema & Concurrency

The system uses SQLite with transactions and foreign keys enabled:

- **`accounts`**: Stores account balances, reserves, and optimistic locking integer `version`.
- **`suppliers`**: Stores KYC status, GSTIN, PAN, bank account, and risk tiers.
- **`invoices`**: Accounts payable invoices tracking `PENDING`, `PAID`, `CANCELLED`, `DISPUTED`.
- **`proposals`**: Root proposal records tracking status, version, and `proposal_hash`.
- **`proposed_transactions`**: Individual disbursement line items linked to proposals.
- **`policies`**: Active rule definitions, parameters JSON, and mandatory flags.
- **`simulation_previews`**: Cached consequence previews with financial projections.
- **`approvals`**: Cryptographic approval records bound to proposal and ledger hashes.
- **`simulated_commits`**: Unique proposal commit records enforcing idempotency.
- **`audit_events`**: Immutable event log with timestamps, actors, outcomes, and JSON context.

---

## 6. Architecture Diagrams

Editable PlantUML sources and rendered vector SVG diagrams are located in `docs/diagrams/`:

1. **System Architecture**: `docs/diagrams/system_architecture.puml` ([SVG](diagrams/system_architecture.svg))
2. **Activity Diagram**: `docs/diagrams/activity_diagram.puml` ([SVG](diagrams/activity_diagram.svg))
3. **Sequence Diagram**: `docs/diagrams/sequence_diagram.puml` ([SVG](diagrams/sequence_diagram.svg))
4. **DFD Level 1**: `docs/diagrams/dfd_level1.puml` ([SVG](diagrams/dfd_level1.svg))
