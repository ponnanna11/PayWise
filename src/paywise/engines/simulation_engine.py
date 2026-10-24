"""
Deterministic Simulation Engine for PayWise.
Calculates projected ledger state: S' = f(S, A).
Simulates consequence of proposed transactions without mutating persistent database state.
"""
from copy import deepcopy
from typing import Dict, List, Optional
from paywise.models.account import Account
from paywise.models.invoice import Invoice
from paywise.models.proposal import Proposal, ProposedTransaction
from paywise.models.simulation import SimulationPreview, TransactionOutcome
from paywise.security.hashing import (
    compute_ledger_state_hash,
    compute_policy_set_hash,
    compute_preview_hash,
    compute_proposal_hash,
)


class SimulationEngine:
    def simulate(
        self,
        account: Account,
        proposal: Proposal,
        invoices: Dict[str, Invoice] = None,
        active_policies: List[Dict] = None,
    ) -> SimulationPreview:
        """
        Runs deterministic virtual simulation of proposal on account.
        Reads current ledger state, copies into virtual simulation state,
        and projects account and available funds without touching persistent storage.
        """
        invoices = invoices or {}
        active_policies = active_policies or []

        # Current ledger metrics
        current_balance = round(float(account.current_balance), 2)
        reserved_balance = round(float(account.reserved_balance), 2)
        avail_before = round(max(0.0, current_balance - reserved_balance), 2)

        # In-memory virtual ledger copy
        virtual_balance = current_balance
        total_outflow = 0.0

        outcomes: List[TransactionOutcome] = []

        for tx in proposal.transactions:
            tx_amount = round(float(tx.amount), 2)
            virtual_balance = round(virtual_balance - tx_amount, 2)
            total_outflow = round(total_outflow + tx_amount, 2)

            outcomes.append(
                TransactionOutcome(
                    transaction_id=tx.id,
                    amount=tx_amount,
                    currency=tx.currency,
                    beneficiary_name=tx.beneficiary_name,
                    account_id=account.id,
                    projected_post_balance=virtual_balance,
                    status="VALID",
                )
            )

        projected_balance = round(current_balance - total_outflow, 2)
        avail_after = round(max(0.0, projected_balance - reserved_balance), 2)

        # Hashes for state binding
        tx_dicts = [t.model_dump() for t in proposal.transactions]
        prop_hash = proposal.proposal_hash or compute_proposal_hash(
            proposal.id, proposal.version, proposal.account_id, tx_dicts
        )

        relevant_invoices = [
            inv.model_dump()
            for inv in invoices.values()
            if inv.id in [t.invoice_id for t in proposal.transactions if t.invoice_id]
        ]
        ledger_state_hash = compute_ledger_state_hash(account.model_dump(), relevant_invoices)
        policy_set_hash = compute_policy_set_hash(active_policies)

        preview_id = f"SIM-{proposal.id}-V{proposal.version}"

        preview = SimulationPreview(
            id=preview_id,
            proposal_id=proposal.id,
            proposal_version=proposal.version,
            proposal_hash=prop_hash,
            ledger_version=account.version,
            ledger_state_hash=ledger_state_hash,
            policy_version=1,
            policy_set_hash=policy_set_hash,
            current_balance=current_balance,
            projected_balance=projected_balance,
            reserved_balance=reserved_balance,
            available_balance_before=avail_before,
            available_balance_after=avail_after,
            total_outflow=total_outflow,
            remaining_budget=avail_after,
            findings=[],
            can_proceed=True,
            requires_approval=False,
            transaction_outcomes=outcomes,
        )
        return preview
