"""
Tests for deterministic Policy Engine rules and safety boundary enforcement.
"""
from datetime import date, timedelta
import pytest
from pydantic import ValidationError
from paywise.models.proposal import ProposalCreate, ProposalType, ProposedTransaction, TransactionType


def test_safe_payment_batch_succeeds(proposal_service):
    """Requirement 1: A safe payment batch succeeds without blocking."""
    prop_create = ProposalCreate(
        title="Safe Telecom Payment",
        proposal_type=ProposalType.SUPPLIER_INVOICE,
        account_id="ACC-HDFC-MAIN",
        transactions=[
            ProposedTransaction(
                id="TX-SAFE-P1",
                transaction_type=TransactionType.SUPPLIER_PAYMENT,
                invoice_id="INV-2026-003",
                supplier_id="SUP-AIRTEL-03",
                beneficiary_name="Bharti Airtel Enterprise Ltd",
                amount=28500.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Routine Telecom Settlement",
            )
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    preview = proposal_service.run_simulation(prop.id)

    assert preview.can_proceed is True
    assert preview.has_blocking_issues is False
    assert preview.requires_approval is False


def test_minimum_reserve_breach_blocked(proposal_service):
    """Requirement 2: A payment that breaches the reserve requirement is blocked."""
    # ACC-ICICI-EXP balance: 750,000, reserved: 150,000.
    # A payment of 650,000 leaves balance 100,000 (< 150,000 reserve).
    prop_create = ProposalCreate(
        title="Reserve Breaching Payment",
        proposal_type=ProposalType.PAYMENT_BATCH,
        account_id="ACC-ICICI-EXP",
        transactions=[
            ProposedTransaction(
                id="TX-RES-01",
                transaction_type=TransactionType.EXPENSE_REIMBURSEMENT,
                beneficiary_name="Corporate Expansion Fund",
                amount=650000.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Excessive Withdrawal Breaching Reserve",
            )
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    preview = proposal_service.run_simulation(prop.id)

    assert preview.can_proceed is False
    assert preview.has_blocking_issues is True
    findings = [f for f in preview.findings if f.policy_id == "POL-002"]
    assert len(findings) == 1
    assert "breach mandatory safety reserve" in findings[0].explanation


def test_duplicate_invoice_payment_blocked(proposal_service):
    """Requirement 3: A duplicate invoice payment is blocked."""
    prop_create = ProposalCreate(
        title="Duplicate Invoice Batch",
        proposal_type=ProposalType.PAYMENT_BATCH,
        account_id="ACC-HDFC-MAIN",
        transactions=[
            ProposedTransaction(
                id="TX-DUP-01",
                transaction_type=TransactionType.SUPPLIER_PAYMENT,
                invoice_id="INV-2026-003",
                supplier_id="SUP-AIRTEL-03",
                beneficiary_name="Bharti Airtel Enterprise Ltd",
                amount=28500.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="First payment attempt",
            ),
            ProposedTransaction(
                id="TX-DUP-02",
                transaction_type=TransactionType.SUPPLIER_PAYMENT,
                invoice_id="INV-2026-003",  # Same invoice!
                supplier_id="SUP-AIRTEL-03",
                beneficiary_name="Bharti Airtel Enterprise Ltd",
                amount=28500.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Accidental duplicate attempt",
            ),
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    preview = proposal_service.run_simulation(prop.id)

    assert preview.can_proceed is False
    dup_findings = [f for f in preview.findings if f.policy_id == "POL-003"]
    assert len(dup_findings) == 1
    assert "Multiple proposed transactions" in dup_findings[0].explanation


def test_cancelled_or_paid_invoice_blocked(proposal_service):
    """Requirement 4: A payment against a cancelled or already-paid invoice is blocked."""
    # INV-2026-005 is CANCELLED in seed data
    prop_create = ProposalCreate(
        title="Payment on Cancelled Invoice",
        proposal_type=ProposalType.SUPPLIER_INVOICE,
        account_id="ACC-HDFC-MAIN",
        transactions=[
            ProposedTransaction(
                id="TX-CANC-01",
                transaction_type=TransactionType.SUPPLIER_PAYMENT,
                invoice_id="INV-2026-005",
                supplier_id="SUP-APEX-04",
                beneficiary_name="Apex Facilities & Logistics Pvt Ltd",
                amount=12000.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Payment attempt on cancelled contract",
            )
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    preview = proposal_service.run_simulation(prop.id)

    assert preview.can_proceed is False
    canc_findings = [f for f in preview.findings if f.policy_id == "POL-004"]
    assert len(canc_findings) == 1
    assert "CANCELLED" in canc_findings[0].explanation


def test_unapproved_supplier_blocked(proposal_service):
    """Requirement 5: An unapproved supplier is blocked or routed according to policy."""
    # SUP-APEX-04 has status SUSPENDED
    prop_create = ProposalCreate(
        title="Payment to Suspended Vendor",
        proposal_type=ProposalType.SUPPLIER_INVOICE,
        account_id="ACC-HDFC-MAIN",
        transactions=[
            ProposedTransaction(
                id="TX-UNAPP-01",
                transaction_type=TransactionType.SUPPLIER_PAYMENT,
                supplier_id="SUP-APEX-04",
                beneficiary_name="Apex Facilities & Logistics Pvt Ltd",
                amount=10000.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Payment to suspended vendor",
            )
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    preview = proposal_service.run_simulation(prop.id)

    assert preview.can_proceed is False
    sup_findings = [f for f in preview.findings if f.policy_id == "POL-005"]
    assert len(sup_findings) == 1
    assert "unapproved status: 'SUSPENDED'" in sup_findings[0].explanation


def test_amount_mismatch_detected(proposal_service):
    """Requirement 6: A payment amount mismatch is detected."""
    # INV-2026-003 amount is 28,500.00. We propose 28,000.00.
    prop_create = ProposalCreate(
        title="Amount Mismatch Proposal",
        proposal_type=ProposalType.SUPPLIER_INVOICE,
        account_id="ACC-HDFC-MAIN",
        transactions=[
            ProposedTransaction(
                id="TX-MISMATCH-01",
                transaction_type=TransactionType.SUPPLIER_PAYMENT,
                invoice_id="INV-2026-003",
                supplier_id="SUP-AIRTEL-03",
                beneficiary_name="Bharti Airtel Enterprise Ltd",
                amount=28000.00,  # 500 less than invoice
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Underpaid invoice test",
            )
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    preview = proposal_service.run_simulation(prop.id)

    assert preview.can_proceed is False
    mismatch_findings = [f for f in preview.findings if f.policy_id == "POL-006"]
    assert len(mismatch_findings) == 1
    assert "differs from invoice amount" in mismatch_findings[0].explanation


def test_batch_budget_breach_detected(proposal_service):
    """Requirement 7: An aggregate payment batch exceeds its configured budget."""
    # Policy POL-007 max_batch_amount is 500,000. Propose 600,000 on ACC-HDFC-MAIN.
    prop_create = ProposalCreate(
        title="Oversized Payment Batch",
        proposal_type=ProposalType.PAYMENT_BATCH,
        account_id="ACC-HDFC-MAIN",
        transactions=[
            ProposedTransaction(
                id="TX-BATCH-01",
                transaction_type=TransactionType.EXPENSE_REIMBURSEMENT,
                beneficiary_name="Global Vendor Supplies",
                amount=600000.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Large batch exceeding budget ceiling",
            )
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    preview = proposal_service.run_simulation(prop.id)

    assert preview.requires_approval is True
    batch_findings = [f for f in preview.findings if f.policy_id == "POL-007"]
    assert len(batch_findings) == 1
    assert "exceeds configured batch ceiling" in batch_findings[0].explanation


def test_approval_threshold_requires_approval(proposal_service):
    """Requirement 8: An approval-threshold payment requires approval."""
    # POL-008 threshold_amount is 50,000. Propose 95,000 for TCS cybersecurity invoice.
    prop_create = ProposalCreate(
        title="High Value Consultant Payout",
        proposal_type=ProposalType.SUPPLIER_INVOICE,
        account_id="ACC-HDFC-MAIN",
        transactions=[
            ProposedTransaction(
                id="TX-HIGH-P1",
                transaction_type=TransactionType.SUPPLIER_PAYMENT,
                invoice_id="INV-2026-007",
                supplier_id="SUP-TCS-01",
                beneficiary_name="Tata Consultancy Services Ltd",
                amount=95000.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Cybersecurity Red Teaming Settlement",
            )
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    preview = proposal_service.run_simulation(prop.id)

    assert preview.can_proceed is True
    assert preview.requires_approval is True
    thresh_findings = [f for f in preview.findings if f.policy_id == "POL-008"]
    assert len(thresh_findings) == 1
    assert "exceeds individual threshold" in thresh_findings[0].explanation


def test_split_payment_detection(proposal_service):
    """Requirement 9: Related split payments are flagged."""
    # Threshold is 50,000. Two payments of 30,000 each to the same beneficiary total 60,000!
    prop_create = ProposalCreate(
        title="Potential Split Payment Evasion",
        proposal_type=ProposalType.PAYMENT_BATCH,
        account_id="ACC-HDFC-MAIN",
        transactions=[
            ProposedTransaction(
                id="TX-SPLIT-01",
                transaction_type=TransactionType.SUPPLIER_PAYMENT,
                supplier_id="SUP-INFY-02",
                beneficiary_name="Infosys Limited",
                amount=30000.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Split installment 1",
            ),
            ProposedTransaction(
                id="TX-SPLIT-02",
                transaction_type=TransactionType.SUPPLIER_PAYMENT,
                supplier_id="SUP-INFY-02",
                beneficiary_name="Infosys Limited",
                amount=30000.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Split installment 2",
            ),
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    preview = proposal_service.run_simulation(prop.id)

    assert preview.requires_approval is True
    split_findings = [f for f in preview.findings if f.policy_id == "POL-009"]
    assert len(split_findings) == 1
    assert "potential split payment" in split_findings[0].explanation


def test_invalid_proposal_fails_validation():
    """Requirement 10: An invalid proposal fails validation."""
    # 1. Negative amount should fail
    with pytest.raises(ValidationError):
        ProposedTransaction(
            id="TX-INVALID-01",
            beneficiary_name="Test Vendor",
            amount=-100.00,
            proposed_payment_date=date.today(),
            description="Negative amount",
        )

    # 2. Unsupported currency should fail
    with pytest.raises(ValidationError):
        ProposedTransaction(
            id="TX-INVALID-02",
            beneficiary_name="Test Vendor",
            amount=100.00,
            currency="XYZ_INVALID",
            proposed_payment_date=date.today(),
            description="Invalid currency",
        )

    # 3. Missing transactions in ProposalCreate should fail
    with pytest.raises(ValidationError):
        ProposalCreate(
            title="Empty proposal",
            account_id="ACC-HDFC-MAIN",
            transactions=[],
        )
