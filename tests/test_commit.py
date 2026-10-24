"""
Tests for atomic simulated commit, idempotency, and failure rollback protection.
"""
from datetime import date, timedelta
import pytest
from paywise.models.approval import ApprovalCreate, ApprovalDecision, ApproverRole
from paywise.models.invoice import InvoiceStatus
from paywise.models.proposal import ProposalCreate, ProposalStatus, ProposalType, ProposedTransaction, TransactionType
from paywise.services.commit_service import CommitError, DuplicateCommitError


def test_successful_simulated_commit_updates_ledger_atomically(
    proposal_service, approval_service, commit_service, account_repo, invoice_repo
):
    """Requirement 18: A successful simulated commit updates the ledger atomically."""
    account_before = account_repo.get_by_id("ACC-HDFC-MAIN")
    initial_balance = account_before.current_balance

    prop_create = ProposalCreate(
        title="Valid Commit Flow Payout",
        proposal_type=ProposalType.SUPPLIER_INVOICE,
        account_id="ACC-HDFC-MAIN",
        transactions=[
            ProposedTransaction(
                id="TX-COMMIT-SUCCESS-01",
                transaction_type=TransactionType.SUPPLIER_PAYMENT,
                invoice_id="INV-2026-003",
                supplier_id="SUP-AIRTEL-03",
                beneficiary_name="Bharti Airtel Enterprise Ltd",
                amount=28500.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Final Telecom Payout",
            )
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    preview = proposal_service.run_simulation(prop.id)
    assert preview.can_proceed is True

    # Commit execution
    result = commit_service.commit_proposal(prop.id, actor="operator_test")
    assert result["success"] is True
    assert result["post_balance"] == initial_balance - 28500.00

    # Verify ledger updated
    account_after = account_repo.get_by_id("ACC-HDFC-MAIN")
    assert account_after.current_balance == initial_balance - 28500.00
    assert account_after.version == account_before.version + 1

    # Verify invoice status updated to PAID
    inv = invoice_repo.get_by_id("INV-2026-003")
    assert inv.status == InvoiceStatus.PAID
    assert inv.paid_transaction_id == "TX-COMMIT-SUCCESS-01"

    # Verify proposal status updated
    final_prop = proposal_service.proposal_repo.get_by_id(prop.id)
    assert final_prop.status == ProposalStatus.COMMITTED_SIMULATED


def test_repeated_commit_request_rejected(
    proposal_service, commit_service
):
    """Requirement 19: A repeated commit request does not apply the payment twice (idempotency)."""
    prop_create = ProposalCreate(
        title="Idempotency Test Proposal",
        proposal_type=ProposalType.SUPPLIER_INVOICE,
        account_id="ACC-HDFC-MAIN",
        transactions=[
            ProposedTransaction(
                id="TX-IDEMP-01",
                transaction_type=TransactionType.SUPPLIER_PAYMENT,
                invoice_id="INV-2026-003",
                supplier_id="SUP-AIRTEL-03",
                beneficiary_name="Bharti Airtel Enterprise Ltd",
                amount=28500.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Idempotent payout",
            )
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    proposal_service.run_simulation(prop.id)

    # First commit succeeds
    result1 = commit_service.commit_proposal(prop.id, actor="operator_test")
    assert result1["success"] is True

    # Second commit must raise DuplicateCommitError
    with pytest.raises(DuplicateCommitError, match="already committed"):
        commit_service.commit_proposal(prop.id, actor="operator_test")


def test_rejected_proposal_does_not_alter_ledger(
    proposal_service, approval_service, commit_service, account_repo
):
    """Requirement 15: A rejected proposal does not alter the ledger."""
    account_before = account_repo.get_by_id("ACC-HDFC-MAIN")
    balance_before = account_before.current_balance

    prop_create = ProposalCreate(
        title="Rejected Payout",
        proposal_type=ProposalType.SUPPLIER_INVOICE,
        account_id="ACC-HDFC-MAIN",
        transactions=[
            ProposedTransaction(
                id="TX-REJ-01",
                transaction_type=TransactionType.SUPPLIER_PAYMENT,
                invoice_id="INV-2026-007",
                supplier_id="SUP-TCS-01",
                beneficiary_name="Tata Consultancy Services Ltd",
                amount=95000.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Consulting invoice",
            )
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    preview = proposal_service.run_simulation(prop.id)

    # Reject proposal
    app_create = ApprovalCreate(
        proposal_id=prop.id,
        preview_id=preview.id,
        approver_id="USR-CFO-01",
        approver_name="Ananya Sharma",
        approver_role=ApproverRole.CFO,
        decision=ApprovalDecision.REJECTED,
        justification="Budget frozen for Q3.",
    )
    approval_service.process_approval(app_create)

    # Attempt commit should fail
    with pytest.raises(CommitError):
        commit_service.commit_proposal(prop.id)

    account_after = account_repo.get_by_id("ACC-HDFC-MAIN")
    assert account_after.current_balance == balance_before


def test_blocked_proposal_does_not_alter_ledger(
    proposal_service, commit_service, account_repo
):
    """Requirement 16: A blocked proposal does not alter the ledger."""
    account_before = account_repo.get_by_id("ACC-ICICI-EXP")
    balance_before = account_before.current_balance

    # Blocked by reserve policy
    prop_create = ProposalCreate(
        title="Blocked Reserve Proposal",
        proposal_type=ProposalType.PAYMENT_BATCH,
        account_id="ACC-ICICI-EXP",
        transactions=[
            ProposedTransaction(
                id="TX-BLOCK-COMMIT",
                transaction_type=TransactionType.EXPENSE_REIMBURSEMENT,
                beneficiary_name="Vendor X",
                amount=700000.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Over reserve",
            )
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    proposal_service.run_simulation(prop.id)

    with pytest.raises(CommitError):
        commit_service.commit_proposal(prop.id)

    account_after = account_repo.get_by_id("ACC-ICICI-EXP")
    assert account_after.current_balance == balance_before


def test_invalid_policy_cannot_be_activated(policy_service):
    """Requirement 20: An invalid or unauthorized policy cannot be activated."""
    # Attempting to deactivate a mandatory safety rule (e.g. POL-001) must fail
    with pytest.raises(ValueError, match="mandatory foundational safety guard"):
        policy_service.toggle_activation("POL-001", is_active=False)

    # Validating policy with bad rule_type or missing threshold must fail
    val = policy_service.validate_policy_draft(
        name="Bad Policy",
        rule_type="UNKNOWN_RULE_TYPE",
        severity="BLOCK",
        parameters={},
    )
    assert val["is_valid"] is False
    assert any("Invalid or unsupported rule type" in e for e in val["errors"])
