"""
Audit event model.
Captures complete trail of pre-execution governance without storing credentials or secrets.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    PROPOSAL_CREATED = "PROPOSAL_CREATED"
    PROPOSAL_VALIDATION_FAILED = "PROPOSAL_VALIDATION_FAILED"
    SIMULATION_GENERATED = "SIMULATION_GENERATED"
    POLICY_VIOLATION_DETECTED = "POLICY_VIOLATION_DETECTED"
    APPROVAL_REQUESTED = "APPROVAL_REQUESTED"
    APPROVAL_GRANTED = "APPROVAL_GRANTED"
    APPROVAL_REJECTED = "APPROVAL_REJECTED"
    PROPOSAL_MODIFIED = "PROPOSAL_MODIFIED"
    REVALIDATION_FAILED = "REVALIDATION_FAILED"
    SIMULATED_COMMIT_SUCCEEDED = "SIMULATED_COMMIT_SUCCEEDED"
    POLICY_CREATED = "POLICY_CREATED"
    POLICY_EDITED = "POLICY_EDITED"
    POLICY_ACTIVATED = "POLICY_ACTIVATED"
    POLICY_DEACTIVATED = "POLICY_DEACTIVATED"


class AuditEvent(BaseModel):
    id: str = Field(..., description="Unique audit event ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: AuditEventType
    proposal_id: Optional[str] = None
    actor: str = Field(default="system")
    outcome: str = Field(default="SUCCESS")  # SUCCESS, BLOCKED, REJECTED, WARNING, FAILED
    details: Dict[str, Any] = Field(default_factory=dict)
