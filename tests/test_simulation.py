"""
Tests for deterministic Simulation Engine and consequence preview calculations.
"""
from datetime import date, timedelta
from paywise.models.proposal import ProposalCreate, ProposalType, ProposedTransaction, TransactionType


def test_simulation_accurate_calculations(proposal_service, account_repo):
    """Scenario: Simulation calculates exact balances and available funds deterministically."""
    account = account_repo.get_by_id("ACC-HDFC-MAIN")
    initial_balance = account.current_balance  # 3,500,000.00
    reserved = account.reserved_balance        # 500,000.00
    avail_before = account.available_funds     # 3,000,000.00

    prop_create = ProposalCreate(
        title="Test Telecom Payout",
        proposal_type=ProposalType.SUPPLIER_INVOICE,
        account_id="ACC-HDFC-MAIN",
        transactions=[
            ProposedTransaction(
                id="TX-TEST-SIM-01",
                transaction_type=TransactionType.SUPPLIER_PAYMENT,
                invoice_id="INV-2026-003",
                supplier_id="SUP-AIRTEL-03",
                beneficiary_name="Bharti Airtel Enterprise Ltd",
                amount=28500.00,
                currency="INR",
                proposed_payment_date=date.today() + timedelta(days=2),
                description="Routine Telecom Settlement",
            )
        ],
    )
    prop = proposal_service.create_proposal(prop_create)
    preview = proposal_service.run_simulation(prop.id)

    assert preview.current_balance == initial_balance
    assert preview.reserved_balance == reserved
    assert preview.available_balance_before == avail_before
    assert preview.total_outflow == 28500.00
    assert preview.projected_balance == initial_balance - 28500.00
    assert preview.available_balance_after == (initial_balance - 28500.00) - reserved
    assert preview.can_proceed is True


def test_simulation_does_not_mutate_persistent_balance(proposal_service, account_repo):
    """Requirement 17: A preview does not mutate persistent balances."""
    account_before = account_repo.get_by_id("ACC-HDFC-MAIN")
    balance_before = account_before.current_balance
    version_before = account_before.version

    # Run preview for an existing proposal
    proposals = proposal_service.proposal_repo.list_all()
    assert len(proposals) > 0
    preview = proposal_service.run_simulation(proposals[0].id)

    account_after = account_repo.get_by_id("ACC-HDFC-MAIN")
    assert account_after.current_balance == balance_before
    assert account_after.version == version_before
