"""
Invoice repository for PayWise.
"""
import sqlite3
from datetime import date, datetime
from typing import List, Optional
from paywise.models.invoice import Invoice, InvoiceStatus
from paywise.repositories.database import get_connection


class InvoiceRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def get_by_id(self, invoice_id: str, conn: sqlite3.Connection = None) -> Optional[Invoice]:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            cur.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
            row = cur.fetchone()
            if not row:
                return None
            return Invoice(
                id=row["id"],
                supplier_id=row["supplier_id"],
                invoice_number=row["invoice_number"],
                invoice_date=date.fromisoformat(row["invoice_date"]),
                due_date=date.fromisoformat(row["due_date"]),
                amount=float(row["amount"]),
                currency=row["currency"],
                status=InvoiceStatus(row["status"]),
                description=row["description"],
                paid_at=datetime.fromisoformat(row["paid_at"]) if row["paid_at"] else None,
                paid_transaction_id=row["paid_transaction_id"],
                version=int(row["version"]),
            )
        finally:
            if own_conn:
                c.close()

    def list_all(self, supplier_id: str = None, conn: sqlite3.Connection = None) -> List[Invoice]:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            if supplier_id:
                cur.execute("SELECT * FROM invoices WHERE supplier_id = ? ORDER BY due_date ASC", (supplier_id,))
            else:
                cur.execute("SELECT * FROM invoices ORDER BY due_date ASC")
            rows = cur.fetchall()
            return [
                Invoice(
                    id=r["id"],
                    supplier_id=r["supplier_id"],
                    invoice_number=r["invoice_number"],
                    invoice_date=date.fromisoformat(r["invoice_date"]),
                    due_date=date.fromisoformat(r["due_date"]),
                    amount=float(r["amount"]),
                    currency=r["currency"],
                    status=InvoiceStatus(r["status"]),
                    description=r["description"],
                    paid_at=datetime.fromisoformat(r["paid_at"]) if r["paid_at"] else None,
                    paid_transaction_id=r["paid_transaction_id"],
                    version=int(r["version"]),
                )
                for r in rows
            ]
        finally:
            if own_conn:
                c.close()

    def mark_as_paid(
        self,
        invoice_id: str,
        transaction_id: str,
        conn: sqlite3.Connection = None,
    ) -> bool:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            now_iso = datetime.utcnow().isoformat()
            cur.execute(
                """
                UPDATE invoices
                SET status = 'PAID', paid_at = ?, paid_transaction_id = ?, version = version + 1
                WHERE id = ? AND status = 'PENDING'
                """,
                (now_iso, transaction_id, invoice_id),
            )
            affected = cur.rowcount
            if own_conn:
                c.commit()
            return affected > 0
        finally:
            if own_conn:
                c.close()

    def upsert(self, invoice: Invoice, conn: sqlite3.Connection = None) -> None:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            cur.execute(
                """
                INSERT INTO invoices (id, supplier_id, invoice_number, invoice_date, due_date, amount, currency, status, description, paid_at, paid_transaction_id, version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    supplier_id = excluded.supplier_id,
                    invoice_number = excluded.invoice_number,
                    invoice_date = excluded.invoice_date,
                    due_date = excluded.due_date,
                    amount = excluded.amount,
                    currency = excluded.currency,
                    status = excluded.status,
                    description = excluded.description,
                    paid_at = excluded.paid_at,
                    paid_transaction_id = excluded.paid_transaction_id,
                    version = excluded.version
                """,
                (
                    invoice.id,
                    invoice.supplier_id,
                    invoice.invoice_number,
                    invoice.invoice_date.isoformat(),
                    invoice.due_date.isoformat(),
                    invoice.amount,
                    invoice.currency,
                    invoice.status.value,
                    invoice.description,
                    invoice.paid_at.isoformat() if invoice.paid_at else None,
                    invoice.paid_transaction_id,
                    invoice.version,
                ),
            )
            if own_conn:
                c.commit()
        finally:
            if own_conn:
                c.close()
