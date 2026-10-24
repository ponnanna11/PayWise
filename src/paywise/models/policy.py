"""
Policy and PolicyFinding data models.
Defines rule types, severity levels, configuration parameters, and structured violation findings.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PolicySeverity(str, Enum):
    BLOCK = "BLOCK"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    WARN = "WARN"


class PolicyRuleType(str, Enum):
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    MINIMUM_RESERVE_BREACH = "MINIMUM_RESERVE_BREACH"
    DUPLICATE_INVOICE_PAYMENT = "DUPLICATE_INVOICE_PAYMENT"
    CANCELLED_OR_PAID_INVOICE = "CANCELLED_OR_PAID_INVOICE"
    UNAPPROVED_SUPPLIER = "UNAPPROVED_SUPPLIER"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    BATCH_BUDGET_EXCEEDED = "BATCH_BUDGET_EXCEEDED"
    APPROVAL_THRESHOLD_EXCEEDED = "APPROVAL_THRESHOLD_EXCEEDED"
    SPLIT_PAYMENT_DETECTION = "SPLIT_PAYMENT_DETECTION"
    PAYMENT_DATE_SCHEDULING = "PAYMENT_DATE_SCHEDULING"
    STALE_PROPOSAL = "STALE_PROPOSAL"
    MODIFIED_AFTER_APPROVAL = "MODIFIED_AFTER_APPROVAL"
    UNAUTHORIZED_COMMIT_ATTEMPT = "UNAUTHORIZED_COMMIT_ATTEMPT"
    POLICY_CHANGED_SINCE_PREVIEW = "POLICY_CHANGED_SINCE_PREVIEW"
    UNUSUAL_PAYMENT_ACTIVITY = "UNUSUAL_PAYMENT_ACTIVITY"


class PolicyFinding(BaseModel):
    policy_id: str = Field(..., description="ID of the triggering policy")
    rule_name: str = Field(..., description="Human-readable rule name")
    severity: PolicySeverity = Field(..., description="BLOCK, REQUIRE_APPROVAL, or WARN")
    affected_transaction_ids: List[str] = Field(default_factory=list, description="IDs of affected transactions")
    explanation: str = Field(..., description="Clear explanation of the triggered rule")
    relevant_values: Dict[str, Any] = Field(default_factory=dict, description="Contextual financial values")
    recommended_action: str = Field(..., description="Corrective guidance for finance operator")


class Policy(BaseModel):
    id: str = Field(..., description="Unique policy identifier, e.g. POL-001")
    name: str = Field(..., min_length=3, description="Descriptive policy name")
    rule_type: PolicyRuleType = Field(..., description="Associated engine rule type")
    severity: PolicySeverity = Field(default=PolicySeverity.REQUIRE_APPROVAL)
    is_mandatory: bool = Field(default=False, description="True for foundational safety rules, False for tunable business rules")
    is_active: bool = Field(default=True, description="Whether the rule is enforced")
    version: int = Field(default=1, ge=1)
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Configurable threshold parameters")
    description: str = Field(..., description="Summary of policy intent")
    created_by: str = Field(default="system_admin")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
