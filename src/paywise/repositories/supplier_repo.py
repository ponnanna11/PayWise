"""
Supplier repository for PayWise.
"""
import sqlite3
from datetime import datetime
from typing import List, Optional
from paywise.models.supplier import RiskTier, Supplier, SupplierStatus
from paywise.repositories.database import get_connection


class SupplierRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def get_by_id(self, supplier_id: str, conn: sqlite3.Connection = None) -> Optional[Supplier]:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            cur.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
            row = cur.fetchone()
            if not row:
                return None
            return Supplier(
                id=row["id"],
                name=row["name"],
                gstin=row["gstin"],
                pan=row["pan"],
                bank_account_number=row["bank_account_number"],
                bank_ifsc=row["bank_ifsc"],
                status=SupplierStatus(row["status"]),
                risk_tier=RiskTier(row["risk_tier"]),
                default_category=row["default_category"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
        finally:
            if own_conn:
                c.close()

    def list_all(self, conn: sqlite3.Connection = None) -> List[Supplier]:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            cur.execute("SELECT * FROM suppliers ORDER BY name ASC")
            rows = cur.fetchall()
            return [
                Supplier(
                    id=r["id"],
                    name=r["name"],
                    gstin=r["gstin"],
                    pan=r["pan"],
                    bank_account_number=r["bank_account_number"],
                    bank_ifsc=r["bank_ifsc"],
                    status=SupplierStatus(r["status"]),
                    risk_tier=RiskTier(r["risk_tier"]),
                    default_category=r["default_category"],
                    created_at=datetime.fromisoformat(r["created_at"]),
                )
                for r in rows
            ]
        finally:
            if own_conn:
                c.close()

    def upsert(self, supplier: Supplier, conn: sqlite3.Connection = None) -> None:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            cur.execute(
                """
                INSERT INTO suppliers (id, name, gstin, pan, bank_account_number, bank_ifsc, status, risk_tier, default_category, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    gstin = excluded.gstin,
                    pan = excluded.pan,
                    bank_account_number = excluded.bank_account_number,
                    bank_ifsc = excluded.bank_ifsc,
                    status = excluded.status,
                    risk_tier = excluded.risk_tier,
                    default_category = excluded.default_category
                """,
                (
                    supplier.id,
                    supplier.name,
                    supplier.gstin,
                    supplier.pan,
                    supplier.bank_account_number,
                    supplier.bank_ifsc,
                    supplier.status.value,
                    supplier.risk_tier.value,
                    supplier.default_category,
                    supplier.created_at.isoformat(),
                ),
            )
            if own_conn:
                c.commit()
        finally:
            if own_conn:
                c.close()
