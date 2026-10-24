"""
AI Provider and Agent Architecture for PayWise.
Implements the Gemini Flash High provider integration with deterministic fallback.
Treats all AI outputs as untrusted candidate proposals requiring schema validation,
simulation preview, policy evaluation, and human authorization.
"""
from abc import ABC, abstractmethod
from datetime import date, timedelta
import json
import logging
import re
from typing import Any, Dict, List, Optional

from paywise.config import AI_MODEL, AI_PROVIDER, GEMINI_API_KEY
from paywise.models.policy import PolicyRuleType, PolicySeverity
from paywise.models.proposal import ProposalCreate, ProposalType, ProposedTransaction, TransactionType

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    """Abstract interface for PayWise AI agent services."""

    @abstractmethod
    def check_health(self) -> Dict[str, Any]:
        """Returns health status, active model, and configuration diagnosis."""
        pass

    @abstractmethod
    def generate_proposal(
        self,
        instruction: str,
        account_id: str,
        available_suppliers: List[Dict[str, Any]],
        available_invoices: List[Dict[str, Any]],
    ) -> ProposalCreate:
        """Parses natural-language request into a candidate ProposalCreate."""
        pass

    @abstractmethod
    def explain_findings(
        self,
        findings: List[Dict[str, Any]],
        proposal_title: str,
        total_amount: float,
        projected_balance: float,
    ) -> str:
        """Generates executive natural-language explanation of policy findings."""
        pass

    @abstractmethod
    def draft_policy(self, instruction: str) -> Dict[str, Any]:
        """Translates a business rule instruction into an untrusted candidate policy schema."""
        pass


class GeminiProvider(BaseAIProvider):
    """Gemini Flash High API Provider using official google-genai SDK."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self._client = None
        if api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize google-genai client: {e}")

    def check_health(self) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "status": "UNCONFIGURED",
                "provider": "Google Gemini",
                "model": self.model_name,
                "message": "GEMINI_API_KEY is not configured in .env. Running in deterministic fallback mode.",
                "is_live": False,
            }
        if not self._client:
            return {
                "status": "ERROR",
                "provider": "Google Gemini",
                "model": self.model_name,
                "message": "google-genai client failed to initialize.",
                "is_live": False,
            }
        try:
            # Lightweight health check test
            response = self._client.models.generate_content(
                model=self.model_name,
                contents="Ping. Respond with 'PONG'.",
            )
            if response and response.text:
                return {
                    "status": "AVAILABLE",
                    "provider": "Google Gemini (Live)",
                    "model": self.model_name,
                    "message": f"Connected to {self.model_name} successfully.",
                    "is_live": True,
                }
            return {
                "status": "UNEXPECTED_RESPONSE",
                "provider": "Google Gemini",
                "model": self.model_name,
                "message": "No response text received from Gemini.",
                "is_live": False,
            }
        except Exception as e:
            return {
                "status": "CONNECTION_FAILED",
                "provider": "Google Gemini",
                "model": self.model_name,
                "message": f"Gemini API connection error: {type(e).__name__}",
                "is_live": False,
            }

    def generate_proposal(
        self,
        instruction: str,
        account_id: str,
        available_suppliers: List[Dict[str, Any]],
        available_invoices: List[Dict[str, Any]],
    ) -> ProposalCreate:
        if not self._client:
            raise RuntimeError("Gemini client is uninitialized.")

        prompt = f"""
You are an autonomous corporate financial operations assistant.
A business user provided this instruction:
"{instruction}"

Disbursement Account ID: {account_id}

Available Suppliers Directory:
{json.dumps([{ 'id': s.get('id'), 'name': s.get('name'), 'category': s.get('default_category') } for s in available_suppliers], indent=2)}

Available Invoices:
{json.dumps([{ 'id': i.get('id'), 'invoice_number': i.get('invoice_number'), 'supplier_id': i.get('supplier_id'), 'amount': i.get('amount'), 'status': i.get('status') } for i in available_invoices], indent=2)}

