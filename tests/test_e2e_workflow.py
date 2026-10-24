"""
End-to-End Workflow & Integration Tests for PayWise.
Tests the entire lifecycle across UI/Service/Engine/Database/Audit boundaries.
"""
from datetime import date, timedelta
import pytest
from paywise.models.approval import ApprovalCreate, ApprovalDecision, ApproverRole
from paywise.models.audit import AuditEventType
from paywise.models.invoice import InvoiceStatus
from paywise.models.proposal import ProposalStatus
from paywise.services.ai_adapter import AIAdapter
from paywise.services.commit_service import CommitError


def test_full_agent_to_commit_e2e_journey(
    proposal_service, approval_service, commit_service, account_repo, invoice_repo, supplier_repo
):
    """
    End-to-end happy path:
    Natural language request -> AI agent draft -> Validation -> Simulation ->
    Approval -> Commit-Time Revalidation -> Atomic Commit -> Ledger Update.
    """
    ai_adapter = AIAdapter(api_key="")
    suppliers = [s.model_dump() for s in supplier_repo.list_all()]
    invoices = [i.model_dump() for i in invoice_repo.list_all()]

    # 1. Agent drafts proposal from natural language
    candidate = ai_adapter.generate_proposal_from_prompt(
        prompt="Prepare payment for TCS Cloud Migration invoice INV-2026-001 totaling ₹185,000",
        account_id="ACC-HDFC-MAIN",
        available_suppliers=suppliers,
        available_invoices=invoices,
    )
    assert candidate.source == "DETERMINISTIC_FALLBACK"

    # 2. Intake and Validation
    proposal = proposal_service.create_proposal(candidate)
    assert proposal.status == ProposalStatus.DRAFT
    assert proposal.total_amount == 185000.0

    # 3. Deterministic Simulation & Policy Evaluation
    preview = proposal_service.run_simulation(proposal.id)
    assert preview.can_proceed is True
    assert preview.requires_approval is True  # > 50,000 INR threshold
    assert proposal_service.proposal_repo.get_by_id(proposal.id).status == ProposalStatus.AWAITING_APPROVAL

    # 4. Role-Aware Cryptographic Approval
    app_create = ApprovalCreate(
        proposal_id=proposal.id,
        preview_id=preview.id,
        approver_id="USR-CFO-01",
        approver_name="Ananya Sharma",
        approver_role=ApproverRole.CFO,
        decision=ApprovalDecision.APPROVED,
        justification="Verified invoice completion certificate with DevOps team.",
    )
    approval = approval_service.process_approval(app_create)
    assert approval.is_valid is True
    assert proposal_service.proposal_repo.get_by_id(proposal.id).status == ProposalStatus.APPROVED

    # 5. Commit-Time Revalidation & Atomic Execution
    account_before = account_repo.get_by_id("ACC-HDFC-MAIN")
    commit_res = commit_service.commit_proposal(proposal.id, actor="finance_cfo")

    assert commit_res["success"] is True
    assert commit_res["post_balance"] == account_before.current_balance - 185000.0

    # 6. Verify Ledger & Invoice Updates
    account_after = account_repo.get_by_id("ACC-HDFC-MAIN")
    assert account_after.current_balance == account_before.current_balance - 185000.0
    assert account_after.version == account_before.version + 1

    inv_after = invoice_repo.get_by_id("INV-2026-001")
    assert inv_after.status == InvoiceStatus.PAID

    final_prop = proposal_service.proposal_repo.get_by_id(proposal.id)
    assert final_prop.status == ProposalStatus.COMMITTED_SIMULATED


def test_audit_trail_records_lifecycle_events(
    proposal_service, approval_service, commit_service, account_repo
):
    """Scenario 22: Audit trail records complete immutable event lifecycle."""
    prop = proposal_service.create_proposal(
        proposal_service.ai_adapter.generate_proposal_from_prompt(
            prompt="Routine Airtel payout of ₹28,500 under INV-2026-003",
            account_id="ACC-HDFC-MAIN",
            available_suppliers=[{"id": "SUP-AIRTEL-03", "name": "Bharti Airtel Enterprise Ltd"}],
            available_invoices=[{"id": "INV-2026-003", "invoice_number": "AIRTEL-901", "amount": 28500.0}],
        )
    )
    proposal_service.run_simulation(prop.id)
    commit_service.commit_proposal(prop.id, actor="auditor_test")

    events = proposal_service.audit_repo.list_all(proposal_id=prop.id)
    event_types = [e.event_type.value for e in events]

    assert "PROPOSAL_CREATED" in event_types
    assert "SIMULATION_GENERATED" in event_types
    assert "SIMULATED_COMMIT_SUCCEEDED" in event_types


def test_business_user_cannot_bypass_approval_rule(proposal_service, commit_service):
    """Scenario 21: A proposal requiring approval cannot be committed by a user without valid approval."""
    # Proposal of 95,000 exceeds the 50,000 approval threshold
    prop = proposal_service.create_proposal(
        proposal_service.ai_adapter.generate_proposal_from_prompt(
            prompt="High value payment of ₹95,000 for TCS audit",
            account_id="ACC-HDFC-MAIN",
            available_suppliers=[{"id": "SUP-TCS-01", "name": "Tata Consultancy Services Ltd"}],
            available_invoices=[{"id": "INV-2026-007", "invoice_number": "TCS-199", "amount": 95000.0}],
        )
    )
    proposal_service.run_simulation(prop.id)

    # Attempt commit directly as business_user without approval
    with pytest.raises(CommitError, match="requires explicit manager approval"):
        commit_service.commit_proposal(prop.id, actor="business_user")
