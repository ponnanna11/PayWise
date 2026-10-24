# PayWise — Simulate Before You Pay

<p align="center">
  <img src="assets/paywise_logo.png" alt="PayWise Logo" width="180">
</p>

<p align="center">
  <b>Pre-execution Safety Gateway for AI-Assisted Financial Operations</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/Streamlit-1.66+-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/Pydantic-2.12+-E92063?logo=pydantic&logoColor=white" alt="Pydantic">
  <img src="https://img.shields.io/badge/Tests-23%20Passed-brightgreen" alt="Tests 23 Passed">
  <img src="https://img.shields.io/badge/License-MIT-blue" alt="MIT License">
</p>

---

## 1. Project Overview & Core Principle

**PayWise** is an architectural pre-execution safety gateway that intercepts, models, and verifies financial disbursements proposed by autonomous AI agents or operations analysts before any transaction touches real banking rails or modifies corporate ledgers.

### The Core Principle
$$\textbf{AI proposes. PayWise simulates. Policies enforce. Humans approve. Revalidation protects.}$$

In enterprise financial operations, autonomous AI agents can draft supplier invoice settlements, vendor payment batches, and employee expense reconciliations. Without deterministic boundaries, AI agents may create catastrophic overdrafts, settle cancelled or duplicate contracts, pay suspended entities, or fall victim to prompt injections.

**PayWise is a simulation-only prototype.** It models consequences against a virtual financial ledger, strictly rejects invalid data, enforces 15 deterministic business and safety policies, and binds approvals with cryptographic hashes.

---

## 2. Problem Statement & Objectives

### The Problem
- **Hallucinations & Blind Executions**: AI agents executing API calls directly can double-pay invoices, breach reserve balances, or transact with sanction-listed vendors.
- **Time-of-Check to Time-of-Use (TOCTOU) Flaws**: A payment approved in the morning may become catastrophic by afternoon if another team disbursed funds in between (stale state).
- **Post-Approval Tampering**: An authorized payment batch might be altered after sign-off without re-triggering managerial scrutiny.

