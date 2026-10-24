"""
Simulated Commit Service for PayWise.
Executes atomic, idempotent commits with optimistic concurrency control in SQLite transactions.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from paywise.models.audit import AuditEventType
from paywise.models.proposal import ProposalStatus
from paywise.repositories.account_repo import AccountRepository
from paywise.repositories.approval_repo import ApprovalRepository
from paywise.repositories.audit_repo import AuditRepository
from paywise.repositories.database import get_connection
from paywise.repositories.invoice_repo import InvoiceRepository
from paywise.repositories.proposal_repo import ProposalRepository
from paywise.security.hashing import compute_hash
from paywise.services.revalidation_service import RevalidationService


class CommitError(Exception):
    pass


class ConcurrencyError(CommitError):
    pass


class DuplicateCommitError(CommitError):
    pass


class CommitService:
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.reval_service = RevalidationService(db_path)
        self.proposal_repo = ProposalRepository(db_path)
        self.account_repo = AccountRepository(db_path)
        self.invoice_repo = InvoiceRepository(db_path)
        self.approval_repo = ApprovalRepository(db_path)
        self.audit_repo = AuditRepository(db_path)

    def commit_proposal(self, proposal_id: str, actor: str = "treasury_operator") -> Dict[str, Any]:
        """
        Executes atomic simulated commit after verifying commit-time revalidation.
        Guarantees idempotency and prevents double-spending.
        """
        conn = get_connection(self.db_path)
        try:
            # 1. Check idempotency: check if proposal was already committed
            cur = conn.cursor()
            cur.execute("SELECT * FROM simulated_commits WHERE proposal_id = ?", (proposal_id,))
            existing_commit = cur.fetchone()
            if existing_commit:
                raise DuplicateCommitError(
                    f"Proposal '{proposal_id}' was already committed on {existing_commit['committed_at']} "
                    f"under commit ID {existing_commit['id']}."
                )

            # 2. Run Commit-Time Revalidation
            reval = self.reval_service.revalidate(proposal_id, actor=actor)
            if not reval.is_valid:
                reasons = "; ".join(reval.failure_reasons)
                raise CommitError(f"Commit-time revalidation failed: {reasons}")

            proposal = reval.proposal
            preview = reval.preview
            approval = reval.approval

            # 3. Begin Atomic Transaction
            conn.execute("BEGIN IMMEDIATE TRANSACTION;")

            # 3.1 Reload account inside transaction for optimistic lock
            cur.execute("SELECT * FROM accounts WHERE id = ?", (proposal.account_id,))
            acc_row = cur.fetchone()
            if not acc_row:
                raise CommitError(f"Account '{proposal.account_id}' not found.")

            current_acc_version = int(acc_row["version"])
            current_acc_balance = float(acc_row["current_balance"])
            expected_balance = preview.projected_balance

            # Optimistic lock balance deduction
            now_iso = datetime.utcnow().isoformat()
            cur.execute(
                """
                UPDATE accounts
                SET current_balance = ?, version = version + 1, updated_at = ?
                WHERE id = ? AND version = ?
                """,
                (expected_balance, now_iso, proposal.account_id, current_acc_version),
            )
            if cur.rowcount == 0:
                raise ConcurrencyError("Account balance was modified by a concurrent operation. Rollback triggered.")

            # 3.2 Update invoices to PAID
            for tx in proposal.transactions:
                if tx.invoice_id:
                    cur.execute(
                        """
                        UPDATE invoices
                        SET status = 'PAID', paid_at = ?, paid_transaction_id = ?, version = version + 1
                        WHERE id = ? AND status = 'PENDING'
                        """,
                        (now_iso, tx.id, tx.invoice_id),
                    )

            # 3.3 Update proposed transactions to COMMITTED
            cur.execute(
                "UPDATE proposed_transactions SET status = 'COMMITTED' WHERE proposal_id = ?",
                (proposal.id,),
            )

            # 3.4 Record simulated commit
            commit_id = f"COM-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            commit_hash = compute_hash({
                "commit_id": commit_id,
                "proposal_id": proposal.id,
                "total_amount": proposal.total_amount,
                "post_balance": expected_balance,
            })

            cur.execute(
                """
                INSERT INTO simulated_commits (id, proposal_id, proposal_version, approval_id, total_amount, account_id, pre_commit_balance, post_commit_balance, commit_hash, committed_by, committed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    commit_id,
                    proposal.id,
                    proposal.version,
                    approval.id if approval else None,
                    proposal.total_amount,
                    proposal.account_id,
                    current_acc_balance,
                    expected_balance,
                    commit_hash,
                    actor,
                    now_iso,
                ),
            )

            # 3.5 Update proposal status to COMMITTED_SIMULATED
            cur.execute(
                "UPDATE proposals SET status = 'COMMITTED_SIMULATED', updated_at = ? WHERE id = ?",
                (now_iso, proposal.id),
            )

            # 3.6 Log Audit Event
            audit_id = f"AUD-{uuid.uuid4().hex[:12].upper()}"
            cur.execute(
                """
                INSERT INTO audit_events (id, timestamp, event_type, proposal_id, actor, outcome, details_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    now_iso,
                    AuditEventType.SIMULATED_COMMIT_SUCCEEDED.value,
                    proposal.id,
                    actor,
                    "SUCCESS",
                    f'{{"commit_id": "{commit_id}", "amount": {proposal.total_amount}, "post_balance": {expected_balance}}}',
                ),
            )

            # Commit SQLite transaction
            conn.commit()

            return {
                "success": True,
                "commit_id": commit_id,
                "proposal_id": proposal.id,
                "pre_balance": current_acc_balance,
                "post_balance": expected_balance,
                "total_outflow": proposal.total_amount,
                "committed_at": now_iso,
            }

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
