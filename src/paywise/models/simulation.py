"""
Simulation data models.
Represents the deterministic state projection: S' = f(S, A) and policy evaluation: R = g(S, S', A, P).
"""
from datetime import datetime
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from paywise.models.policy import PolicyFinding


class TransactionOutcome(BaseModel):
    transaction_id: str
    amount: float
    currency: str = "INR"
    beneficiary_name: str
    account_id: str
    projected_post_balance: float
    findings: List[PolicyFinding] = Field(default_factory=list)
    status: str = "VALID"  # VALID, BLOCKED, NEEDS_APPROVAL, WARN


class SimulationPreview(BaseModel):
    id: str = Field(..., description="Preview identifier, e.g. SIM-2026-001")
    proposal_id: str
    proposal_version: int
    proposal_hash: str
    ledger_version: int
    ledger_state_hash: str
    policy_version: int = 1
    policy_set_hash: str
    current_balance: float
    projected_balance: float
    reserved_balance: float
    available_balance_before: float
    available_balance_after: float
    total_outflow: float
    remaining_budget: float = 0.0
    findings: List[PolicyFinding] = Field(default_factory=list)
    can_proceed: bool = True
    requires_approval: bool = False
    transaction_outcomes: List[TransactionOutcome] = Field(default_factory=list)
    simulated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def has_blocking_issues(self) -> bool:
        return any(f.severity.value == "BLOCK" for f in self.findings)

    @property
    def has_approval_requirements(self) -> bool:
        return any(f.severity.value == "REQUIRE_APPROVAL" for f in self.findings)

    @property
    def has_warnings(self) -> bool:
        return any(f.severity.value == "WARN" for f in self.findings)
