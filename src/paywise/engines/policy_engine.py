"""
Deterministic Policy Engine for PayWise.
Evaluates explicit business rules and safety boundaries: R = g(S, S', A, P).
Produces structured findings with severity: BLOCK, REQUIRE_APPROVAL, or WARN.
"""
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from paywise.models.account import Account
from paywise.models.approval import Approval
from paywise.models.invoice import Invoice, InvoiceStatus
from paywise.models.policy import (
    Policy,
    PolicyFinding,
    PolicyRuleType,
    PolicySeverity,
)
from paywise.models.proposal import Proposal, ProposedTransaction
from paywise.models.simulation import SimulationPreview
from paywise.models.supplier import RiskTier, Supplier, SupplierStatus
from paywise.utils.formatters import format_inr


class PolicyEngine:
    def evaluate(
        self,
        account: Account,
        preview: SimulationPreview,
        proposal: Proposal,
        policies: List[Policy],
        suppliers: Dict[str, Supplier] = None,
        invoices: Dict[str, Invoice] = None,
        existing_approval: Optional[Approval] = None,
        is_commit_check: bool = False,
    ) -> List[PolicyFinding]:
        """
        Executes deterministic rule evaluation against active policies.
        Returns a list of structured PolicyFinding objects.
        """
        suppliers = suppliers or {}
        invoices = invoices or {}
        findings: List[PolicyFinding] = []

        # Only evaluate active policies
        active_policies = [p for p in policies if p.is_active]
        policy_map: Dict[PolicyRuleType, Policy] = {p.rule_type: p for p in active_policies}

        # 1. INSUFFICIENT_FUNDS
        if PolicyRuleType.INSUFFICIENT_FUNDS in policy_map:
            pol = policy_map[PolicyRuleType.INSUFFICIENT_FUNDS]
            if preview.projected_balance < 0 or proposal.total_amount > account.available_funds:
                findings.append(
                    PolicyFinding(
                        policy_id=pol.id,
                        rule_name=pol.name,
                        severity=pol.severity,
                        affected_transaction_ids=[t.id for t in proposal.transactions],
                        explanation=(
                            f"Total proposed outflow ({format_inr(proposal.total_amount)}) exceeds "
                            f"available funds ({format_inr(account.available_funds)}). "
                            f"Projected balance would be {format_inr(preview.projected_balance)}."
                        ),
                        relevant_values={
                            "total_outflow": proposal.total_amount,
                            "available_funds": account.available_funds,
                            "projected_balance": preview.projected_balance,
                        },
                        recommended_action="Deposit additional liquidity into account or reduce proposed payout batch.",
                    )
                )

        # 2. MINIMUM_RESERVE_BREACH
        if PolicyRuleType.MINIMUM_RESERVE_BREACH in policy_map:
            pol = policy_map[PolicyRuleType.MINIMUM_RESERVE_BREACH]
            if preview.projected_balance < account.reserved_balance and preview.projected_balance >= 0:
                deficit = round(account.reserved_balance - preview.projected_balance, 2)
                findings.append(
                    PolicyFinding(
                        policy_id=pol.id,
                        rule_name=pol.name,
                        severity=pol.severity,
                        affected_transaction_ids=[t.id for t in proposal.transactions],
                        explanation=(
                            f"Disbursement would breach mandatory safety reserve of {format_inr(account.reserved_balance)}. "
                            f"Projected balance of {format_inr(preview.projected_balance)} creates a {format_inr(deficit)} reserve shortfall."
                        ),
                        relevant_values={
                            "reserved_balance": account.reserved_balance,
                            "projected_balance": preview.projected_balance,
                            "shortfall": deficit,
                        },
                        recommended_action=(
                            f"Maintain at least {format_inr(account.reserved_balance)} in reserve. "
                            f"Reduce batch size by at least {format_inr(deficit)}."
                        ),
                    )
                )

        # 3. DUPLICATE_INVOICE_PAYMENT
        if PolicyRuleType.DUPLICATE_INVOICE_PAYMENT in policy_map:
            pol = policy_map[PolicyRuleType.DUPLICATE_INVOICE_PAYMENT]
            seen_invoices = defaultdict(list)
            for tx in proposal.transactions:
                if tx.invoice_id:
                    seen_invoices[tx.invoice_id].append(tx.id)

            for inv_id, tx_ids in seen_invoices.items():
                if len(tx_ids) > 1:
                    findings.append(
                        PolicyFinding(
                            policy_id=pol.id,
                            rule_name=pol.name,
                            severity=pol.severity,
                            affected_transaction_ids=tx_ids,
                            explanation=f"Multiple proposed transactions ({', '.join(tx_ids)}) target the identical invoice {inv_id}.",
                            relevant_values={"invoice_id": inv_id, "duplicate_count": len(tx_ids)},
                            recommended_action="Consolidate duplicate payment entries or remove redundant line items.",
                        )
                    )

        # 4. CANCELLED_OR_PAID_INVOICE
        if PolicyRuleType.CANCELLED_OR_PAID_INVOICE in policy_map:
            pol = policy_map[PolicyRuleType.CANCELLED_OR_PAID_INVOICE]
            for tx in proposal.transactions:
                if tx.invoice_id and tx.invoice_id in invoices:
                    inv = invoices[tx.invoice_id]
                    if inv.status in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED, InvoiceStatus.DISPUTED]:
                        findings.append(
                            PolicyFinding(
                                policy_id=pol.id,
                                rule_name=pol.name,
                                severity=pol.severity,
                                affected_transaction_ids=[tx.id],
                                explanation=(
                                    f"Transaction {tx.id} targets invoice {inv.id} with non-payable status: '{inv.status.value}'."
                                ),
                                relevant_values={"invoice_id": inv.id, "invoice_status": inv.status.value},
                                recommended_action=f"Remove payment for {inv.status.value.lower()} invoice {inv.id}.",
                            )
                        )

        # 5. UNAPPROVED_SUPPLIER
        if PolicyRuleType.UNAPPROVED_SUPPLIER in policy_map:
            pol = policy_map[PolicyRuleType.UNAPPROVED_SUPPLIER]
            for tx in proposal.transactions:
                if tx.supplier_id:
                    sup = suppliers.get(tx.supplier_id)
                    if not sup or sup.status != SupplierStatus.APPROVED:
                        status_str = sup.status.value if sup else "UNKNOWN_VENDOR"
                        findings.append(
                            PolicyFinding(
                                policy_id=pol.id,
                                rule_name=pol.name,
                                severity=pol.severity,
                                affected_transaction_ids=[tx.id],
                                explanation=(
                                    f"Payee {tx.beneficiary_name} (ID: {tx.supplier_id}) has unapproved status: '{status_str}'."
                                ),
                                relevant_values={"supplier_id": tx.supplier_id, "supplier_status": status_str},
                                recommended_action="Complete vendor onboarding and KYC approval before releasing payment.",
                            )
                        )

        # 6. AMOUNT_MISMATCH
        if PolicyRuleType.AMOUNT_MISMATCH in policy_map:
            pol = policy_map[PolicyRuleType.AMOUNT_MISMATCH]
            tolerance = float(pol.parameters.get("tolerance_amount", 0.0))
            for tx in proposal.transactions:
                if tx.invoice_id and tx.invoice_id in invoices:
                    inv = invoices[tx.invoice_id]
                    diff = round(abs(tx.amount - inv.amount), 2)
                    if diff > tolerance:
                        findings.append(
                            PolicyFinding(
                                policy_id=pol.id,
                                rule_name=pol.name,
                                severity=pol.severity,
                                affected_transaction_ids=[tx.id],
                                explanation=(
                                    f"Payment amount ({format_inr(tx.amount)}) differs from invoice amount "
                                    f"({format_inr(inv.amount)}) by {format_inr(diff)}."
                                ),
                                relevant_values={
                                    "transaction_amount": tx.amount,
                                    "invoice_amount": inv.amount,
                                    "difference": diff,
                                    "tolerance": tolerance,
                                },
                                recommended_action="Adjust payment amount to exactly match the billed invoice figure.",
                            )
                        )

        # 7. BATCH_BUDGET_EXCEEDED
        if PolicyRuleType.BATCH_BUDGET_EXCEEDED in policy_map:
            pol = policy_map[PolicyRuleType.BATCH_BUDGET_EXCEEDED]
            max_batch = float(pol.parameters.get("max_batch_amount", 500000.0))
            if proposal.total_amount > max_batch:
                excess = round(proposal.total_amount - max_batch, 2)
                findings.append(
                    PolicyFinding(
                        policy_id=pol.id,
                        rule_name=pol.name,
                        severity=pol.severity,
                        affected_transaction_ids=[t.id for t in proposal.transactions],
                        explanation=(
                            f"Total batch amount ({format_inr(proposal.total_amount)}) exceeds configured "
                            f"batch ceiling of {format_inr(max_batch)} by {format_inr(excess)}."
                        ),
                        relevant_values={"total_amount": proposal.total_amount, "batch_limit": max_batch, "excess": excess},
                        recommended_action="Obtain authorized executive approval for high-value batch disbursement.",
                    )
                )

        # 8. APPROVAL_THRESHOLD_EXCEEDED
        if PolicyRuleType.APPROVAL_THRESHOLD_EXCEEDED in policy_map:
            pol = policy_map[PolicyRuleType.APPROVAL_THRESHOLD_EXCEEDED]
            threshold = float(pol.parameters.get("threshold_amount", 50000.0))
            for tx in proposal.transactions:
                if tx.amount > threshold:
                    findings.append(
                        PolicyFinding(
                            policy_id=pol.id,
                            rule_name=pol.name,
                            severity=pol.severity,
                            affected_transaction_ids=[tx.id],
                            explanation=(
                                f"Payment {tx.id} for {format_inr(tx.amount)} to {tx.beneficiary_name} "
                                f"exceeds individual threshold of {format_inr(threshold)}."
                            ),
                            relevant_values={"amount": tx.amount, "threshold": threshold},
                            recommended_action="Route transaction for managerial sign-off.",
                        )
                    )

        # 9. SPLIT_PAYMENT_DETECTION
        if PolicyRuleType.SPLIT_PAYMENT_DETECTION in policy_map:
            pol = policy_map[PolicyRuleType.SPLIT_PAYMENT_DETECTION]
            threshold = float(pol.parameters.get("threshold_amount", 50000.0))
            # Group transactions by supplier / beneficiary
            by_payee = defaultdict(list)
            for tx in proposal.transactions:
                key = tx.supplier_id or tx.beneficiary_name
                by_payee[key].append(tx)

            for key, txs in by_payee.items():
                if len(txs) > 1:
                    payee_total = sum(t.amount for t in txs)
                    # If each tx was individually below or equal to threshold, but together they exceed threshold!
                    all_below = all(t.amount <= threshold for t in txs)
                    if all_below and payee_total > threshold:
                        findings.append(
                            PolicyFinding(
                                policy_id=pol.id,
                                rule_name=pol.name,
                                severity=pol.severity,
                                affected_transaction_ids=[t.id for t in txs],
                                explanation=(
                                    f"Detected {len(txs)} transactions to '{txs[0].beneficiary_name}' "
                                    f"individually under {format_inr(threshold)} but totaling {format_inr(payee_total)}, "
                                    f"indicating a potential split payment to evade approval."
                                ),
                                relevant_values={"payee": txs[0].beneficiary_name, "cumulative_total": payee_total, "threshold": threshold},
                                recommended_action="Consolidate disbursements and obtain formal manager sign-off.",
                            )
                        )

        # 10. PAYMENT_DATE_SCHEDULING
        if PolicyRuleType.PAYMENT_DATE_SCHEDULING in policy_map:
            pol = policy_map[PolicyRuleType.PAYMENT_DATE_SCHEDULING]
            allow_past = pol.parameters.get("allow_past_dates", False)
            allow_weekends = pol.parameters.get("allow_weekends", False)
            max_advance = int(pol.parameters.get("max_advance_days", 60))
            today = date.today()

            for tx in proposal.transactions:
                tx_date = tx.proposed_payment_date
                # Past check
                if not allow_past and tx_date < today:
                    findings.append(
                        PolicyFinding(
                            policy_id=pol.id,
                            rule_name=pol.name,
                            severity=pol.severity,
                            affected_transaction_ids=[tx.id],
                            explanation=f"Transaction {tx.id} is scheduled for a past date: {tx_date}.",
                            relevant_values={"scheduled_date": str(tx_date), "today": str(today)},
                            recommended_action="Update execution date to today or a future business banking day.",
                        )
                    )
                # Weekend check (5=Saturday, 6=Sunday)
                if not allow_weekends and tx_date.weekday() in (5, 6):
                    findings.append(
                        PolicyFinding(
                            policy_id=pol.id,
                            rule_name=pol.name,
                            severity=pol.severity,
                            affected_transaction_ids=[tx.id],
                            explanation=f"Transaction {tx.id} is scheduled on a weekend ({tx_date.strftime('%A')}).",
                            relevant_values={"scheduled_date": str(tx_date), "day_of_week": tx_date.strftime('%A')},
                            recommended_action="Reschedule to the next standard banking business day.",
                        )
                    )
                # Max advance check
                if (tx_date - today).days > max_advance:
                    findings.append(
                        PolicyFinding(
                            policy_id=pol.id,
                            rule_name=pol.name,
                            severity=pol.severity,
                            affected_transaction_ids=[tx.id],
                            explanation=f"Transaction {tx.id} is scheduled {(tx_date - today).days} days in advance (limit: {max_advance} days).",
                            relevant_values={"scheduled_date": str(tx_date), "max_advance_days": max_advance},
                            recommended_action="Schedule disbursements within the active 60-day operational window.",
                        )
                    )

        # 15. UNUSUAL_PAYMENT_ACTIVITY
        if PolicyRuleType.UNUSUAL_PAYMENT_ACTIVITY in policy_map:
            pol = policy_map[PolicyRuleType.UNUSUAL_PAYMENT_ACTIVITY]
            high_risk_flag = pol.parameters.get("high_risk_tier_flag", True)
            for tx in proposal.transactions:
                if tx.supplier_id:
                    sup = suppliers.get(tx.supplier_id)
                    if sup and high_risk_flag and sup.risk_tier == RiskTier.HIGH:
                        findings.append(
                            PolicyFinding(
                                policy_id=pol.id,
                                rule_name=pol.name,
                                severity=pol.severity,
                                affected_transaction_ids=[tx.id],
                                explanation=f"Payee {sup.name} is classified under HIGH risk tier.",
                                relevant_values={"supplier_id": sup.id, "risk_tier": sup.risk_tier.value},
                                recommended_action="Perform secondary verification of vendor bank credentials before release.",
                            )
                        )

        # Commit-Time Revalidation Specific Checks (Rules 11, 12, 13, 14)
        if is_commit_check:
            # 11. STALE_PROPOSAL
            if PolicyRuleType.STALE_PROPOSAL in policy_map:
                pol = policy_map[PolicyRuleType.STALE_PROPOSAL]
                if existing_approval and existing_approval.ledger_state_hash != preview.ledger_state_hash:
                    findings.append(
                        PolicyFinding(
                            policy_id=pol.id,
                            rule_name=pol.name,
                            severity=pol.severity,
                            affected_transaction_ids=[t.id for t in proposal.transactions],
                            explanation="Simulated ledger balance or invoice state changed since simulation preview was approved.",
                            relevant_values={
                                "preview_ledger_hash": existing_approval.ledger_state_hash,
                                "current_ledger_hash": preview.ledger_state_hash,
                            },
                            recommended_action="Re-run simulation preview and obtain fresh approval.",
                        )
                    )

            # 12. MODIFIED_AFTER_APPROVAL
            if PolicyRuleType.MODIFIED_AFTER_APPROVAL in policy_map:
                pol = policy_map[PolicyRuleType.MODIFIED_AFTER_APPROVAL]
                if existing_approval and existing_approval.proposal_hash != proposal.proposal_hash:
                    findings.append(
                        PolicyFinding(
                            policy_id=pol.id,
                            rule_name=pol.name,
                            severity=pol.severity,
                            affected_transaction_ids=[t.id for t in proposal.transactions],
                            explanation="Proposal transactions or amounts were modified after approval was granted.",
                            relevant_values={
                                "approved_hash": existing_approval.proposal_hash,
                                "current_hash": proposal.proposal_hash,
                            },
                            recommended_action="Re-submit modified proposal for authorization.",
                        )
                    )

            # 13. UNAUTHORIZED_COMMIT_ATTEMPT
            if PolicyRuleType.UNAUTHORIZED_COMMIT_ATTEMPT in policy_map:
                pol = policy_map[PolicyRuleType.UNAUTHORIZED_COMMIT_ATTEMPT]
                needs_approval = preview.requires_approval or any(
                    f.severity == PolicySeverity.REQUIRE_APPROVAL for f in findings
                )
                if needs_approval and (not existing_approval or not existing_approval.is_valid):
                    findings.append(
                        PolicyFinding(
                            policy_id=pol.id,
                            rule_name=pol.name,
                            severity=pol.severity,
                            affected_transaction_ids=[t.id for t in proposal.transactions],
                            explanation="Attempted to commit a proposal requiring approval without valid authorized sign-off.",
                            relevant_values={"requires_approval": True, "has_valid_approval": bool(existing_approval and existing_approval.is_valid)},
                            recommended_action="Obtain approval from an authorized manager before committing.",
                        )
                    )

            # 14. POLICY_CHANGED_SINCE_PREVIEW
            if PolicyRuleType.POLICY_CHANGED_SINCE_PREVIEW in policy_map:
                pol = policy_map[PolicyRuleType.POLICY_CHANGED_SINCE_PREVIEW]
                if existing_approval and existing_approval.policy_set_hash != preview.policy_set_hash:
                    findings.append(
                        PolicyFinding(
                            policy_id=pol.id,
                            rule_name=pol.name,
                            severity=pol.severity,
                            affected_transaction_ids=[t.id for t in proposal.transactions],
                            explanation="Active policy rules or thresholds were modified between approval and commit time.",
                            relevant_values={
                                "approval_policy_hash": existing_approval.policy_set_hash,
                                "current_policy_hash": preview.policy_set_hash,
                            },
                            recommended_action="Re-simulate under the updated policies and re-approve.",
                        )
                    )

        return findings