Task:
Generate a structured JSON object representing the payment proposal.
Return ONLY valid JSON matching this schema:
{{
  "title": "Short descriptive title",
  "description": "Business justification explaining what invoices or expenses are being paid",
  "proposal_type": "SUPPLIER_INVOICE" or "EXPENSE_REIMBURSEMENT" or "PAYMENT_BATCH",
  "transactions": [
    {{
      "beneficiary_name": "Exact Payee Name",
      "supplier_id": "SUP-... or null",
      "invoice_id": "INV-... or null",
      "amount": 10000.0,
      "currency": "INR",
      "proposed_payment_date": "{str(date.today() + timedelta(days=2))}",
      "transaction_category": "Category",
      "description": "Specific line item justification"
    }}
  ]
}}
Do not include any explanation outside the JSON code block.
"""
        response = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        text = response.text.strip()
        # Extract json if wrapped in ```json ... ```
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if json_match:
            text = json_match.group(1).strip()

        data = json.loads(text)

        tx_list = []
        for i, t in enumerate(data.get("transactions", [])):
            tx_date = date.today() + timedelta(days=2)
            if t.get("proposed_payment_date"):
                try:
                    tx_date = date.fromisoformat(str(t.get("proposed_payment_date")))
                except Exception:
                    pass

            tx_list.append(
                ProposedTransaction(
                    id=f"TX-GEMINI-{date.today().strftime('%Y%m%d')}-{i+1}",
                    transaction_type=TransactionType.SUPPLIER_PAYMENT if t.get("invoice_id") else TransactionType.EXPENSE_REIMBURSEMENT,
                    invoice_id=t.get("invoice_id"),
                    supplier_id=t.get("supplier_id"),
                    beneficiary_name=t.get("beneficiary_name", "Vendor Payee"),
                    amount=float(t.get("amount", 1000.0)),
                    currency=t.get("currency", "INR"),
                    proposed_payment_date=tx_date,
                    transaction_category=t.get("transaction_category", "Operational"),
                    description=t.get("description", "Gemini generated line item"),
                )
            )

        return ProposalCreate(
            title=data.get("title", f"Gemini Proposal: {instruction[:40]}"),
            description=data.get("description", f"AI-drafted proposal based on instruction: '{instruction}'"),
            proposal_type=ProposalType(data.get("proposal_type", "SUPPLIER_INVOICE")),
            account_id=account_id,
            currency="INR",
            source="GEMINI_FLASH_AGENT",
            created_by="gemini_agent",
            transactions=tx_list,
        )

    def explain_findings(
        self,
        findings: List[Dict[str, Any]],
        proposal_title: str,
        total_amount: float,
        projected_balance: float,
    ) -> str:
        if not self._client:
            raise RuntimeError("Gemini client is uninitialized.")

        prompt = f"""
You are PayWise's executive financial safety explainer.
A proposed payment batch "{proposal_title}" totaling ₹{total_amount:,.2f} resulted in a projected ledger balance of ₹{projected_balance:,.2f}.
The deterministic policy engine produced these findings:
{json.dumps(findings, indent=2)}

Provide a concise, professional executive briefing (3-4 bullet points) explaining:
1. The primary risk or barrier (BLOCK or REQUIRE_APPROVAL).
2. The specific financial impact (e.g. reserve shortfall, unapproved payee, duplicate invoice).
3. The recommended action for the CFO or finance operator.
Be factual, concise, and professional.
"""
        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            return f"Unable to generate Gemini summary: {e}"

    def draft_policy(self, instruction: str) -> Dict[str, Any]:
        if not self._client:
            raise RuntimeError("Gemini client is uninitialized.")

        prompt = f"""
You are a financial governance policy translator.
Translate this natural language business instruction into a structured policy definition:
"{instruction}"

Supported Rule Types:
- INSUFFICIENT_FUNDS
- MINIMUM_RESERVE_BREACH
- DUPLICATE_INVOICE_PAYMENT
- CANCELLED_OR_PAID_INVOICE
- UNAPPROVED_SUPPLIER
- AMOUNT_MISMATCH
- BATCH_BUDGET_EXCEEDED
- APPROVAL_THRESHOLD_EXCEEDED
- SPLIT_PAYMENT_DETECTION
- PAYMENT_DATE_SCHEDULING
- UNUSUAL_PAYMENT_ACTIVITY

Supported Severities:
- BLOCK
- REQUIRE_APPROVAL
- WARN