### Objectives
1. **Deterministic State Modeling**: Project post-execution balances ($S' = f(S, A)$) in an in-memory virtual sandbox without mutating persistent databases.
2. **Deterministic Safety Enforcement**: Evaluate 15 explicit policy rules producing actionable findings (`BLOCK`, `REQUIRE_APPROVAL`, `WARN`).
3. **Cryptographic Binding**: Bind approvals to exact SHA-256 hashes of the proposal, simulation preview, ledger state, and active policy set.
4. **Commit-Time Revalidation**: Re-check all 10 state and policy conditions atomically before executing any simulated commit.
5. **Separation of Concerns**: Treat all AI-generated content as untrusted input; never allow AI to modify ledgers, approve itself, or activate policies.

---

## 3. Technology Stack

- **Language**: Python 3.11+
- **Frontend / Presentation**: Streamlit (Light Mode, modern SaaS dashboard design)
- **Data Validation**: Pydantic v2
- **Persistent Storage**: SQLite with optimistic concurrency locks and foreign keys
- **Data Processing**: pandas
- **Testing**: pytest (23 automated test scenarios)
- **Architecture Diagrams**: PlantUML (.puml sources and vector SVGs)
- **Default Currency**: Indian Rupee (INR — ₹) with Indian numbering conventions (`₹ 1,85,000.00`)
- **AI Integration**: Configurable adapter supporting offline deterministic mock parsing or optional LLM integration

---

## 4. Main Application Modules

| Module | Purpose | Key Capabilities |
| :--- | :--- | :--- |
| **1. Operations Dashboard** | Real-time liquidity & governance | Simulated cash balance, reserved balance, available funds, pending outflow, blocked batches, and violation alerts. |
| **2. Proposal Management** | Pydantic intake & validation | Manages invoice payments, expense disbursements, and multi-item payment batches with strict validation. |
| **3. New Proposal Studio** | Multi-channel creation | Manual transaction builder, one-click safety barrier demo presets, and untrusted AI prompt drafter. |
| **4. Simulation & Preview** | Deterministic virtual preview | Before-and-after ledger comparison, aggregate outflow, budget impacts, and visual policy findings. |
| **5. Approvals Console** | Role-aware governance | Simulated role switcher (Business Analyst vs Manager vs CFO) with cryptographic hash binding and mandatory audit justification. |
| **6. Policy Management** | Rule administration & AI assistant | View and configure the 15 rules, adjust threshold parameters, toggle active rules, or draft policies from text with AI. |
| **7. Simulated Ledger** | Virtual banking accounts | Live inspection of HDFC, ICICI, SBI accounts, registered suppliers directory, and AP invoices. |
| **8. Audit Trail** | Tamper-evident governance log | Query and inspect complete lifecycle events (proposal created, violations, approvals, revalidations, commits) without logging secrets. |
| **9. System Architecture** | Formal technical blueprints | Embedded vector SVGs and PlantUML sources for System Architecture, Activity, Sequence, and DFD Level 1. |

---

## 5. Policy Engine: The 15 Deterministic Rules

The policy engine implements 15 explicit rules, separating **Mandatory Safety Guards** from **Configurable Business Rules**:

```
                              ┌── BLOCK (Halt execution)
R = g(S, S', A, P) ─────────► ├── REQUIRE_APPROVAL (Manager sign-off required)
                              └── WARN (Caution flag)
```

1. **`POL-001` (Insufficient Funds)**: Blocks disbursements when total proposed outflow exceeds available funds. *(Mandatory)*
2. **`POL-002` (Minimum Reserve Breach)**: Blocks disbursements that would cause ledger balances to breach mandatory reserve floors. *(Mandatory)*
3. **`POL-003` (Duplicate Invoice Payment)**: Blocks multiple transactions targeting the identical invoice ID. *(Mandatory)*
4. **`POL-004` (Settled/Cancelled Invoice Protection)**: Blocks payments mapped to invoices already marked `PAID`, `CANCELLED`, or `DISPUTED`. *(Mandatory)*
5. **`POL-005` (Approved Vendor Compliance)**: Blocks or escalates payments to vendors with unapproved or suspended standing. *(Configurable)*
6. **`POL-006` (Exact Invoice Amount Match)**: Blocks payments that deviate from the legally recognized invoice gross total. *(Mandatory)*
7. **`POL-007` (Payment Batch Aggregate Ceiling)**: Escalates payment batches exceeding ₹5,00,000 for executive CFO sign-off. *(Configurable)*
8. **`POL-008` (Discretionary Single Payment Threshold)**: Flags single payments > ₹50,000 for manager approval. *(Configurable)*
9. **`POL-009` (Structured Split Payment Evasion)**: Detects sub-threshold split payments to identical payees totaling above the threshold. *(Configurable)*
10. **`POL-010` (Disbursement Banking Schedule)**: Flags payments scheduled on weekends (Saturday/Sunday) or in the past. *(Configurable)*
11. **`POL-011` (Stale State Revalidation Guard)**: Blocks commit when ledger balance or invoice states changed since simulation preview. *(Mandatory)*
12. **`POL-012` (Post-Approval Tamper Protection)**: Invalidates approvals immediately if proposal payload was modified. *(Mandatory)*
13. **`POL-013` (Mandatory Authorization Enforcement)**: Rejects commit attempts without valid approved sign-off. *(Mandatory)*
14. **`POL-014` (Active Policy Consistency)**: Prevents commit if active policies or thresholds were changed since preview. *(Mandatory)*
15. **`POL-015` (Anomalous & High-Risk Payee Surveillance)**: Warns when transacting with high-risk vendor tiers. *(Configurable)*

*For full rule details and mathematical formulations, see [docs/policy_reference.md](docs/policy_reference.md).*

---

## 6. Commit-Time Revalidation & Atomic Transactions

When an approved proposal is submitted for commit, PayWise executes a 10-step commit-time revalidation guard:

```
[ Commit Trigger ]
        │
        ▼
1. Reload latest Account balance from SQLite
2. Reload latest Active Policies from SQLite
3. Verify current Proposal Hash == stored Proposal Hash (No tampering)
4. Verify required Approval is present & Valid
5. Verify approval.decision == APPROVED
6. Verify approval.proposal_hash == current_proposal_hash
7. Verify approval.ledger_state_hash == current_ledger_hash (Stale check)
8. Verify approval.policy_set_hash == current_policy_hash (Policy check)
9. Re-run Simulation on fresh state
10. Re-run Policy Engine with is_commit_check=True
        │
        ├── Any failure ──► Reject Commit, Mark STALE/BLOCKED, Log Audit
        │
        ▼ All pass
[ Atomic SQLite Transaction: BEGIN IMMEDIATE ]
  ├── Optimistic concurrency check (WHERE version = expected_version)
  ├── Deduct account ledger balance
  ├── Mark matched invoices as PAID
  ├── Update proposed transactions to COMMITTED
  ├── Insert into simulated_commits (Enforces UNIQUE proposal_id idempotency)
  ├── Update proposal status to COMMITTED_SIMULATED
  ├── Insert immutable SIMULATED_COMMIT_SUCCEEDED audit log
[ COMMIT TRANSACTION ]
```

---

## 7. Project Structure

```
paywise/
├── app.py                      # Main Streamlit web application entrypoint
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Build & package definition
├── pytest.ini                  # Pytest configuration
├── README.md                   # Comprehensive documentation
├── .env.example                # Sample environment configuration
├── .gitignore                  # Git ignore rules (excludes .db files)
├── assets/
│   └── paywise_logo.png        # PayWise application logo
├── data/
│   └── .gitkeep                # SQLite storage placeholder
├── scripts/
│   └── render_diagrams.py      # PlantUML SVG rendering script
├── src/
│   └── paywise/
│       ├── __init__.py
│       ├── config.py           # Application settings & environment loader
│       ├── models/             # Pydantic data models
│       │   ├── __init__.py
│       │   ├── account.py      # Bank accounts & reserve limits
│       │   ├── supplier.py     # Payee KYC & risk tiers
│       │   ├── invoice.py      # Accounts payable records
│       │   ├── proposal.py     # Proposals & proposed transactions
│       │   ├── policy.py       # Policy definitions & findings
│       │   ├── simulation.py   # State projection results
│       │   ├── approval.py     # Cryptographic approval records
│       │   └── audit.py        # Audit event records
│       ├── security/
│       │   ├── __init__.py
│       │   └── hashing.py      # Deterministic SHA-256 canonical hasher
│       ├── repositories/       # SQLite data access & transactions
│       │   ├── __init__.py
│       │   ├── database.py     # Schema definition & connection pool
│       │   ├── account_repo.py
│       │   ├── supplier_repo.py
│       │   ├── invoice_repo.py
│       │   ├── proposal_repo.py
│       │   ├── policy_repo.py
│       │   ├── approval_repo.py
│       │   └── audit_repo.py
│       ├── engines/            # Deterministic calculation engines
│       │   ├── __init__.py
│       │   ├── simulation_engine.py # In-memory projection S' = f(S, A)
│       │   └── policy_engine.py     # Rule engine R = g(S, S', A, P)
│       ├── services/           # Application coordination & gateways
│       │   ├── __init__.py
│       │   ├── proposal_service.py
│       │   ├── approval_service.py
│       │   ├── revalidation_service.py # 10-step commit revalidation
│       │   ├── commit_service.py       # Atomic commit & idempotency
│       │   ├── policy_service.py
│       │   └── ai_adapter.py           # Untrusted AI parser & generator
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── formatters.py   # Indian numbering & currency formatters
│       │   └── seed_data.py    # Idempotent Indian synthetic seed data
│       └── views/              # Streamlit modular UI views
│           ├── __init__.py
│           ├── styles.py       # Light mode SaaS styling
│           ├── dashboard_view.py
│           ├── proposals_view.py
│           ├── new_proposal_view.py
│           ├── simulation_view.py
│           ├── approvals_view.py
│           ├── policies_view.py
│           ├── ledger_view.py
│           ├── audit_view.py
│           └── architecture_view.py
├── tests/                      # Automated test suite (23 tests)
│   ├── conftest.py             # Isolated temporary database fixtures
│   ├── test_simulation.py      # Simulation determinism & non-mutation
│   ├── test_policies.py        # Policy rules 1 to 10 & 15
│   ├── test_approval.py        # Cryptographic approval binding & tamper checks
│   ├── test_revalidation.py    # Stale ledger, policy changes, missing approvals
│   └── test_commit.py          # Atomic commits, idempotency, failure rollback
└── docs/
    ├── architecture.md         # Deep technical architecture design
    ├── policy_reference.md     # Mathematical policy specifications
    └── diagrams/               # PlantUML source files and rendered SVGs
        ├── system_architecture.puml & .svg
        ├── activity_diagram.puml & .svg
        ├── sequence_diagram.puml & .svg
        └── dfd_level1.puml & .svg
```

---

## 8. Installation & Setup on Windows

### Prerequisites
- Python 3.11 or higher installed on Windows
- Windows PowerShell

### Step-by-Step Installation

1. Open PowerShell and navigate to the project directory:
   ```powershell
   cd "c:\Users\Ponnanna KC\OneDrive\Desktop\paywise"
   ```

2. Create a virtual environment:
   ```powershell
   python -m venv .venv
   ```

3. Activate the virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   *(If script execution is disabled on your system, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

4. Install the required dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

5. (Optional) Configure environment variables:
   ```powershell
   Copy-Item .env.example .env
   ```

---

## 9. How to Run the Application

Launch the Streamlit dashboard:

```powershell
streamlit run app.py
```

The application will automatically initialize the local SQLite database with realistic synthetic Indian corporate data and open in your default browser at:

```
http://localhost:8501
```

---

## 10. How to Run Automated Tests

Execute the complete pytest test suite covering all 20+ required scenarios:

```powershell
python -m pytest -v
```

All 23 automated tests pass with 100% success rate:
- Safe batch approvals
- Reserve balance breach blocking
- Duplicate invoice blocking
- Cancelled/settled invoice blocking
- Unapproved/suspended supplier blocking
- Amount mismatch detection
- Batch budget ceiling exceedance
- Discretionary threshold escalation
- Split payment evasion detection
- Pydantic validation rejection
- Post-approval tamper invalidation
- Ledger drift stale state detection
- Policy change revalidation triggers
- Unapproved commit rejection
- Atomic transaction execution & optimistic locking
- Idempotency & double-commit prevention
- Non-mutation during simulation preview

---

## 11. How to Render PlantUML Diagrams

The four required diagrams are pre-rendered into vector SVGs in `docs/diagrams/`:
- `docs/diagrams/system_architecture.puml` -> `system_architecture.svg`
- `docs/diagrams/activity_diagram.puml` -> `activity_diagram.svg`
- `docs/diagrams/sequence_diagram.puml` -> `sequence_diagram.svg`
- `docs/diagrams/dfd_level1.puml` -> `dfd_level1.svg`

To re-render the `.puml` files at any time, run the built-in script:

```powershell
python scripts/render_diagrams.py
```

---

## 12. Optional AI Integration Configuration

PayWise includes a configurable AI adapter (`paywise.services.ai_adapter.AIAdapter`).
- **Default Mode (Offline)**: Runs completely without internet or API keys using the built-in regex and structural rule extractor.
- **LLM Mode (Optional)**: If you wish to connect an OpenAI, Anthropic, or Gemini endpoint, populate `.env`:
  ```ini
  PAYWISE_AI_PROVIDER=openai
  PAYWISE_AI_API_KEY=your_api_key_here
  PAYWISE_AI_MODEL=gpt-4o-mini
  ```
- **Safety Guarantee**: Regardless of whether offline or online AI is selected, AI outputs are always treated as **untrusted candidate drafts**. They must pass Pydantic schema validation, in-memory simulation, and human authorization before activation.

---

## 13. Known Limitations & Future Enhancements

### Known Limitations (Simulation-Only Prototype)
1. **Virtual Rails**: PayWise simulates banking balances locally in SQLite. It does not initiate real NEFT, RTGS, IMPS, or ACH wire transactions.
2. **Simplified Authentication**: Role-switching is interactive for demonstration purposes; production deployments require enterprise SSO / SAML / OAuth2 integration.
3. **Single Currency Base**: Demonstrated in Indian Rupees (INR — ₹). Multi-currency conversion requires a real-time foreign exchange rate provider.

### Future Enhancements
1. **ERP Adapters**: Real-time two-way synchronization with SAP, Oracle NetSuite, and TallyPrime.
2. **Hardware Security Modules (HSM)**: Cryptographic signature generation using PKCS#11 or cloud KMS for institutional multi-party signing.
3. **Dynamic Anomaly Scoring**: Integration of statistical isolation forests for unusual payment detection alongside deterministic rules.

---

## 14. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
