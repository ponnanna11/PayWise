"""
Supplier payee data model.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SupplierStatus(str, Enum):
    APPROVED = "APPROVED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    SUSPENDED = "SUSPENDED"
    INACTIVE = "INACTIVE"


class RiskTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Supplier(BaseModel):
    id: str = Field(..., description="Unique supplier code, e.g. SUP-IND-101")
    name: str = Field(..., min_length=2, description="Registered legal name")
    gstin: Optional[str] = Field(None, description="15-character Indian GSTIN")
    pan: Optional[str] = Field(None, description="10-character PAN")
    bank_account_number: str = Field(..., description="Designated bank account number")
    bank_ifsc: str = Field(..., description="Bank IFSC code, e.g. HDFC0000123")
    status: SupplierStatus = Field(default=SupplierStatus.APPROVED)
    risk_tier: RiskTier = Field(default=RiskTier.LOW)
    default_category: str = Field(default="IT Services", description="Default expense categorization")
    created_at: datetime = Field(default_factory=datetime.utcnow)
