"""
Audit repository for PayWise.
Records and queries tamper-evident audit logs.
"""
import json
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from paywise.models.audit import AuditEvent, AuditEventType
from paywise.repositories.database import get_connection


class AuditRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def log(
        self,
        event_type: AuditEventType,
        actor: str,
        outcome: str = "SUCCESS",
        proposal_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        conn: sqlite3.Connection = None,
    ) -> AuditEvent:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            event = AuditEvent(
                id=f"AUD-{uuid.uuid4().hex[:12].upper()}",
                timestamp=datetime.utcnow(),
                event_type=event_type,
                proposal_id=proposal_id,
                actor=actor,
                outcome=outcome,
                details=details or {},
            )
            cur = c.cursor()
            cur.execute(
                """
                INSERT INTO audit_events (id, timestamp, event_type, proposal_id, actor, outcome, details_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.timestamp.isoformat(),
                    event.event_type.value,
                    event.proposal_id,
                    event.actor,
                    event.outcome,
                    json.dumps(event.details),
                ),
            )
            if own_conn:
                c.commit()
            return event
        finally:
            if own_conn:
                c.close()

    def list_all(
        self,
        proposal_id: Optional[str] = None,
        event_type: Optional[str] = None,
        outcome: Optional[str] = None,
        limit: int = 100,
        conn: sqlite3.Connection = None,
    ) -> List[AuditEvent]:
        own_conn = conn is None
        c = conn or get_connection(self.db_path)
        try:
            cur = c.cursor()
            query = "SELECT * FROM audit_events WHERE 1=1"
            params = []
            if proposal_id:
                query += " AND proposal_id = ?"
                params.append(proposal_id)
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            if outcome:
                query += " AND outcome = ?"
                params.append(outcome)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            return [
                AuditEvent(
                    id=r["id"],
                    timestamp=datetime.fromisoformat(r["timestamp"]),
                    event_type=AuditEventType(r["event_type"]),
                    proposal_id=r["proposal_id"],
                    actor=r["actor"],
                    outcome=r["outcome"],
                    details=json.loads(r["details_json"]) if r["details_json"] else {},
                )
                for r in rows
            ]
        finally:
            if own_conn:
                c.close()
