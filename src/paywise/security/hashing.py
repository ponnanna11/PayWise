"""
Deterministic hashing utility for cryptographic binding in PayWise.
Produces repeatable SHA-256 hashes of canonical JSON representations.
"""
import hashlib
import json
from typing import Any, Dict, List


def canonical_json_dump(data: Any) -> str:
    """Serializes data into sorted, deterministic JSON without whitespace."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def compute_hash(data: Any) -> str:
    """Computes a SHA-256 hex digest for any JSON-serializable structure."""
    canonical_str = canonical_json_dump(data)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


def compute_proposal_hash(proposal_id: str, version: int, account_id: str, transactions: List[Dict[str, Any]]) -> str:
    """
    Computes deterministic hash of a proposal's content.
    Any alteration to transactions, amount, beneficiary, date, etc. will alter this hash.
    """
    simplified_txs = []
    for tx in transactions:
        simplified_txs.append({
            "id": tx.get("id"),
            "amount": float(tx.get("amount", 0.0)),
            "currency": tx.get("currency", "INR"),
            "beneficiary_name": tx.get("beneficiary_name"),
            "supplier_id": tx.get("supplier_id"),
            "invoice_id": tx.get("invoice_id"),
            "proposed_payment_date": tx.get("proposed_payment_date"),
            "transaction_category": tx.get("transaction_category"),
        })
    # Sort transactions by ID for deterministic order
    simplified_txs.sort(key=lambda x: str(x.get("id", "")))
    payload = {
        "proposal_id": proposal_id,
        "version": version,
        "account_id": account_id,
        "transactions": simplified_txs,
    }
    return compute_hash(payload)


def compute_ledger_state_hash(account_data: Dict[str, Any], relevant_invoices: List[Dict[str, Any]] = None) -> str:
    """
    Computes a hash of the current state of accounts and relevant invoices.
    If another transaction mutated the account balance or invoice status, this hash changes.
    """
    inv_data = []
    if relevant_invoices:
        for inv in relevant_invoices:
            inv_data.append({
                "id": inv.get("id"),
                "status": inv.get("status"),
                "amount": float(inv.get("amount", 0.0)),
                "version": inv.get("version", 1),
            })
        inv_data.sort(key=lambda x: str(x.get("id", "")))

    payload = {
        "account_id": account_data.get("id"),
        "current_balance": float(account_data.get("current_balance", 0.0)),
        "reserved_balance": float(account_data.get("reserved_balance", 0.0)),
        "version": account_data.get("version", 1),
        "invoices": inv_data,
    }
    return compute_hash(payload)


def compute_policy_set_hash(active_policies: List[Dict[str, Any]]) -> str:
    """
    Computes a hash of the current active policy definitions and parameters.
    If policies are added, deleted, disabled, or parameter thresholds change, hash changes.
    """
    simplified_pols = []
    for pol in active_policies:
        simplified_pols.append({
            "id": pol.get("id"),
            "rule_type": pol.get("rule_type"),
            "severity": pol.get("severity"),
            "is_active": pol.get("is_active"),
            "version": pol.get("version", 1),
            "parameters": pol.get("parameters", {}),
        })
    simplified_pols.sort(key=lambda x: str(x.get("id", "")))
    return compute_hash(simplified_pols)


def compute_preview_hash(preview_data: Dict[str, Any]) -> str:
    """Computes a hash of the simulation preview result."""
    payload = {
        "proposal_id": preview_data.get("proposal_id"),
        "proposal_version": preview_data.get("proposal_version"),
        "proposal_hash": preview_data.get("proposal_hash"),
        "current_balance": float(preview_data.get("current_balance", 0.0)),
        "projected_balance": float(preview_data.get("projected_balance", 0.0)),
        "total_outflow": float(preview_data.get("total_outflow", 0.0)),
        "findings_count": len(preview_data.get("findings", [])),
    }
    return compute_hash(payload)
