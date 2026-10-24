"""
Policy management service for PayWise.
Handles policy lifecycle, validation, activation, and parameter configuration.
"""
from typing import Any, Dict, List, Optional
from paywise.models.audit import AuditEventType
from paywise.models.policy import Policy, PolicyRuleType, PolicySeverity
from paywise.repositories.audit_repo import AuditRepository
from paywise.repositories.policy_repo import PolicyRepository


class PolicyService:
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.policy_repo = PolicyRepository(db_path)
        self.audit_repo = AuditRepository(db_path)

    def list_policies(self, active_only: bool = False) -> List[Policy]:
        if active_only:
            return self.policy_repo.list_active()
        return self.policy_repo.list_all()

    def get_policy(self, policy_id: str) -> Optional[Policy]:
        return self.policy_repo.get_by_id(policy_id)

    def validate_policy_draft(
        self,
        name: str,
        rule_type: str,
        severity: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validates schema, allowed rule types, supported parameters, and severity.
        Does NOT execute code or SQL.
        """
        errors = []
        if not name or len(name.strip()) < 3:
            errors.append("Policy name must be at least 3 characters.")

        try:
            valid_rule = PolicyRuleType(rule_type)
        except ValueError:
            errors.append(f"Invalid or unsupported rule type: '{rule_type}'.")
            valid_rule = None

        try:
            valid_severity = PolicySeverity(severity)
        except ValueError:
            errors.append(f"Invalid severity level: '{severity}'. Must be BLOCK, REQUIRE_APPROVAL, or WARN.")
            valid_severity = None

        # Validate parameters according to rule
        if valid_rule == PolicyRuleType.APPROVAL_THRESHOLD_EXCEEDED:
            if "threshold_amount" not in parameters or float(parameters["threshold_amount"]) <= 0:
                errors.append("Parameter 'threshold_amount' must be a positive number.")
        elif valid_rule == PolicyRuleType.BATCH_BUDGET_EXCEEDED:
            if "max_batch_amount" not in parameters or float(parameters["max_batch_amount"]) <= 0:
                errors.append("Parameter 'max_batch_amount' must be a positive number.")
        elif valid_rule == PolicyRuleType.SPLIT_PAYMENT_DETECTION:
            if "threshold_amount" not in parameters or float(parameters["threshold_amount"]) <= 0:
                errors.append("Parameter 'threshold_amount' must be positive for split detection.")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "rule_type": valid_rule,
            "severity": valid_severity,
        }

    def save_policy(
        self,
        policy: Policy,
        actor: str = "policy_admin",
    ) -> Policy:
        val = self.validate_policy_draft(
            name=policy.name,
            rule_type=policy.rule_type.value,
            severity=policy.severity.value,
            parameters=policy.parameters,
        )
        if not val["is_valid"]:
            raise ValueError(f"Policy validation failed: {'; '.join(val['errors'])}")

        existing = self.policy_repo.get_by_id(policy.id)
        self.policy_repo.upsert(policy)

        event_type = AuditEventType.POLICY_EDITED if existing else AuditEventType.POLICY_CREATED
        self.audit_repo.log(
            event_type=event_type,
            actor=actor,
            outcome="SUCCESS",
            details={
                "policy_id": policy.id,
                "name": policy.name,
                "rule_type": policy.rule_type.value,
                "severity": policy.severity.value,
                "is_active": policy.is_active,
            },
        )
        return policy

    def toggle_activation(self, policy_id: str, is_active: bool, actor: str = "policy_admin") -> bool:
        policy = self.policy_repo.get_by_id(policy_id)
        if not policy:
            raise ValueError(f"Policy '{policy_id}' not found.")

        # Mandatory safety policies cannot be deactivated
        if not is_active and policy.is_mandatory:
            raise ValueError(f"Policy '{policy.name}' is a mandatory foundational safety guard and cannot be deactivated.")

        success = self.policy_repo.toggle_active(policy_id, is_active)
        if success:
            event_type = AuditEventType.POLICY_ACTIVATED if is_active else AuditEventType.POLICY_DEACTIVATED
            self.audit_repo.log(
                event_type=event_type,
                actor=actor,
                outcome="SUCCESS",
                details={"policy_id": policy_id, "is_active": is_active},
            )
        return success
