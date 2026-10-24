"""
Proposal and ProposedTransaction repository.
"""
import json
import sqlite3
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from paywise.models.proposal import (
    Proposal,
    ProposalStatus,
    ProposalType,
    ProposedTransaction,
    TransactionType,
)
from paywise.models.simulation import SimulationPreview, TransactionOutcome
from paywise.models.policy import PolicyFinding, PolicySeverity
from paywise.repositories.database import get_connection
from paywise.security.hashing import compute_proposal_hash


class ProposalRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def create(self, proposal: Proposal, conn: sqlite3.Connection = None) -> Proposal:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            # Calculate total and hash
            proposal.total_amount = proposal.calculate_total()
            tx_dicts = [t.model_dump() for t in proposal.transactions]
            proposal.proposal_hash = compute_proposal_hash(
                proposal.id, proposal.version, proposal.account_id, tx_dicts
            )

            cur.execute(
                """
                INSERT INTO proposals (id, proposal_type, title, description, source, account_id, total_amount, currency, status, version, proposal_hash, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proposal.id,
                    proposal.proposal_type.value,
                    proposal.title,
                    proposal.description,
                    proposal.source,
                    proposal.account_id,
                    proposal.total_amount,
                    proposal.currency,
                    proposal.status.value,
                    proposal.version,
                    proposal.proposal_hash,
                    proposal.created_by,
                    proposal.created_at.isoformat(),
                    proposal.updated_at.isoformat(),
                ),
            )

            # Insert transactions
            for tx in proposal.transactions:
                cur.execute(
                    """
                    INSERT INTO proposed_transactions (id, proposal_id, proposal_version, transaction_type, invoice_id, supplier_id, beneficiary_name, amount, currency, proposed_payment_date, transaction_category, description, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tx.id,
                        proposal.id,
                        proposal.version,
                        tx.transaction_type.value,
                        tx.invoice_id,
                        tx.supplier_id,
                        tx.beneficiary_name,
                        tx.amount,
                        tx.currency,
                        tx.proposed_payment_date.isoformat(),
                        tx.transaction_category,
                        tx.description,
                        tx.status,
                        datetime.utcnow().isoformat(),
                    ),
                )

            if own_conn:
                c.commit()
            return proposal
        finally:
            if own_conn:
                c.close()

    def get_by_id(self, proposal_id: str, conn: sqlite3.Connection = None) -> Optional[Proposal]:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            cur.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,))
            p_row = cur.fetchone()
            if not p_row:
                return None

            cur.execute(
                "SELECT * FROM proposed_transactions WHERE proposal_id = ? ORDER BY id ASC",
                (proposal_id,),
            )
            tx_rows = cur.fetchall()

            txs = [
                ProposedTransaction(
                    id=tr["id"],
                    proposal_id=tr["proposal_id"],
                    proposal_version=int(tr["proposal_version"]),
                    transaction_type=TransactionType(tr["transaction_type"]),
                    invoice_id=tr["invoice_id"],
                    supplier_id=tr["supplier_id"],
                    beneficiary_name=tr["beneficiary_name"],
                    amount=float(tr["amount"]),
                    currency=tr["currency"],
                    proposed_payment_date=date.fromisoformat(tr["proposed_payment_date"]),
                    transaction_category=tr["transaction_category"],
                    description=tr["description"],
                    status=tr["status"],
                )
                for tr in tx_rows
            ]

            return Proposal(
                id=p_row["id"],
                proposal_type=ProposalType(p_row["proposal_type"]),
                title=p_row["title"],
                description=p_row["description"],
                source=p_row["source"],
                account_id=p_row["account_id"],
                total_amount=float(p_row["total_amount"]),
                currency=p_row["currency"],
                status=ProposalStatus(p_row["status"]),
                version=int(p_row["version"]),
                proposal_hash=p_row["proposal_hash"],
                created_by=p_row["created_by"],
                created_at=datetime.fromisoformat(p_row["created_at"]),
                updated_at=datetime.fromisoformat(p_row["updated_at"]),
                transactions=txs,
            )
        finally:
            if own_conn:
                c.close()

    def list_all(self, status: Optional[str] = None, conn: sqlite3.Connection = None) -> List[Proposal]:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            if status:
                cur.execute("SELECT id FROM proposals WHERE status = ? ORDER BY created_at DESC", (status,))
            else:
                cur.execute("SELECT id FROM proposals ORDER BY created_at DESC")
            ids = [r["id"] for r in cur.fetchall()]
            return [self.get_by_id(pid, conn=c) for pid in ids if pid]
        finally:
            if own_conn:
                c.close()

    def update_proposal(self, proposal: Proposal, conn: sqlite3.Connection = None) -> Proposal:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            proposal.version += 1
            proposal.updated_at = datetime.utcnow()
            proposal.total_amount = proposal.calculate_total()
            tx_dicts = [t.model_dump() for t in proposal.transactions]
            proposal.proposal_hash = compute_proposal_hash(
                proposal.id, proposal.version, proposal.account_id, tx_dicts
            )

            cur.execute(
                """
                UPDATE proposals
                SET title = ?, description = ?, account_id = ?, total_amount = ?,
                    status = ?, version = ?, proposal_hash = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    proposal.title,
                    proposal.description,
                    proposal.account_id,
                    proposal.total_amount,
                    proposal.status.value,
                    proposal.version,
                    proposal.proposal_hash,
                    proposal.updated_at.isoformat(),
                    proposal.id,
                ),
            )

            # Re-insert transactions with new version
            cur.execute("DELETE FROM proposed_transactions WHERE proposal_id = ?", (proposal.id,))
            for tx in proposal.transactions:
                cur.execute(
                    """
                    INSERT INTO proposed_transactions (id, proposal_id, proposal_version, transaction_type, invoice_id, supplier_id, beneficiary_name, amount, currency, proposed_payment_date, transaction_category, description, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tx.id,
                        proposal.id,
                        proposal.version,
                        tx.transaction_type.value,
                        tx.invoice_id,
                        tx.supplier_id,
                        tx.beneficiary_name,
                        tx.amount,
                        tx.currency,
                        tx.proposed_payment_date.isoformat(),
                        tx.transaction_category,
                        tx.description,
                        tx.status,
                        datetime.utcnow().isoformat(),
                    ),
                )

            if own_conn:
                c.commit()
            return proposal
        finally:
            if own_conn:
                c.close()

    def update_status(self, proposal_id: str, new_status: ProposalStatus, conn: sqlite3.Connection = None) -> bool:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            now_iso = datetime.utcnow().isoformat()
            cur.execute(
                "UPDATE proposals SET status = ?, updated_at = ? WHERE id = ?",
                (new_status.value, now_iso, proposal_id),
            )
            affected = cur.rowcount
            if own_conn:
                c.commit()
            return affected > 0
        finally:
            if own_conn:
                c.close()

    def save_preview(self, preview: SimulationPreview, conn: sqlite3.Connection = None) -> None:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            findings_data = [f.model_dump() for f in preview.findings]
            cur.execute(
                """
                INSERT INTO simulation_previews (
                    id, proposal_id, proposal_version, proposal_hash,
                    ledger_version, ledger_state_hash, policy_version, policy_set_hash,
                    current_balance, projected_balance, reserved_balance,
                    available_balance_before, available_balance_after,
                    total_outflow, remaining_budget, findings_json,
                    can_proceed, requires_approval, simulated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    findings_json = excluded.findings_json,
                    can_proceed = excluded.can_proceed,
                    requires_approval = excluded.requires_approval,
                    simulated_at = excluded.simulated_at
                """,
                (
                    preview.id,
                    preview.proposal_id,
                    preview.proposal_version,
                    preview.proposal_hash,
                    preview.ledger_version,
                    preview.ledger_state_hash,
                    preview.policy_version,
                    preview.policy_set_hash,
                    preview.current_balance,
                    preview.projected_balance,
                    preview.reserved_balance,
                    preview.available_balance_before,
                    preview.available_balance_after,
                    preview.total_outflow,
                    preview.remaining_budget,
                    json.dumps(findings_data),
                    1 if preview.can_proceed else 0,
                    1 if preview.requires_approval else 0,
                    preview.simulated_at.isoformat(),
                ),
            )
            if own_conn:
                c.commit()
        finally:
            if own_conn:
                c.close()

    def get_latest_preview(self, proposal_id: str, conn: sqlite3.Connection = None) -> Optional[SimulationPreview]:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            cur.execute(
                "SELECT * FROM simulation_previews WHERE proposal_id = ? ORDER BY simulated_at DESC LIMIT 1",
                (proposal_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            findings_raw = json.loads(row["findings_json"])
            findings = [
                PolicyFinding(
                    policy_id=f["policy_id"],
                    rule_name=f["rule_name"],
                    severity=PolicySeverity(f["severity"]),
                    affected_transaction_ids=f["affected_transaction_ids"],
                    explanation=f["explanation"],
                    relevant_values=f["relevant_values"],
                    recommended_action=f["recommended_action"],
                )
                for f in findings_raw
            ]
            return SimulationPreview(
                id=row["id"],
                proposal_id=row["proposal_id"],
                proposal_version=int(row["proposal_version"]),
                proposal_hash=row["proposal_hash"],
                ledger_version=int(row["ledger_version"]),
                ledger_state_hash=row["ledger_state_hash"],
                policy_version=int(row["policy_version"]),
                policy_set_hash=row["policy_set_hash"],
                current_balance=float(row["current_balance"]),
                projected_balance=float(row["projected_balance"]),
                reserved_balance=float(row["reserved_balance"]),
                available_balance_before=float(row["available_balance_before"]),
                available_balance_after=float(row["available_balance_after"]),
                total_outflow=float(row["total_outflow"]),
                remaining_budget=float(row["remaining_budget"]),
                findings=findings,
                can_proceed=bool(row["can_proceed"]),
                requires_approval=bool(row["requires_approval"]),
                simulated_at=datetime.fromisoformat(row["simulated_at"]),
            )
        finally:
            if own_conn:
                c.close()
