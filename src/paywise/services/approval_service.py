"""
Approval service for PayWise.
Handles cryptographically bound authorizations and role-aware approval workflows.
"""
import uuid
from datetime import datetime
from paywise.models.approval import Approval, ApprovalCreate, ApprovalDecision
from paywise.models.audit import AuditEventType
from paywise.models.proposal import ProposalStatus
from paywise.repositories.approval_repo import ApprovalRepository
from paywise.repositories.audit_repo import AuditRepository
from paywise.repositories.proposal_repo import ProposalRepository
from paywise.security.hashing import compute_preview_hash


class ApprovalService:
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.approval_repo = ApprovalRepository(db_path)
        self.proposal_repo = ProposalRepository(db_path)
        self.audit_repo = AuditRepository(db_path)

    def process_approval(self, approval_input: ApprovalCreate) -> Approval:
        proposal = self.proposal_repo.get_by_id(approval_input.proposal_id)
        if not proposal:
            raise ValueError(f"Proposal '{approval_input.proposal_id}' not found.")

        preview = self.proposal_repo.get_latest_preview(proposal.id)
        if not preview or preview.id != approval_input.preview_id:
            raise ValueError("No matching simulation preview found for this proposal.")

        # Ensure no active BLOCK findings
        if preview.has_blocking_issues and approval_input.decision == ApprovalDecision.APPROVED:
            raise ValueError(
                "Cannot approve a proposal containing unresolved BLOCK safety policy findings."
            )

        preview_hash = compute_preview_hash(preview.model_dump())
        approval_id = f"APP-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        approval = Approval(
            id=approval_id,
            proposal_id=proposal.id,
            proposal_version=proposal.version,
            proposal_hash=proposal.proposal_hash,
            preview_id=preview.id,
            preview_hash=preview_hash,
            ledger_state_hash=preview.ledger_state_hash,
            policy_set_hash=preview.policy_set_hash,
            approver_id=approval_input.approver_id,
            approver_name=approval_input.approver_name,
            approver_role=approval_input.approver_role.value,
            decision=approval_input.decision,
            justification=approval_input.justification,
            created_at=datetime.utcnow(),
            is_valid=True,
        )

        saved_approval = self.approval_repo.create(approval)

        if approval_input.decision == ApprovalDecision.APPROVED:
            self.proposal_repo.update_status(proposal.id, ProposalStatus.APPROVED)
            self.audit_repo.log(
                event_type=AuditEventType.APPROVAL_GRANTED,
                actor=approval.approver_name,
                proposal_id=proposal.id,
                outcome="SUCCESS",
                details={
                    "approval_id": approval.id,
                    "approver_role": approval.approver_role,
                    "justification": approval.justification,
                    "proposal_version": proposal.version,
                },
            )
        else:
            self.proposal_repo.update_status(proposal.id, ProposalStatus.REJECTED)
            self.audit_repo.log(
                event_type=AuditEventType.APPROVAL_REJECTED,
                actor=approval.approver_name,
                proposal_id=proposal.id,
                outcome="REJECTED",
                details={
                    "approval_id": approval.id,
                    "approver_role": approval.approver_role,
                    "justification": approval.justification,
                },
            )

        return saved_approval
