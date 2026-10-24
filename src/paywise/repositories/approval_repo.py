"""
Approval repository for PayWise.
"""
import sqlite3
from datetime import datetime
from typing import List, Optional
from paywise.models.approval import Approval, ApprovalDecision
from paywise.repositories.database import get_connection


class ApprovalRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def create(self, approval: Approval, conn: sqlite3.Connection = None) -> Approval:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            cur.execute(
                """
                INSERT INTO approvals (id, proposal_id, proposal_version, proposal_hash, preview_id, preview_hash, ledger_state_hash, policy_set_hash, approver_id, approver_name, approver_role, decision, justification, created_at, is_valid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    approval.id,
                    approval.proposal_id,
                    approval.proposal_version,
                    approval.proposal_hash,
                    approval.preview_id,
                    approval.preview_hash,
                    approval.ledger_state_hash,
                    approval.policy_set_hash,
                    approval.approver_id,
                    approval.approver_name,
                    approval.approver_role,
                    approval.decision.value,
                    approval.justification,
                    approval.created_at.isoformat(),
                    1 if approval.is_valid else 0,
                ),
            )
            if own_conn:
                c.commit()
            return approval
        finally:
            if own_conn:
                c.close()

    def get_latest_valid_approval(self, proposal_id: str, conn: sqlite3.Connection = None) -> Optional[Approval]:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            cur.execute(
                "SELECT * FROM approvals WHERE proposal_id = ? AND is_valid = 1 ORDER BY created_at DESC LIMIT 1",
                (proposal_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_approval(row)
        finally:
            if own_conn:
                c.close()

    def list_for_proposal(self, proposal_id: str, conn: sqlite3.Connection = None) -> List[Approval]:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            cur.execute(
                "SELECT * FROM approvals WHERE proposal_id = ? ORDER BY created_at DESC",
                (proposal_id,),
            )
            return [self._row_to_approval(r) for r in cur.fetchall()]
        finally:
            if own_conn:
                c.close()

    def invalidate_all_for_proposal(self, proposal_id: str, conn: sqlite3.Connection = None) -> int:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            cur.execute(
                "UPDATE approvals SET is_valid = 0 WHERE proposal_id = ? AND is_valid = 1",
                (proposal_id,),
            )
            affected = cur.rowcount
            if own_conn:
                c.commit()
            return affected
        finally:
            if own_conn:
                c.close()

    def _row_to_approval(self, row: sqlite3.Row) -> Approval:
        return Approval(
            id=row["id"],
            proposal_id=row["proposal_id"],
            proposal_version=int(row["proposal_version"]),
            proposal_hash=row["proposal_hash"],
            preview_id=row["preview_id"],
            preview_hash=row["preview_hash"],
            ledger_state_hash=row["ledger_state_hash"],
            policy_set_hash=row["policy_set_hash"],
            approver_id=row["approver_id"],
            approver_name=row["approver_name"],
            approver_role=row["approver_role"],
            decision=ApprovalDecision(row["decision"]),
            justification=row["justification"],
            created_at=datetime.fromisoformat(row["created_at"]),
            is_valid=bool(row["is_valid"]),
        )
