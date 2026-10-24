"""
Invoice data model.
"""
from datetime import datetime, date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class InvoiceStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    DISPUTED = "DISPUTED"


class Invoice(BaseModel):
    id: str = Field(..., description="Internal invoice identifier, e.g. INV-2026-0891")
    supplier_id: str = Field(..., description="Reference to supplier")
    invoice_number: str = Field(..., description="Vendor invoice reference number")
    invoice_date: date = Field(..., description="Date invoice was issued")
    due_date: date = Field(..., description="Payment due date")
    amount: float = Field(..., gt=0.0, description="Gross invoice amount")
    currency: str = Field(default="INR", description="Invoice currency")
    status: InvoiceStatus = Field(default=InvoiceStatus.PENDING)
    description: Optional[str] = Field(None, description="Invoice line item summary")
    paid_at: Optional[datetime] = None
    paid_transaction_id: Optional[str] = None
    version: int = Field(default=1, ge=1)
