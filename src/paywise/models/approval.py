"""
Approval data model.
Cryptographically binds approval decisions to explicit proposal, preview, ledger, and policy hashes.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ApprovalDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApproverRole(str, Enum):
    BUSINESS_USER = "BUSINESS_USER"
    FINANCE_MANAGER = "FINANCE_MANAGER"
    CFO = "CFO"
    TREASURY_HEAD = "TREASURY_HEAD"


class ApprovalCreate(BaseModel):
    proposal_id: str
    preview_id: str
    approver_id: str
    approver_name: str
    approver_role: ApproverRole = ApproverRole.FINANCE_MANAGER
    decision: ApprovalDecision = ApprovalDecision.APPROVED
    justification: str = Field(..., min_length=3, description="Audit justification for financial action sign-off")


class Approval(BaseModel):
    id: str = Field(..., description="Approval record ID, e.g. APP-2026-001")
    proposal_id: str
    proposal_version: int
    proposal_hash: str
    preview_id: str
    preview_hash: str
    ledger_state_hash: str
    policy_set_hash: str
    approver_id: str
    approver_name: str
    approver_role: str
    decision: ApprovalDecision
    justification: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_valid: bool = True