Return ONLY valid JSON matching this schema:
{{
  "name": "Short Policy Title",
  "rule_type": "EXACT_RULE_TYPE_FROM_LIST",
  "severity": "BLOCK" or "REQUIRE_APPROVAL" or "WARN",
  "parameters": {{ "threshold_amount": 50000.0 }},
  "description": "Clear explanation of what this rule enforces",
  "ai_interpretation": "Detailed human-readable explanation of how this policy applies"
}}
"""
        response = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        text = response.text.strip()
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if json_match:
            text = json_match.group(1).strip()

        data = json.loads(text)
        return {
            "id": f"POL-GEMINI-{abs(hash(instruction)) % 100000}",
            "name": data.get("name", "Gemini Drafted Policy"),
            "rule_type": data.get("rule_type", "APPROVAL_THRESHOLD_EXCEEDED"),
            "severity": data.get("severity", "REQUIRE_APPROVAL"),
            "parameters": data.get("parameters", {}),
            "description": data.get("description", instruction),
            "ai_interpretation": data.get("ai_interpretation", "Candidate rule drafted by Gemini."),
            "is_mandatory": False,
            "is_active": False,  # Safety invariant: Untrusted draft!
        }


class DeterministicFallbackProvider(BaseAIProvider):
    """
    Offline deterministic assistant.
    Provides reliable, repeatable parsing and explanation when Gemini API is unconfigured.
    Transparently labels source as DETERMINISTIC_FALLBACK.
    """

    def check_health(self) -> Dict[str, Any]:
        return {
            "status": "FALLBACK_ACTIVE",
            "provider": "Deterministic Fallback Assistant",
            "model": "Rule-Based Parser & Template Synthesizer",
            "message": "Operating offline without external API dependency. All core safety simulations functional.",
            "is_live": True,
        }

    def generate_proposal(
        self,
        instruction: str,
        account_id: str,
        available_suppliers: List[Dict[str, Any]],
        available_invoices: List[Dict[str, Any]],
    ) -> ProposalCreate:
        text = instruction.strip()

        # Extract amount
        amount_match = re.search(r"(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        amount = 25000.0
        if amount_match:
            try:
                amount = float(amount_match.group(1).replace(",", ""))
            except ValueError:
                pass

        # Match supplier
        matched_sup = None
        for sup in available_suppliers:
            name = sup.get("name", "").lower()
            sid = sup.get("id", "").lower()
            if name in text.lower() or sid in text.lower():
                matched_sup = sup
                break

        # Match invoice
        matched_inv = None
        for inv in available_invoices:
            inum = inv.get("invoice_number", "").lower()
            iid = inv.get("id", "").lower()
            if inum in text.lower() or iid in text.lower():
                matched_inv = inv
                break

        beneficiary = matched_sup.get("name") if matched_sup else "Designated Commercial Vendor"
        sup_id = matched_sup.get("id") if matched_sup else None
        inv_id = matched_inv.get("id") if matched_inv else None
        category = matched_sup.get("default_category", "IT Services") if matched_sup else "Operational Expense"

        if matched_inv:
            amount = float(matched_inv.get("amount", amount))

        today = date.today()
        tx = ProposedTransaction(
            id=f"TX-DET-{today.strftime('%Y%m%d')}-01",
            transaction_type=TransactionType.SUPPLIER_PAYMENT if inv_id else TransactionType.EXPENSE_REIMBURSEMENT,
            invoice_id=inv_id,
            supplier_id=sup_id,
            beneficiary_name=beneficiary,
            amount=amount,
            currency="INR",
            proposed_payment_date=today + timedelta(days=2),
            transaction_category=category,
            description=f"Fallback parser drafted disbursement based on: {text[:80]}",
            status="PROPOSED",
        )

        return ProposalCreate(
            title=f"Prepared Settlement: {beneficiary}",
            description=f"Draft payment proposal prepared by offline financial assistant. Context: {text}",
            proposal_type=ProposalType.SUPPLIER_INVOICE if inv_id else ProposalType.EXPENSE_REIMBURSEMENT,
            account_id=account_id,
            currency="INR",
            source="DETERMINISTIC_FALLBACK",
            created_by="deterministic_assistant",
            transactions=[tx],
        )

    def explain_findings(
        self,
        findings: List[Dict[str, Any]],
        proposal_title: str,
        total_amount: float,
        projected_balance: float,
    ) -> str:
        if not findings:
            return "All financial policies satisfied. No blocking violations or approval thresholds triggered."

        blocks = [f for f in findings if f.get("severity") == "BLOCK" or f.get("severity") == PolicySeverity.BLOCK]
        approvals = [f for f in findings if f.get("severity") == "REQUIRE_APPROVAL" or f.get("severity") == PolicySeverity.REQUIRE_APPROVAL]
        warns = [f for f in findings if f.get("severity") == "WARN" or f.get("severity") == PolicySeverity.WARN]

        summary_parts = []
        if blocks:
            summary_parts.append(
                f"🛑 **Critical Safety Blocks ({len(blocks)})**: This proposal cannot proceed. "
                + "; ".join(f"{b.get('rule_name', 'Rule')}: {b.get('explanation', '')}" for b in blocks)
            )
        if approvals:
            summary_parts.append(
                f"⚠️ **Authorization Required ({len(approvals)})**: Requires explicit sign-off from an authorized officer. "
                + "; ".join(f"{a.get('rule_name', 'Rule')}: {a.get('explanation', '')}" for a in approvals)
            )
        if warns:
            summary_parts.append(
                f"ℹ️ **Operational Warnings ({len(warns)})**: "
                + "; ".join(f"{w.get('rule_name', 'Rule')}: {w.get('explanation', '')}" for w in warns)
            )

        return "\n\n".join(summary_parts)

    def draft_policy(self, instruction: str) -> Dict[str, Any]:
        text = instruction.strip()
        threshold_match = re.search(r"(?:above|exceeding|over|greater than)\s*(?:₹|rs\.?|inr)?\s*([\d,]+)", text, re.IGNORECASE)
        amount = 50000.0
        if threshold_match:
            amount_str = threshold_match.group(1).replace(",", "")
            try:
                amount = float(amount_str)
            except ValueError:
                pass

        rule_type = PolicyRuleType.APPROVAL_THRESHOLD_EXCEEDED
        severity = PolicySeverity.REQUIRE_APPROVAL
        name = f"Approval Threshold for Payments > ₹{amount:,.0f}"
        params = {"threshold_amount": amount}
        explanation = f"Disbursements exceeding ₹{amount:,.0f} require explicit manager authorization."

        if any(w in text.lower() for w in ["batch", "budget", "ceiling", "aggregate"]):
            rule_type = PolicyRuleType.BATCH_BUDGET_EXCEEDED
            name = f"Batch Budget Ceiling ₹{amount:,.0f}"
            params = {"max_batch_amount": amount}
            explanation = f"Aggregate batch disbursements exceeding ₹{amount:,.0f} require executive approval."
        elif any(w in text.lower() for w in ["split", "evad", "structure"]):
            rule_type = PolicyRuleType.SPLIT_PAYMENT_DETECTION
            name = f"Split Payment Detection (Threshold ₹{amount:,.0f})"
            params = {"threshold_amount": amount, "window_days": 3}
            explanation = f"Detects multiple payments to same payee totaling above ₹{amount:,.0f} within 3 days."
        elif any(w in text.lower() for w in ["weekend", "holiday", "schedule", "past"]):
            rule_type = PolicyRuleType.PAYMENT_DATE_SCHEDULING
            severity = PolicySeverity.WARN
            name = "Disbursement Banking Schedule Compliance"
            params = {"allow_past_dates": False, "allow_weekends": False, "max_advance_days": 60}
            explanation = "Flags disbursements scheduled on weekends or in the past."

        return {
            "id": f"POL-CANDIDATE-{int(amount)}",
            "name": name,
            "rule_type": rule_type.value,
            "severity": severity.value,
            "parameters": params,
            "description": f"Draft policy based on: '{instruction}'",
            "ai_interpretation": explanation,
            "is_mandatory": False,
            "is_active": False,
        }


class AIAdapter:
    """
    Unified AI Integration Gateway.
    Selects GeminiProvider when configured; otherwise cleanly falls back to DeterministicFallbackProvider.
    """

    def __init__(self, provider_type: str = None, api_key: str = None, model: str = None):
        self.api_key = api_key if api_key is not None else GEMINI_API_KEY
        self.model = model or AI_MODEL
        self.provider_type = provider_type or AI_PROVIDER

        if self.provider_type == "gemini":
            self.provider = GeminiProvider(api_key=self.api_key or "", model_name=self.model)
        else:
            self.provider = DeterministicFallbackProvider()

    def check_health(self) -> Dict[str, Any]:
        return self.provider.check_health()

    def generate_proposal_from_prompt(
        self,
        prompt: str,
        account_id: str = "ACC-HDFC-MAIN",
        available_suppliers: List[Dict[str, Any]] = None,
        available_invoices: List[Dict[str, Any]] = None,
    ) -> ProposalCreate:
        try:
            return self.provider.generate_proposal(
                instruction=prompt,
                account_id=account_id,
                available_suppliers=available_suppliers or [],
                available_invoices=available_invoices or [],
            )
        except Exception as e:
            logger.warning(f"Primary AI provider failed: {e}. Falling back to deterministic assistant.")
            fallback = DeterministicFallbackProvider()
            return fallback.generate_proposal(
                instruction=prompt,
                account_id=account_id,
                available_suppliers=available_suppliers or [],
                available_invoices=available_invoices or [],
            )

    def explain_findings(
        self,
        findings: List[Any],
        proposal_title: str,
        total_amount: float,
        projected_balance: float,
    ) -> str:
        findings_dicts = [f.model_dump() if hasattr(f, "model_dump") else dict(f) for f in findings]
        try:
            return self.provider.explain_findings(
                findings=findings_dicts,
                proposal_title=proposal_title,
                total_amount=total_amount,
                projected_balance=projected_balance,
            )
        except Exception as e:
            fallback = DeterministicFallbackProvider()
            return fallback.explain_findings(
                findings=findings_dicts,
                proposal_title=proposal_title,
                total_amount=total_amount,
                projected_balance=projected_balance,
            )

    def draft_policy_from_text(self, natural_language_instruction: str) -> Dict[str, Any]:
        try:
            return self.provider.draft_policy(natural_language_instruction)
        except Exception as e:
            fallback = DeterministicFallbackProvider()
            return fallback.draft_policy(natural_language_instruction)
