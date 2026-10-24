"""
Proposal service for PayWise.
Coordinates proposal creation, validation, updating, and simulation preview generation.
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from paywise.engines.policy_engine import PolicyEngine
from paywise.engines.simulation_engine import SimulationEngine
from paywise.models.audit import AuditEventType
from paywise.models.proposal import (
    Proposal,
    ProposalCreate,
    ProposalStatus,
    ProposedTransaction,
)
from paywise.models.simulation import SimulationPreview
from paywise.repositories.account_repo import AccountRepository
from paywise.repositories.approval_repo import ApprovalRepository
from paywise.repositories.audit_repo import AuditRepository
from paywise.repositories.invoice_repo import InvoiceRepository
from paywise.repositories.policy_repo import PolicyRepository
from paywise.repositories.proposal_repo import ProposalRepository
from paywise.repositories.supplier_repo import SupplierRepository
from paywise.services.ai_adapter import AIAdapter


class ProposalService:
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
        self.ai_adapter = AIAdapter()

    def create_proposal(self, proposal_input: ProposalCreate) -> Proposal:
        """
        Validates input schema and creates a new proposal in DRAFT status.
        """
        # Verify account exists
        account = self.account_repo.get_by_id(proposal_input.account_id)
        if not account:
            self.audit_repo.log(
                event_type=AuditEventType.PROPOSAL_VALIDATION_FAILED,
                actor=proposal_input.created_by,
                outcome="FAILED",
                details={"reason": f"Account '{proposal_input.account_id}' does not exist."},
            )
            raise ValueError(f"Disbursement account '{proposal_input.account_id}' does not exist.")

        prop_id = f"PROP-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # Assign proposal_id to transactions if missing
        assigned_txs = []
        for i, tx in enumerate(proposal_input.transactions):
            tx_data = tx.model_dump()
            tx_data["proposal_id"] = prop_id
            tx_data["proposal_version"] = 1
            if not tx_data.get("id"):
                tx_data["id"] = f"TX-{prop_id}-{i+1}"
            assigned_txs.append(ProposedTransaction(**tx_data))

        proposal = Proposal(
            id=prop_id,
            proposal_type=proposal_input.proposal_type,
            title=proposal_input.title,
            description=proposal_input.description,
            source=proposal_input.source,
            account_id=proposal_input.account_id,
            currency=proposal_input.currency,
            status=ProposalStatus.DRAFT,
            version=1,
            created_by=proposal_input.created_by,
            transactions=assigned_txs,
        )

        saved_prop = self.proposal_repo.create(proposal)

        self.audit_repo.log(
            event_type=AuditEventType.PROPOSAL_CREATED,
            actor=proposal.created_by,
            proposal_id=proposal.id,
            outcome="SUCCESS",
            details={
                "proposal_id": proposal.id,
                "type": proposal.proposal_type.value,
                "amount": proposal.total_amount,
                "source": proposal.source,
                "transaction_count": len(proposal.transactions),
            },
        )
        return saved_prop

    def update_proposal(self, proposal: Proposal, actor: str = "finance_analyst") -> Proposal:
        """
        Updates proposal contents, increments version, and invalidates any previous approvals.
        """
        updated = self.proposal_repo.update_proposal(proposal)

        # Invalidate existing approvals as state changed
        invalidated_count = self.approval_repo.invalidate_all_for_proposal(proposal.id)

        # Reset status to DRAFT
        self.proposal_repo.update_status(proposal.id, ProposalStatus.DRAFT)
        updated.status = ProposalStatus.DRAFT

        self.audit_repo.log(
            event_type=AuditEventType.PROPOSAL_MODIFIED,
            actor=actor,
            proposal_id=proposal.id,
            outcome="SUCCESS",
            details={
                "new_version": updated.version,
                "invalidated_approvals": invalidated_count,
                "new_total": updated.total_amount,
            },
        )
        return updated

    def run_simulation(self, proposal_id: str, actor: str = "simulation_engine") -> SimulationPreview:
        """
        Runs deterministic simulation engine and evaluates policies.
        Updates proposal status to SIMULATED, AWAITING_APPROVAL, or BLOCKED.
        """
        proposal = self.proposal_repo.get_by_id(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal '{proposal_id}' not found.")

        account = self.account_repo.get_by_id(proposal.account_id)
        if not account:
            raise ValueError(f"Account '{proposal.account_id}' not found.")

        # Load context
        all_suppliers = {s.id: s for s in self.supplier_repo.list_all()}
        all_invoices = {inv.id: inv for inv in self.invoice_repo.list_all()}
        active_policies = self.policy_repo.list_active()
        active_policy_dicts = [p.model_dump() for p in active_policies]

        # 1. Deterministic simulation
        preview = self.sim_engine.simulate(
            account=account,
            proposal=proposal,
            invoices=all_invoices,
            active_policies=active_policy_dicts,
        )

        # 2. Policy evaluation
        findings = self.policy_engine.evaluate(
            account=account,
            preview=preview,
            proposal=proposal,
            policies=active_policies,
            suppliers=all_suppliers,
            invoices=all_invoices,
            is_commit_check=False,
        )
        preview.findings = findings

        has_block = any(f.severity.value == "BLOCK" for f in findings)
        needs_approval = any(f.severity.value == "REQUIRE_APPROVAL" for f in findings)

        preview.can_proceed = not has_block
        preview.requires_approval = needs_approval

        # Tag transaction outcomes
        for outcome in preview.transaction_outcomes:
            tx_findings = [f for f in findings if outcome.transaction_id in f.affected_transaction_ids]
            outcome.findings = tx_findings
            if any(f.severity.value == "BLOCK" for f in tx_findings):
                outcome.status = "BLOCKED"
            elif any(f.severity.value == "REQUIRE_APPROVAL" for f in tx_findings):
                outcome.status = "NEEDS_APPROVAL"
            elif any(f.severity.value == "WARN" for f in tx_findings):
                outcome.status = "WARN"

        # Save preview
        self.proposal_repo.save_preview(preview)

        # Update proposal status
        if has_block:
            self.proposal_repo.update_status(proposal.id, ProposalStatus.BLOCKED)
            audit_outcome = "BLOCKED"
        elif needs_approval:
            self.proposal_repo.update_status(proposal.id, ProposalStatus.AWAITING_APPROVAL)
            audit_outcome = "WARNING"
        else:
            self.proposal_repo.update_status(proposal.id, ProposalStatus.SIMULATED)
            audit_outcome = "SUCCESS"

        self.audit_repo.log(
            event_type=AuditEventType.SIMULATION_GENERATED,
            actor=actor,
            proposal_id=proposal.id,
            outcome=audit_outcome,
            details={
                "preview_id": preview.id,
                "projected_balance": preview.projected_balance,
                "findings_count": len(findings),
                "has_blocking_issues": has_block,
                "requires_approval": needs_approval,
            },
        )

        if findings:
            for f in findings:
                self.audit_repo.log(
                    event_type=AuditEventType.POLICY_VIOLATION_DETECTED,
                    actor=actor,
                    proposal_id=proposal.id,
                    outcome=f.severity.value,
                    details={
                        "rule_name": f.rule_name,
                        "severity": f.severity.value,
                        "explanation": f.explanation,
                    },
                )

        return preview

    def get_proposal_with_preview(self, proposal_id: str):
        proposal = self.proposal_repo.get_by_id(proposal_id)
        if not proposal:
            return None, None
        preview = self.proposal_repo.get_latest_preview(proposal_id)
        return proposal, preview
