"""
Account repository for PayWise.
"""
import sqlite3
from datetime import datetime
from typing import List, Optional
from paywise.models.account import Account, AccountStatus
from paywise.repositories.database import get_connection


class AccountRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def get_by_id(self, account_id: str, conn: sqlite3.Connection = None) -> Optional[Account]:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            cur.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
            row = cur.fetchone()
            if not row:
                return None
            return Account(
                id=row["id"],
                account_number=row["account_number"],
                bank_name=row["bank_name"],
                account_name=row["account_name"],
                currency=row["currency"],
                current_balance=float(row["current_balance"]),
                reserved_balance=float(row["reserved_balance"]),
                status=AccountStatus(row["status"]),
                version=int(row["version"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
        finally:
            if own_conn:
                c.close()

    def list_all(self, conn: sqlite3.Connection = None) -> List[Account]:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            cur.execute("SELECT * FROM accounts ORDER BY id ASC")
            rows = cur.fetchall()
            return [
                Account(
                    id=r["id"],
                    account_number=r["account_number"],
                    bank_name=r["bank_name"],
                    account_name=r["account_name"],
                    currency=r["currency"],
                    current_balance=float(r["current_balance"]),
                    reserved_balance=float(r["reserved_balance"]),
                    status=AccountStatus(r["status"]),
                    version=int(r["version"]),
                    updated_at=datetime.fromisoformat(r["updated_at"]),
                )
                for r in rows
            ]
        finally:
            if own_conn:
                c.close()

    def update_balance(
        self,
        account_id: str,
        new_balance: float,
        expected_version: int,
        conn: sqlite3.Connection = None,
    ) -> bool:
        """
        Updates ledger balance using optimistic concurrency locking.
        Fails if account version does not match expected_version.
        """
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            now_iso = datetime.utcnow().isoformat()
            cur.execute(
                """
                UPDATE accounts
                SET current_balance = ?, version = version + 1, updated_at = ?
                WHERE id = ? AND version = ?
                """,
                (new_balance, now_iso, account_id, expected_version),
            )
            affected = cur.rowcount
            if own_conn:
                c.commit()
            return affected > 0
        finally:
            if own_conn:
                c.close()

    def upsert(self, account: Account, conn: sqlite3.Connection = None) -> None:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            cur.execute(
                """
                INSERT INTO accounts (id, account_number, bank_name, account_name, currency, current_balance, reserved_balance, status, version, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    account_number = excluded.account_number,
                    bank_name = excluded.bank_name,
                    account_name = excluded.account_name,
                    currency = excluded.currency,
                    current_balance = excluded.current_balance,
                    reserved_balance = excluded.reserved_balance,
                    status = excluded.status,
                    version = excluded.version,
                    updated_at = excluded.updated_at
                """,
                (
                    account.id,
                    account.account_number,
                    account.bank_name,
                    account.account_name,
                    account.currency,
                    account.current_balance,
                    account.reserved_balance,
                    account.status.value,
                    account.version,
                    account.updated_at.isoformat(),
                ),
            )
            if own_conn:
                c.commit()
        finally:
            if own_conn:
                c.close()
