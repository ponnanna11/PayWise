"""
Tests for AI Agent Provider, Gemini integration contracts, and untrusted safety boundaries.
"""
from datetime import date
import pytest
from pydantic import ValidationError
from paywise.models.proposal import ProposedTransaction
from paywise.services.ai_adapter import AIAdapter, DeterministicFallbackProvider, GeminiProvider


def test_ai_provider_health_check_unconfigured():
    """Scenario 19: Unconfigured or missing API key is reported transparently without crashing."""
    adapter = AIAdapter(provider_type="gemini", api_key="")
    health = adapter.check_health()
    assert health["status"] == "UNCONFIGURED"
    assert health["is_live"] is False
    assert "GEMINI_API_KEY" in health["message"]


def test_deterministic_fallback_health_check():
    """Scenario: Fallback assistant reports FALLBACK_ACTIVE without claiming to be live Gemini."""
    provider = DeterministicFallbackProvider()
    health = provider.check_health()
    assert health["status"] == "FALLBACK_ACTIVE"
    assert "Deterministic Fallback" in health["provider"]


def test_ai_generated_proposal_validation_contract():
    """Scenario 11: AI-generated proposal data must strictly validate via Pydantic schema."""
    adapter = AIAdapter(api_key="")
    suppliers = [{"id": "SUP-TCS-01", "name": "Tata Consultancy Services Ltd", "default_category": "Cloud"}]
    invoices = [{"id": "INV-2026-001", "invoice_number": "TCS-104", "amount": 185000.0}]

    candidate = adapter.generate_proposal_from_prompt(
        prompt="Prepare payment for TCS Cloud invoice TCS-104 of ₹185,000",
        account_id="ACC-HDFC-MAIN",
        available_suppliers=suppliers,
        available_invoices=invoices,
    )

    assert candidate.account_id == "ACC-HDFC-MAIN"
    assert candidate.source == "DETERMINISTIC_FALLBACK"
    assert candidate.created_by == "deterministic_assistant"
    assert len(candidate.transactions) == 1
    assert candidate.transactions[0].amount == 185000.0
    assert candidate.transactions[0].currency == "INR"


def test_ai_invalid_proposal_data_rejected():
    """Scenario 11: Malformed data from AI cannot bypass Pydantic validation."""
    with pytest.raises(ValidationError):
        ProposedTransaction(
            id="TX-BAD",
            beneficiary_name="V",  # Too short, min 2 chars
            amount=-500.0,         # Negative amount
            proposed_payment_date=date.today(),
            description="Bad",
        )


def test_ai_policy_draft_cannot_activate_without_human_action():
    """Scenario 20: AI-generated policies are untrusted drafts and cannot be active by default."""
    adapter = AIAdapter(api_key="")
    draft = adapter.draft_policy_from_text("Payments over ₹75,000 require CFO authorization.")

    assert draft["is_active"] is False  # Must NOT be active!
    assert draft["is_mandatory"] is False
    assert draft["parameters"]["threshold_amount"] == 75000.0
    assert draft["severity"] == "REQUIRE_APPROVAL"


def test_ai_explain_findings():
    """Scenario: AI provider synthesizes human-readable executive briefing of findings."""
    adapter = AIAdapter(api_key="")
    sample_findings = [
        {
            "rule_name": "Minimum Reserve Balance Breach",
            "severity": "BLOCK",
            "explanation": "Projected balance would fall below mandatory reserve of ₹5,00,000.",
        },
        {
            "rule_name": "Discretionary Approval Threshold",
            "severity": "REQUIRE_APPROVAL",
            "explanation": "Payment exceeds ₹50,000.",
        },
    ]

    briefing = adapter.explain_findings(
        findings=sample_findings,
        proposal_title="Vendor Expansion Payout",
        total_amount=600000.0,
        projected_balance=200000.0,
    )

    assert "Critical Safety Blocks" in briefing or "Reserve" in briefing
    assert "Authorization Required" in briefing or "Sign-off" in briefing
