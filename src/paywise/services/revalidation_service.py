"""
Commit-Time Revalidation Service for PayWise.
Performs rigorous pre-commit verification to prevent stale execution, post-approval tampering,
or race conditions.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from paywise.engines.policy_engine import PolicyEngine
from paywise.engines.simulation_engine import SimulationEngine
from paywise.models.approval import Approval, ApprovalDecision
from paywise.models.audit import AuditEventType
from paywise.models.policy import PolicyFinding
from paywise.models.proposal import Proposal, ProposalStatus
from paywise.models.simulation import SimulationPreview
from paywise.repositories.account_repo import AccountRepository
from paywise.repositories.approval_repo import ApprovalRepository
from paywise.repositories.audit_repo import AuditRepository
from paywise.repositories.invoice_repo import InvoiceRepository
from paywise.repositories.policy_repo import PolicyRepository
from paywise.repositories.proposal_repo import ProposalRepository
from paywise.repositories.supplier_repo import SupplierRepository
from paywise.security.hashing import (
    compute_ledger_state_hash,
    compute_policy_set_hash,
    compute_preview_hash,
    compute_proposal_hash,
)


@dataclass
class RevalidationResult:
    is_valid: bool
    proposal: Proposal
    preview: SimulationPreview
    approval: Optional[Approval]
    findings: List[PolicyFinding] = field(default_factory=list)
    failure_reasons: List[str] = field(default_factory=list)


class RevalidationService:
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.proposal_repo = ProposalRepository(db_path)
        self.account_repo = AccountRepository(db_path)
        self.supplier_repo = SupplierRepository(db_path)
        self.invoice_repo = InvoiceRepository(db_path)
        self.policy_repo = PolicyRepository(db_path)
        self.approval_repo = ApprovalRepository(db_path)
        self.audit_repo = AuditRepository(db_path)
        self.sim_engine = SimulationEngine()
        self.policy_engine = PolicyEngine()

    def revalidate(self, proposal_id: str, actor: str = "commit_gateway") -> RevalidationResult:
        """
        Executes complete 10-step commit-time revalidation.
        """
        # Step 1: Reload proposal
        proposal = self.proposal_repo.get_by_id(proposal_id)
        if not proposal:
            return RevalidationResult(
                is_valid=False,
                proposal=None,
                preview=None,
                approval=None,
                failure_reasons=[f"Proposal '{proposal_id}' does not exist."],
            )

        # Step 2: Reload latest ledger state (Account)
        account = self.account_repo.get_by_id(proposal.account_id)
        if not account:
            return RevalidationResult(
                is_valid=False,
                proposal=proposal,
                preview=None,
                approval=None,
                failure_reasons=[f"Account '{proposal.account_id}' does not exist."],
            )

        # Step 3: Reload suppliers and invoices
        all_suppliers = {s.id: s for s in self.supplier_repo.list_all()}
        all_invoices = {inv.id: inv for inv in self.invoice_repo.list_all()}

        # Step 4: Reload latest active policies
        active_policies = self.policy_repo.list_active()
        active_policy_dicts = [p.model_dump() for p in active_policies]

        # Step 5: Confirm proposal is unchanged
        tx_dicts = [t.model_dump() for t in proposal.transactions]
        current_proposal_hash = compute_proposal_hash(
            proposal.id, proposal.version, proposal.account_id, tx_dicts
        )
        if current_proposal_hash != proposal.proposal_hash:
            self._fail_revalidation(proposal.id, actor, "Proposal hash mismatch; data tampered.")
            return RevalidationResult(
                is_valid=False,
                proposal=proposal,
                preview=None,
                approval=None,
                failure_reasons=["Proposal payload hash mismatch: transactions or amounts were altered."],
            )

        # Step 6: Re-run simulation against fresh state
        preview = self.sim_engine.simulate(
            account=account,
            proposal=proposal,
            invoices=all_invoices,
            active_policies=active_policy_dicts,
        )

        # Step 7: Load approval if required
        approval = self.approval_repo.get_latest_valid_approval(proposal.id)

        # Step 8: Re-run policy engine with commit-time flags
        findings = self.policy_engine.evaluate(
            account=account,
            preview=preview,
            proposal=proposal,
            policies=active_policies,
            suppliers=all_suppliers,
            invoices=all_invoices,
            existing_approval=approval,
            is_commit_check=True,
        )
        preview.findings = findings

        failure_reasons = []

        # Check for any BLOCK findings
        blocking_findings = [f for f in findings if f.severity.value == "BLOCK"]
        if blocking_findings:
            for bf in blocking_findings:
                failure_reasons.append(f"[{bf.rule_name}] {bf.explanation}")

        # Check proposal status
        if proposal.status == ProposalStatus.REJECTED:
            failure_reasons.append(f"Proposal '{proposal.id}' has been marked as REJECTED and cannot be committed.")

        # Check approval requirement
        needs_approval = any(f.severity.value == "REQUIRE_APPROVAL" for f in findings) or preview.requires_approval
        if needs_approval:
            if not approval or not approval.is_valid:
                failure_reasons.append("Proposal requires explicit manager approval before commit, but no valid approval exists.")
            elif approval.decision != ApprovalDecision.APPROVED:
                failure_reasons.append("Approval was rejected; cannot commit a rejected proposal.")
            elif approval.proposal_hash != current_proposal_hash:
                failure_reasons.append("Approved proposal hash does not match current proposal state.")
            elif approval.ledger_state_hash != preview.ledger_state_hash:
                failure_reasons.append("Ledger balance or invoice status changed since approval (stale state).")
            elif approval.policy_set_hash != preview.policy_set_hash:
                failure_reasons.append("Active policy rules or thresholds changed since approval.")

        is_valid = len(failure_reasons) == 0

        if not is_valid:
            self._fail_revalidation(proposal.id, actor, "; ".join(failure_reasons))
            # Set proposal status to STALE or BLOCKED
            new_status = ProposalStatus.BLOCKED if blocking_findings else ProposalStatus.STALE
            self.proposal_repo.update_status(proposal.id, new_status)
            proposal.status = new_status

        return RevalidationResult(
            is_valid=is_valid,
            proposal=proposal,
            preview=preview,
            approval=approval,
            findings=findings,
            failure_reasons=failure_reasons,
        )

    def _fail_revalidation(self, proposal_id: str, actor: str, reason: str):
        self.audit_repo.log(
            event_type=AuditEventType.REVALIDATION_FAILED,
            actor=actor,
            proposal_id=proposal_id,
            outcome="FAILED",
            details={"revalidation_failure": reason},
        )
