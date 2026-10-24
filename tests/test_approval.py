"""
Tests for Approval workflow, cryptographic binding, and post-approval modification invalidation.
"""
from datetime import date, timedelta
import pytest
from paywise.models.approval import ApprovalCreate, ApprovalDecision, ApproverRole
from paywise.models.proposal import ProposalCreate, ProposalStatus, ProposalType, ProposedTransaction, TransactionType


def test_approval_binding_and_grant(proposal_service, approval_service):
    """Scenario: Approval binds hashes and updates proposal status to APPROVED."""
    prop_create = ProposalCreate(
        title="Manager Approval Payout",
        proposal_type=ProposalType.SUPPLIER_INVOICE,
        account_id="ACC-HDFC-MAIN",
        transactions=[
            ProposedTransaction(
                id="TX-APP-01",
                transaction_type=TransactionType.SUPPLIER_PAYMENT,
                invoice_id="INV-2026-007",
                supplier_id="SUP-TCS-01",
                beneficiary_name="Tata Consultancy Services Ltd",
                amount=95000.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="High value cybersecurity retainer",
            )
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    preview = proposal_service.run_simulation(prop.id)
    assert preview.requires_approval is True

    # Grant approval
    app_create = ApprovalCreate(
        proposal_id=prop.id,
        preview_id=preview.id,
        approver_id="USR-CFO-01",
        approver_name="Ananya Sharma",
        approver_role=ApproverRole.FINANCE_MANAGER,
        decision=ApprovalDecision.APPROVED,
        justification="Verified invoice milestone completion with IT security head.",
    )
    approval = approval_service.process_approval(app_create)

    assert approval.is_valid is True
    assert approval.proposal_hash == prop.proposal_hash
    assert approval.ledger_state_hash == preview.ledger_state_hash
    assert approval.policy_set_hash == preview.policy_set_hash

    # Check updated proposal status
    reloaded_prop = proposal_service.proposal_repo.get_by_id(prop.id)
    assert reloaded_prop.status == ProposalStatus.APPROVED


def test_blocked_proposal_cannot_be_approved(proposal_service, approval_service):
    """Requirement: Cannot grant approval to a proposal with active BLOCK findings."""
    # Proposal violating reserve
    prop_create = ProposalCreate(
        title="Illegal Reserve Breaching Proposal",
        proposal_type=ProposalType.PAYMENT_BATCH,
        account_id="ACC-ICICI-EXP",
        transactions=[
            ProposedTransaction(
                id="TX-BLOCKED-APP",
                transaction_type=TransactionType.EXPENSE_REIMBURSEMENT,
                beneficiary_name="Venture Payout",
                amount=700000.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Breaching reserve completely",
            )
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    preview = proposal_service.run_simulation(prop.id)
    assert preview.has_blocking_issues is True

    app_create = ApprovalCreate(
        proposal_id=prop.id,
        preview_id=preview.id,
        approver_id="USR-MGR-01",
        approver_name="Rajiv Menon",
        approver_role=ApproverRole.FINANCE_MANAGER,
        decision=ApprovalDecision.APPROVED,
        justification="Attempting to force approval on blocked proposal",
    )
    with pytest.raises(ValueError, match="Cannot approve a proposal containing unresolved BLOCK"):
        approval_service.process_approval(app_create)


def test_proposal_modification_invalidates_prior_approval(proposal_service, approval_service):
    """Requirement 11 & Section 3.G: Modifying a proposal invalidates previous approval."""
    prop_create = ProposalCreate(
        title="Initial Valid Payout",
        proposal_type=ProposalType.SUPPLIER_INVOICE,
        account_id="ACC-HDFC-MAIN",
        transactions=[
            ProposedTransaction(
                id="TX-MOD-01",
                transaction_type=TransactionType.SUPPLIER_PAYMENT,
                invoice_id="INV-2026-007",
                supplier_id="SUP-TCS-01",
                beneficiary_name="Tata Consultancy Services Ltd",
                amount=95000.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Original description",
            )
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    preview = proposal_service.run_simulation(prop.id)

    app_create = ApprovalCreate(
        proposal_id=prop.id,
        preview_id=preview.id,
        approver_id="USR-MGR-01",
        approver_name="Rajiv Menon",
        approver_role=ApproverRole.FINANCE_MANAGER,
        decision=ApprovalDecision.APPROVED,
        justification="Initial sign-off",
    )
    approval_service.process_approval(app_create)
    assert proposal_service.proposal_repo.get_by_id(prop.id).status == ProposalStatus.APPROVED

    # Now modify the proposal (e.g. increase amount or add transaction)
    prop.transactions[0].amount = 99000.00
    updated_prop = proposal_service.update_proposal(prop)

    # Status must be reset to DRAFT
    assert updated_prop.status == ProposalStatus.DRAFT
    # Approval must be invalidated in repo
    latest_app = approval_service.approval_repo.get_latest_valid_approval(prop.id)
    assert latest_app is None  # no valid approval remains!
