"""
Proposal and ProposedTransaction data models.
Strict Pydantic validation ensures bad amounts, missing fields, and unsupported types are rejected.
"""
from datetime import datetime, date
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class ProposalType(str, Enum):
    SUPPLIER_INVOICE = "SUPPLIER_INVOICE"
    EXPENSE_REIMBURSEMENT = "EXPENSE_REIMBURSEMENT"
    PAYMENT_BATCH = "PAYMENT_BATCH"


class TransactionType(str, Enum):
    SUPPLIER_PAYMENT = "SUPPLIER_PAYMENT"
    EXPENSE_REIMBURSEMENT = "EXPENSE_REIMBURSEMENT"
    PAYROLL = "PAYROLL"
    TAX = "TAX"


class ProposalStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    SIMULATED = "SIMULATED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REVALIDATING = "REVALIDATING"
    COMMITTED_SIMULATED = "COMMITTED_SIMULATED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    STALE = "STALE"
    FAILED = "FAILED"


class ProposedTransaction(BaseModel):
    id: str = Field(..., description="Unique transaction ID, e.g. TX-001")
    proposal_id: Optional[str] = Field(None, description="Linked proposal ID")
    proposal_version: int = Field(default=1, ge=1)
    transaction_type: TransactionType = Field(default=TransactionType.SUPPLIER_PAYMENT)
    invoice_id: Optional[str] = Field(None, description="Matching invoice code, if applicable")
    supplier_id: Optional[str] = Field(None, description="Payee supplier code, if applicable")
    beneficiary_name: str = Field(..., min_length=2, description="Target recipient name")
    amount: float = Field(..., gt=0.0, description="Transaction payment amount, must be positive")
    currency: str = Field(default="INR", description="Currency code, e.g. INR")
    proposed_payment_date: date = Field(..., description="Target execution date")
    transaction_category: str = Field(default="Vendor Settlement", description="Operational category")
    description: str = Field(..., min_length=3, description="Business justification or line item details")
    status: str = Field(default="PROPOSED")

    @field_validator("amount")
    @classmethod
    def validate_positive_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Payment amount must be strictly greater than zero.")
        return round(v, 2)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in ["INR", "USD", "EUR", "GBP"]:
            raise ValueError(f"Unsupported currency: {v}. Default supported currency is INR.")
        return v_upper


class ProposalCreate(BaseModel):
    title: str = Field(..., min_length=3, description="Descriptive proposal title")
    description: Optional[str] = Field(None, description="Business context")
    proposal_type: ProposalType = Field(default=ProposalType.PAYMENT_BATCH)
    account_id: str = Field(..., description="Source disbursement account ID")
    currency: str = Field(default="INR")
    source: str = Field(default="MANUAL_ENTRY", description="Origin: MANUAL_ENTRY, AI_AGENT, CSV_IMPORT")
    created_by: str = Field(default="finance_analyst")
    transactions: List[ProposedTransaction] = Field(..., min_length=1, description="List of proposed transactions")

    @model_validator(mode="after")
    def check_non_empty(self) -> "ProposalCreate":
        if not self.transactions:
            raise ValueError("A proposal must contain at least one proposed transaction.")
        return self


class Proposal(BaseModel):
    id: str = Field(..., description="Unique proposal identifier, e.g. PROP-2026-001")
    proposal_type: ProposalType
    title: str
    description: Optional[str] = None
    source: str = Field(default="MANUAL_ENTRY")
    account_id: str
    total_amount: float = Field(default=0.0, ge=0.0)
    currency: str = Field(default="INR")
    status: ProposalStatus = Field(default=ProposalStatus.DRAFT)
    version: int = Field(default=1, ge=1)
    proposal_hash: str = Field(default="")
    created_by: str = Field(default="finance_analyst")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    transactions: List[ProposedTransaction] = Field(default_factory=list)

    def calculate_total(self) -> float:
        return round(sum(tx.amount for tx in self.transactions), 2)
