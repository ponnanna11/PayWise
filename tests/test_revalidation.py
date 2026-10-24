"""
Tests for Commit-Time Revalidation and stale-state protection.
"""
from datetime import date, timedelta
from paywise.models.approval import ApprovalCreate, ApprovalDecision, ApproverRole
from paywise.models.proposal import ProposalCreate, ProposalType, ProposedTransaction, TransactionType


def test_ledger_change_after_preview_triggers_revalidation_failure(
    proposal_service, approval_service, revalidation_service, account_repo
):
    """Requirement 12: A ledger change after preview triggers revalidation failure."""
    prop_create = ProposalCreate(
        title="Revalidation Stale Ledger Test",
        proposal_type=ProposalType.SUPPLIER_INVOICE,
        account_id="ACC-HDFC-MAIN",
        transactions=[
            ProposedTransaction(
                id="TX-REVAL-LEDGER",
                transaction_type=TransactionType.SUPPLIER_PAYMENT,
                invoice_id="INV-2026-007",
                supplier_id="SUP-TCS-01",
                beneficiary_name="Tata Consultancy Services Ltd",
                amount=95000.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Retainer payment",
            )
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    preview = proposal_service.run_simulation(prop.id)

    app_create = ApprovalCreate(
        proposal_id=prop.id,
        preview_id=preview.id,
        approver_id="USR-CFO-01",
        approver_name="Ananya Sharma",
        approver_role=ApproverRole.CFO,
        decision=ApprovalDecision.APPROVED,
        justification="Approved for release",
    )
    approval_service.process_approval(app_create)

    # Now mutate the ledger in persistent storage (e.g., account balance changed by another transaction)
    acc = account_repo.get_by_id("ACC-HDFC-MAIN")
    account_repo.update_balance(
        account_id=acc.id,
        new_balance=acc.current_balance - 50000.0,
        expected_version=acc.version,
    )

    # Attempt revalidation
    reval = revalidation_service.revalidate(prop.id)
    assert reval.is_valid is False
    assert any("stale" in reason.lower() or "changed" in reason.lower() for reason in reval.failure_reasons)


def test_policy_change_after_preview_triggers_revalidation(
    proposal_service, approval_service, revalidation_service, policy_repo
):
    """Requirement 13: A policy change after preview triggers revalidation."""
    prop_create = ProposalCreate(
        title="Revalidation Policy Change Test",
        proposal_type=ProposalType.SUPPLIER_INVOICE,
        account_id="ACC-HDFC-MAIN",
        transactions=[
            ProposedTransaction(
                id="TX-REVAL-POL",
                transaction_type=TransactionType.SUPPLIER_PAYMENT,
                invoice_id="INV-2026-007",
                supplier_id="SUP-TCS-01",
                beneficiary_name="Tata Consultancy Services Ltd",
                amount=95000.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Consultancy milestone",
            )
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    preview = proposal_service.run_simulation(prop.id)

    app_create = ApprovalCreate(
        proposal_id=prop.id,
        preview_id=preview.id,
        approver_id="USR-CFO-01",
        approver_name="Ananya Sharma",
        approver_role=ApproverRole.CFO,
        decision=ApprovalDecision.APPROVED,
        justification="Pre-approved under previous policies",
    )
    approval_service.process_approval(app_create)

    # Now modify an active policy (e.g., toggle or update POL-007)
    pol = policy_repo.get_by_id("POL-007")
    pol.parameters["max_batch_amount"] = 300000.0  # changed parameter
    policy_repo.upsert(pol)

    reval = revalidation_service.revalidate(prop.id)
    assert reval.is_valid is False
    assert any("policy" in reason.lower() for reason in reval.failure_reasons)


def test_commit_without_required_approval_rejected(proposal_service, revalidation_service):
    """Requirement 14: A commit attempt without required approval is rejected."""
    # Proposal > 50,000 threshold requires approval
    prop_create = ProposalCreate(
        title="Unapproved High Value Payment",
        proposal_type=ProposalType.SUPPLIER_INVOICE,
        account_id="ACC-HDFC-MAIN",
        transactions=[
            ProposedTransaction(
                id="TX-NO-APP",
                transaction_type=TransactionType.SUPPLIER_PAYMENT,
                invoice_id="INV-2026-007",
                supplier_id="SUP-TCS-01",
                beneficiary_name="Tata Consultancy Services Ltd",
                amount=95000.00,
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Unapproved payment attempt",
            )
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    proposal_service.run_simulation(prop.id)

    # Do NOT approve! Attempt revalidation directly:
    reval = revalidation_service.revalidate(prop.id)
    assert reval.is_valid is False
    assert any("requires explicit manager approval" in reason for reason in reval.failure_reasons)
