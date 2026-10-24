"""
Policy repository for PayWise.
Handles persistent policy rules, parameters, and active/inactive status.
"""
import json
import sqlite3
from datetime import datetime
from typing import List, Optional
from paywise.models.policy import Policy, PolicyRuleType, PolicySeverity
from paywise.repositories.database import get_connection


class PolicyRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def get_by_id(self, policy_id: str, conn: sqlite3.Connection = None) -> Optional[Policy]:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            cur.execute("SELECT * FROM policies WHERE id = ?", (policy_id,))
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_policy(row)
        finally:
            if own_conn:
                c.close()

    def list_all(self, conn: sqlite3.Connection = None) -> List[Policy]:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            cur.execute("SELECT * FROM policies ORDER BY id ASC")
            return [self._row_to_policy(r) for r in cur.fetchall()]
        finally:
            if own_conn:
                c.close()

    def list_active(self, conn: sqlite3.Connection = None) -> List[Policy]:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            cur.execute("SELECT * FROM policies WHERE is_active = 1 ORDER BY id ASC")
            return [self._row_to_policy(r) for r in cur.fetchall()]
        finally:
            if own_conn:
                c.close()

    def upsert(self, policy: Policy, conn: sqlite3.Connection = None) -> None:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            cur.execute(
                """
                INSERT INTO policies (id, name, rule_type, severity, is_mandatory, is_active, version, parameters_json, description, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    rule_type = excluded.rule_type,
                    severity = excluded.severity,
                    is_mandatory = excluded.is_mandatory,
                    is_active = excluded.is_active,
                    version = policies.version + 1,
                    parameters_json = excluded.parameters_json,
                    description = excluded.description,
                    updated_at = excluded.updated_at
                """,
                (
                    policy.id,
                    policy.name,
                    policy.rule_type.value,
                    policy.severity.value,
                    1 if policy.is_mandatory else 0,
                    1 if policy.is_active else 0,
                    policy.version,
                    json.dumps(policy.parameters),
                    policy.description,
                    policy.created_by,
                    policy.created_at.isoformat(),
                    policy.updated_at.isoformat(),
                ),
            )
            if own_conn:
                c.commit()
        finally:
            if own_conn:
                c.close()

    def toggle_active(self, policy_id: str, is_active: bool, conn: sqlite3.Connection = None) -> bool:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            now_iso = datetime.utcnow().isoformat()
            cur.execute(
                """
                UPDATE policies
                SET is_active = ?, version = version + 1, updated_at = ?
                WHERE id = ?
                """,
                (1 if is_active else 0, now_iso, policy_id),
            )
            affected = cur.rowcount
            if own_conn:
                c.commit()
            return affected > 0
        finally:
            if own_conn:
                c.close()

    def _row_to_policy(self, row: sqlite3.Row) -> Policy:
        params = json.loads(row["parameters_json"]) if row["parameters_json"] else {}
        return Policy(
            id=row["id"],
            name=row["name"],
            rule_type=PolicyRuleType(row["rule_type"]),
            severity=PolicySeverity(row["severity"]),
            is_mandatory=bool(row["is_mandatory"]),
            is_active=bool(row["is_active"]),
            version=int(row["version"]),
            parameters=params,
            description=row["description"],
            created_by=row["created_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
