"""
SQLite database connection and schema management for PayWise.
Uses standard library sqlite3 with connection pooling / thread-local awareness and foreign keys enabled.
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from paywise.config import DB_PATH


def get_db_path() -> str:
    path = os.getenv("PAYWISE_DB_PATH", DB_PATH)
    # Ensure directory exists
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return path


def get_connection(db_path: str = None) -> sqlite3.Connection:
    target_path = db_path or get_db_path()
    conn = sqlite3.connect(target_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def get_db_cursor(db_path: str = None) -> Generator[sqlite3.Cursor, None, None]:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str = None) -> None:
    """Initializes SQLite schema if not already present."""
    target_path = db_path or get_db_path()
    conn = sqlite3.connect(target_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # Accounts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id TEXT PRIMARY KEY,
        account_number TEXT UNIQUE NOT NULL,
        bank_name TEXT NOT NULL,
        account_name TEXT NOT NULL,
        currency TEXT NOT NULL DEFAULT 'INR',
        current_balance REAL NOT NULL CHECK(current_balance >= 0),
        reserved_balance REAL NOT NULL DEFAULT 0.0 CHECK(reserved_balance >= 0),
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        version INTEGER NOT NULL DEFAULT 1,
        updated_at TEXT NOT NULL
    );
    """)

    # Suppliers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        gstin TEXT,
        pan TEXT,
        bank_account_number TEXT NOT NULL,
        bank_ifsc TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'APPROVED',
        risk_tier TEXT NOT NULL DEFAULT 'LOW',
        default_category TEXT NOT NULL DEFAULT 'IT Services',
        created_at TEXT NOT NULL
    );
    """)

    # Invoices table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id TEXT PRIMARY KEY,
        supplier_id TEXT NOT NULL,
        invoice_number TEXT NOT NULL,
        invoice_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        amount REAL NOT NULL CHECK(amount > 0),
        currency TEXT NOT NULL DEFAULT 'INR',
        status TEXT NOT NULL DEFAULT 'PENDING',
        description TEXT,
        paid_at TEXT,
        paid_transaction_id TEXT,
        version INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
    );
    """)

    # Proposals table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proposals (
        id TEXT PRIMARY KEY,
        proposal_type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        source TEXT NOT NULL DEFAULT 'MANUAL_ENTRY',
        account_id TEXT NOT NULL,
        total_amount REAL NOT NULL DEFAULT 0.0 CHECK(total_amount >= 0),
        currency TEXT NOT NULL DEFAULT 'INR',
        status TEXT NOT NULL DEFAULT 'DRAFT',
        version INTEGER NOT NULL DEFAULT 1,
        proposal_hash TEXT NOT NULL DEFAULT '',
        created_by TEXT NOT NULL DEFAULT 'finance_analyst',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(account_id) REFERENCES accounts(id)
    );
    """)

    # Proposed transactions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proposed_transactions (
        id TEXT PRIMARY KEY,
        proposal_id TEXT NOT NULL,
        proposal_version INTEGER NOT NULL DEFAULT 1,
        transaction_type TEXT NOT NULL DEFAULT 'SUPPLIER_PAYMENT',
        invoice_id TEXT,
        supplier_id TEXT,
        beneficiary_name TEXT NOT NULL,
        amount REAL NOT NULL CHECK(amount > 0),
        currency TEXT NOT NULL DEFAULT 'INR',
        proposed_payment_date TEXT NOT NULL,
        transaction_category TEXT NOT NULL DEFAULT 'General',
        description TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PROPOSED',
        created_at TEXT NOT NULL,
        FOREIGN KEY(proposal_id) REFERENCES proposals(id) ON DELETE CASCADE,
        FOREIGN KEY(invoice_id) REFERENCES invoices(id),
        FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
    );
    """)

    # Policies table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS policies (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        rule_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        is_mandatory INTEGER NOT NULL DEFAULT 0,
        is_active INTEGER NOT NULL DEFAULT 1,
        version INTEGER NOT NULL DEFAULT 1,
        parameters_json TEXT NOT NULL DEFAULT '{}',
        description TEXT NOT NULL,
        created_by TEXT NOT NULL DEFAULT 'system_admin',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # Simulation Previews table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS simulation_previews (
        id TEXT PRIMARY KEY,
        proposal_id TEXT NOT NULL,
        proposal_version INTEGER NOT NULL,
        proposal_hash TEXT NOT NULL,
        ledger_version INTEGER NOT NULL,
        ledger_state_hash TEXT NOT NULL,
        policy_version INTEGER NOT NULL DEFAULT 1,
        policy_set_hash TEXT NOT NULL,
        current_balance REAL NOT NULL,
        projected_balance REAL NOT NULL,
        reserved_balance REAL NOT NULL,
        available_balance_before REAL NOT NULL,
        available_balance_after REAL NOT NULL,
        total_outflow REAL NOT NULL,
        remaining_budget REAL NOT NULL DEFAULT 0.0,
        findings_json TEXT NOT NULL DEFAULT '[]',
        can_proceed INTEGER NOT NULL DEFAULT 1,
        requires_approval INTEGER NOT NULL DEFAULT 0,
        simulated_at TEXT NOT NULL,
        FOREIGN KEY(proposal_id) REFERENCES proposals(id)
    );
    """)

    # Approvals table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS approvals (
        id TEXT PRIMARY KEY,
        proposal_id TEXT NOT NULL,
        proposal_version INTEGER NOT NULL,
        proposal_hash TEXT NOT NULL,
        preview_id TEXT NOT NULL,
        preview_hash TEXT NOT NULL,
        ledger_state_hash TEXT NOT NULL,
        policy_set_hash TEXT NOT NULL,
        approver_id TEXT NOT NULL,
        approver_name TEXT NOT NULL,
        approver_role TEXT NOT NULL,
        decision TEXT NOT NULL,
        justification TEXT NOT NULL,
        created_at TEXT NOT NULL,
        is_valid INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY(proposal_id) REFERENCES proposals(id),
        FOREIGN KEY(preview_id) REFERENCES simulation_previews(id)
    );
    """)

    # Simulated Commits table (Enforces proposal_id UNIQUE for idempotency!)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS simulated_commits (
        id TEXT PRIMARY KEY,
        proposal_id TEXT UNIQUE NOT NULL,
        proposal_version INTEGER NOT NULL,
        approval_id TEXT,
        total_amount REAL NOT NULL,
        account_id TEXT NOT NULL,
        pre_commit_balance REAL NOT NULL,
        post_commit_balance REAL NOT NULL,
        commit_hash TEXT NOT NULL,
        committed_by TEXT NOT NULL,
        committed_at TEXT NOT NULL,
        FOREIGN KEY(proposal_id) REFERENCES proposals(id),
        FOREIGN KEY(account_id) REFERENCES accounts(id),
        FOREIGN KEY(approval_id) REFERENCES approvals(id)
    );
    """)

    # Audit Events table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_events (
        id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        event_type TEXT NOT NULL,
        proposal_id TEXT,
        actor TEXT NOT NULL,
        outcome TEXT NOT NULL,
        details_json TEXT NOT NULL DEFAULT '{}'
    );
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_proposal ON proposed_transactions(proposal_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_supplier ON invoices(supplier_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_proposal ON audit_events(proposal_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_type ON audit_events(event_type);")

    conn.commit()
    conn.close()
