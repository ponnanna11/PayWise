"""
Deterministic seed data generator for PayWise.
Seeds realistic Indian corporate finance entities, accounts, suppliers, invoices, and standard policies.
"""
from datetime import date, datetime, timedelta
from typing import Optional
from paywise.models.account import Account, AccountStatus
from paywise.models.approval import Approval, ApprovalDecision
from paywise.models.invoice import Invoice, InvoiceStatus
from paywise.models.policy import Policy, PolicyRuleType, PolicySeverity
from paywise.models.proposal import (
    Proposal,
    ProposalStatus,
    ProposalType,
    ProposedTransaction,
    TransactionType,
)
from paywise.models.supplier import RiskTier, Supplier, SupplierStatus
from paywise.repositories.account_repo import AccountRepository
from paywise.repositories.supplier_repo import SupplierRepository
from paywise.repositories.approval_repo import ApprovalRepository
from paywise.repositories.audit_repo import AuditRepository
from paywise.repositories.database import init_db
from paywise.repositories.invoice_repo import InvoiceRepository
from paywise.repositories.policy_repo import PolicyRepository
from paywise.repositories.proposal_repo import ProposalRepository


def seed_database(db_path: Optional[str] = None) -> None:
    """Populates database with idempotent seed records."""
    init_db(db_path)

    acc_repo = AccountRepository(db_path)
    sup_repo = SupplierRepository(db_path)
    inv_repo = InvoiceRepository(db_path)
    pol_repo = PolicyRepository(db_path)
    prop_repo = ProposalRepository(db_path)

    # 1. Accounts
    accounts = [
        Account(
            id="ACC-HDFC-MAIN",
            account_number="HDFC-00129384910",
            bank_name="HDFC Bank",
            account_name="Primary Operating Account",
            currency="INR",
            current_balance=3500000.00,
            reserved_balance=500000.00,
            status=AccountStatus.ACTIVE,
            version=1,
            updated_at=datetime.utcnow(),
        ),
        Account(
            id="ACC-ICICI-EXP",
            account_number="ICICI-99281726354",
            bank_name="ICICI Bank",
            account_name="Vendor & Operational Disbursements",
            currency="INR",
            current_balance=750000.00,
            reserved_balance=150000.00,
            status=AccountStatus.ACTIVE,
            version=1,
            updated_at=datetime.utcnow(),
        ),
        Account(
            id="ACC-SBI-ESCROW",
            account_number="SBIN-00293847561",
            bank_name="State Bank of India",
            account_name="Statutory Tax & Reserve Escrow",
            currency="INR",
            current_balance=1200000.00,
            reserved_balance=1000000.00,
            status=AccountStatus.ACTIVE,
            version=1,
            updated_at=datetime.utcnow(),
        ),
    ]
    for acc in accounts:
        acc_repo.upsert(acc)

    # 2. Suppliers
    suppliers = [
        Supplier(
            id="SUP-TCS-01",
            name="Tata Consultancy Services Ltd",
            gstin="27AAACT2727Q1ZB",
            pan="AAACT2727Q",
            bank_account_number="50200019283746",
            bank_ifsc="HDFC0000060",
            status=SupplierStatus.APPROVED,
            risk_tier=RiskTier.LOW,
            default_category="Cloud & IT Services",
            created_at=datetime.utcnow(),
        ),
        Supplier(
            id="SUP-INFY-02",
            name="Infosys Limited",
            gstin="29AAACI4740L1Z2",
            pan="AAACI4740L",
            bank_account_number="000205018273",
            bank_ifsc="ICIC0000002",
            status=SupplierStatus.APPROVED,
            risk_tier=RiskTier.LOW,
            default_category="Software Consulting",
            created_at=datetime.utcnow(),
        ),
        Supplier(
            id="SUP-AIRTEL-03",
            name="Bharti Airtel Enterprise Ltd",
            gstin="07AAACB2894G1ZG",
            pan="AAACB2894G",
            bank_account_number="001102938475",
            bank_ifsc="SBIN0000691",
            status=SupplierStatus.APPROVED,
            risk_tier=RiskTier.LOW,
            default_category="Telecom & Connectivity",
            created_at=datetime.utcnow(),
        ),
        Supplier(
            id="SUP-APEX-04",
            name="Apex Facilities & Logistics Pvt Ltd",
            gstin="29AABCA1234F1ZX",
            pan="AABCA1234F",
            bank_account_number="918273645019",
            bank_ifsc="UTIB0000123",
            status=SupplierStatus.SUSPENDED,
            risk_tier=RiskTier.HIGH,
            default_category="Office Maintenance",
            created_at=datetime.utcnow(),
        ),
        Supplier(
            id="SUP-SHADOW-05",
            name="BlueStar Logistics Unverified",
            gstin=None,
            pan=None,
            bank_account_number="123456789012",
            bank_ifsc="YESB0000999",
            status=SupplierStatus.PENDING_VERIFICATION,
            risk_tier=RiskTier.HIGH,
            default_category="Logistics",
            created_at=datetime.utcnow(),
        ),
        Supplier(
            id="SUP-GODREJ-06",
            name="Godrej Properties Facility Services",
            gstin="27AAACG0829M1ZQ",
            pan="AAACG0829M",
            bank_account_number="019283746501",
            bank_ifsc="KKBK0000101",
            status=SupplierStatus.APPROVED,
            risk_tier=RiskTier.MEDIUM,
            default_category="Commercial Lease",
            created_at=datetime.utcnow(),
        ),
    ]
    for sup in suppliers:
        sup_repo.upsert(sup)

    # 3. Invoices
    today = date.today()
    invoices = [
        Invoice(
            id="INV-2026-001",
            supplier_id="SUP-TCS-01",
            invoice_number="TCS-MUM-2026-104",
            invoice_date=today - timedelta(days=15),
            due_date=today + timedelta(days=15),
            amount=185000.00,
            currency="INR",
            status=InvoiceStatus.PENDING,
            description="Enterprise Cloud Migration Milestone 1",
            version=1,
        ),
        Invoice(
            id="INV-2026-002",
            supplier_id="SUP-INFY-02",
            invoice_number="INFY-BLR-2026-442",
            invoice_date=today - timedelta(days=20),
            due_date=today + timedelta(days=10),
            amount=45000.00,
            currency="INR",
            status=InvoiceStatus.PENDING,
            description="ERP Maintenance & Security Patching",
            version=1,
        ),
        Invoice(
            id="INV-2026-003",
            supplier_id="SUP-AIRTEL-03",
            invoice_number="AIRTEL-DEL-2026-901",
            invoice_date=today - timedelta(days=10),
            due_date=today + timedelta(days=5),
            amount=28500.00,
            currency="INR",
            status=InvoiceStatus.PENDING,
            description="Primary Leased Line Internet Access",
            version=1,
        ),
        Invoice(
            id="INV-2026-004",
            supplier_id="SUP-AIRTEL-03",
            invoice_number="AIRTEL-DEL-2026-880",
            invoice_date=today - timedelta(days=40),
            due_date=today - timedelta(days=10),
            amount=32000.00,
            currency="INR",
            status=InvoiceStatus.PAID,
            description="Backup Microwave Bandwidth Settlement",
            paid_at=datetime.utcnow() - timedelta(days=12),
            paid_transaction_id="TX-PAID-PRIOR-01",
            version=2,
        ),
        Invoice(
            id="INV-2026-005",
            supplier_id="SUP-APEX-04",
            invoice_number="APEX-BLR-2026-012",
            invoice_date=today - timedelta(days=25),
            due_date=today - timedelta(days=5),
            amount=12000.00,
            currency="INR",
            status=InvoiceStatus.CANCELLED,
            description="Cancelled Deep Cleaning Contract",
            version=1,
        ),
        Invoice(
            id="INV-2026-006",
            supplier_id="SUP-GODREJ-06",
            invoice_number="GODREJ-MUM-2026-009",
            invoice_date=today - timedelta(days=5),
            due_date=today + timedelta(days=25),
            amount=220000.00,
            currency="INR",
            status=InvoiceStatus.PENDING,
            description="Headquarters Monthly Lease Payment",
            version=1,
        ),
        Invoice(
            id="INV-2026-007",
            supplier_id="SUP-TCS-01",
            invoice_number="TCS-MUM-2026-199",
            invoice_date=today - timedelta(days=7),
            due_date=today + timedelta(days=20),
            amount=95000.00,
            currency="INR",
            status=InvoiceStatus.PENDING,
            description="Cybersecurity Red Teaming & Assessment",
            version=1,
        ),
    ]
    for inv in invoices:
        inv_repo.upsert(inv)

    # 4. Policies (15 Rules)
    policies = [
        Policy(
            id="POL-001",
            name="Sufficient Available Funds Enforcement",
            rule_type=PolicyRuleType.INSUFFICIENT_FUNDS,
            severity=PolicySeverity.BLOCK,
            is_mandatory=True,
            is_active=True,
            version=1,
            parameters={},
            description="Blocks transactions when proposed total exceeds liquid funds available.",
        ),
        Policy(
            id="POL-002",
            name="Minimum Reserve Balance Protection",
            rule_type=PolicyRuleType.MINIMUM_RESERVE_BREACH,
            severity=PolicySeverity.BLOCK,
            is_mandatory=True,
            is_active=True,
            version=1,
            parameters={},
            description="Blocks transactions that would cause ledger balance to fall below reserved threshold.",
        ),
        Policy(
            id="POL-003",
            name="Duplicate Invoice Payment Prevention",
            rule_type=PolicyRuleType.DUPLICATE_INVOICE_PAYMENT,
            severity=PolicySeverity.BLOCK,
            is_mandatory=True,
            is_active=True,
            version=1,
            parameters={},
            description="Blocks proposals containing multiple payments targeting the exact same invoice.",
        ),
        Policy(
            id="POL-004",
            name="Settled or Cancelled Invoice Protection",
            rule_type=PolicyRuleType.CANCELLED_OR_PAID_INVOICE,
            severity=PolicySeverity.BLOCK,
            is_mandatory=True,
            is_active=True,
            version=1,
            parameters={},
            description="Blocks payments mapped to invoices already marked as PAID, CANCELLED, or DISPUTED.",
        ),
        Policy(
            id="POL-005",
            name="Approved Vendor Compliance",
            rule_type=PolicyRuleType.UNAPPROVED_SUPPLIER,
            severity=PolicySeverity.BLOCK,
            is_mandatory=False,
            is_active=True,
            version=1,
            parameters={},
            description="Requires payees to possess APPROVED supplier standing in the company directory.",
        ),
        Policy(
            id="POL-006",
            name="Exact Invoice Amount Reconciliation",
            rule_type=PolicyRuleType.AMOUNT_MISMATCH,
            severity=PolicySeverity.BLOCK,
            is_mandatory=True,
            is_active=True,
            version=1,
            parameters={"tolerance_amount": 0.0},
            description="Blocks payments that deviate from the legally recognized invoice gross total.",
        ),
        Policy(
            id="POL-007",
            name="Payment Batch Aggregate Ceiling",
            rule_type=PolicyRuleType.BATCH_BUDGET_EXCEEDED,
            severity=PolicySeverity.REQUIRE_APPROVAL,
            is_mandatory=False,
            is_active=True,
            version=1,
            parameters={"max_batch_amount": 500000.0},
            description="Escalates payment batches exceeding ₹5,00,000 for executive sign-off.",
        ),
        Policy(
            id="POL-008",
            name="Discretionary Single Transaction Threshold",
            rule_type=PolicyRuleType.APPROVAL_THRESHOLD_EXCEEDED,
            severity=PolicySeverity.REQUIRE_APPROVAL,
            is_mandatory=False,
            is_active=True,
            version=1,
            parameters={"threshold_amount": 50000.0},
            description="Requires managerial approval for any individual payment exceeding ₹50,000.",
        ),
        Policy(
            id="POL-009",
            name="Structured Split Payment Evasion Detector",
            rule_type=PolicyRuleType.SPLIT_PAYMENT_DETECTION,
            severity=PolicySeverity.REQUIRE_APPROVAL,
            is_mandatory=False,
            is_active=True,
            version=1,
            parameters={"window_days": 3, "threshold_amount": 50000.0},
            description="Detects multiple sub-threshold transactions to the same beneficiary totaling above the threshold.",
        ),
        Policy(
            id="POL-010",
            name="Disbursement Schedule Compliance",
            rule_type=PolicyRuleType.PAYMENT_DATE_SCHEDULING,
            severity=PolicySeverity.WARN,
            is_mandatory=False,
            is_active=True,
            version=1,
            parameters={"allow_past_dates": False, "allow_weekends": False, "max_advance_days": 60},
            description="Flags transactions scheduled in the past, on weekend banking holidays, or too far ahead.",
        ),
        Policy(
            id="POL-011",
            name="Stale State Revalidation Guard",
            rule_type=PolicyRuleType.STALE_PROPOSAL,
            severity=PolicySeverity.BLOCK,
            is_mandatory=True,
            is_active=True,
            version=1,
            parameters={},
            description="Blocks commit when the simulated ledger or invoice state changed since simulation preview.",
        ),
        Policy(
            id="POL-012",
            name="Post-Approval Tamper Protection",
            rule_type=PolicyRuleType.MODIFIED_AFTER_APPROVAL,
            severity=PolicySeverity.BLOCK,
            is_mandatory=True,
            is_active=True,
            version=1,
            parameters={},
            description="Invalidates approvals immediately if proposal payload or transactions are modified.",
        ),
        Policy(
            id="POL-013",
            name="Mandatory Authorization Enforcement",
            rule_type=PolicyRuleType.UNAUTHORIZED_COMMIT_ATTEMPT,
            severity=PolicySeverity.BLOCK,
            is_mandatory=True,
            is_active=True,
            version=1,
            parameters={},
            description="Rejects any attempt to commit a proposal requiring approval without valid authorized sign-off.",
        ),
        Policy(
            id="POL-014",
            name="Active Policy Version Consistency",
            rule_type=PolicyRuleType.POLICY_CHANGED_SINCE_PREVIEW,
            severity=PolicySeverity.BLOCK,
            is_mandatory=True,
            is_active=True,
            version=1,
            parameters={},
            description="Prevents commit if policies were edited or reconfigured between preview and execution.",
        ),
        Policy(
            id="POL-015",
            name="Anomalous & High-Risk Payee Surveillance",
            rule_type=PolicyRuleType.UNUSUAL_PAYMENT_ACTIVITY,
            severity=PolicySeverity.WARN,
            is_mandatory=False,
            is_active=True,
            version=1,
            parameters={"high_risk_tier_flag": True, "unusual_amount_multiplier": 2.5},
            description="Warns when payments involve high-risk vendors or exceed 2.5x historical benchmark amounts.",
        ),
    ]
    for pol in policies:
        pol_repo.upsert(pol)

    # 5. Seed Pre-configured Demo Proposals
    # Only seed if no proposals exist yet
    existing_proposals = prop_repo.list_all()
    if not existing_proposals:
        # A) Safe proposal
        safe_tx = ProposedTransaction(
            id="TX-SAFE-001",
            proposal_id="PROP-DEMO-SAFE-01",
            proposal_version=1,
            transaction_type=TransactionType.SUPPLIER_PAYMENT,
            invoice_id="INV-2026-003",
            supplier_id="SUP-AIRTEL-03",
            beneficiary_name="Bharti Airtel Enterprise Ltd",
            amount=28500.00,
            currency="INR",
            proposed_payment_date=today + timedelta(days=2),
            transaction_category="Telecom & Connectivity",
            description="Primary Leased Line Monthly Settlement",
            status="PROPOSED",
        )
        safe_prop = Proposal(
            id="PROP-DEMO-SAFE-01",
            proposal_type=ProposalType.SUPPLIER_INVOICE,
            title="Airtel Leased Line Monthly Settlement",
            description="Routine telecom billing settlement for headquarters internet link.",
            source="MANUAL_ENTRY",
            account_id="ACC-HDFC-MAIN",
            total_amount=28500.00,
            currency="INR",
            status=ProposalStatus.DRAFT,
            version=1,
            created_by="finance_analyst",
            created_at=datetime.utcnow() - timedelta(hours=2),
            updated_at=datetime.utcnow() - timedelta(hours=2),
            transactions=[safe_tx],
        )
        prop_repo.create(safe_prop)

        # B) Proposal requiring manager approval (> ₹50,000 threshold)
        high_tx = ProposedTransaction(
            id="TX-HIGH-001",
            proposal_id="PROP-DEMO-HIGH-02",
            proposal_version=1,
            transaction_type=TransactionType.SUPPLIER_PAYMENT,
            invoice_id="INV-2026-001",
            supplier_id="SUP-TCS-01",
            beneficiary_name="Tata Consultancy Services Ltd",
            amount=185000.00,
            currency="INR",
            proposed_payment_date=today + timedelta(days=3),
            transaction_category="Cloud & IT Services",
            description="Enterprise Cloud Migration Milestone 1 Settlement",
            status="PROPOSED",
        )
        high_prop = Proposal(
            id="PROP-DEMO-HIGH-02",
            proposal_type=ProposalType.SUPPLIER_INVOICE,
            title="TCS Enterprise Cloud Migration - Milestone 1",
            description="Major infrastructure migration installment requiring executive sign-off.",
            source="AI_AGENT",
            account_id="ACC-HDFC-MAIN",
            total_amount=185000.00,
            currency="INR",
            status=ProposalStatus.DRAFT,
            version=1,
            created_by="ai_payment_agent",
            created_at=datetime.utcnow() - timedelta(hours=1),
            updated_at=datetime.utcnow() - timedelta(hours=1),
            transactions=[high_tx],
        )
        prop_repo.create(high_prop)

        # C) Risky Batch Proposal (Intentionally triggering multiple policies for demonstration)
        risky_tx1 = ProposedTransaction(
            id="TX-RISK-001",
            proposal_id="PROP-DEMO-RISKY-03",
            proposal_version=1,
            transaction_type=TransactionType.SUPPLIER_PAYMENT,
            invoice_id="INV-2026-005",  # Cancelled invoice!
            supplier_id="SUP-APEX-04",  # Suspended supplier!
            beneficiary_name="Apex Facilities & Logistics Pvt Ltd",
            amount=12000.00,
            currency="INR",
            proposed_payment_date=today + timedelta(days=1),
            transaction_category="Office Maintenance",
            description="Cleaning fee for cancelled facility contract",
            status="PROPOSED",
        )
        risky_tx2 = ProposedTransaction(
            id="TX-RISK-002",
            proposal_id="PROP-DEMO-RISKY-03",
            proposal_version=1,
            transaction_type=TransactionType.SUPPLIER_PAYMENT,
            invoice_id="INV-2026-004",  # Already paid invoice!
            supplier_id="SUP-AIRTEL-03",
            beneficiary_name="Bharti Airtel Enterprise Ltd",
            amount=32000.00,
            currency="INR",
            proposed_payment_date=today + timedelta(days=1),
            transaction_category="Telecom",
            description="Duplicate attempt on microwave bandwidth invoice",
            status="PROPOSED",
        )
        risky_prop = Proposal(
            id="PROP-DEMO-RISKY-03",
            proposal_type=ProposalType.PAYMENT_BATCH,
            title="High-Risk Multi-Vendor Batch [Demo Safety Barriers]",
            description="Demonstrates automated detection of cancelled contracts, suspended vendors, and duplicate payments.",
            source="AI_AGENT",
            account_id="ACC-ICICI-EXP",
            total_amount=44000.00,
            currency="INR",
            status=ProposalStatus.DRAFT,
            version=1,
            created_by="ai_payment_agent",
            created_at=datetime.utcnow() - timedelta(minutes=30),
            updated_at=datetime.utcnow() - timedelta(minutes=30),
            transactions=[risky_tx1, risky_tx2],
        )
        prop_repo.create(risky_prop)
