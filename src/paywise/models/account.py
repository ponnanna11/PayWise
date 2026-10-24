"""
Account data model.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    CLOSED = "CLOSED"


class Account(BaseModel):
    id: str = Field(..., description="Unique account identifier, e.g. ACC-CORP-01")
    account_number: str = Field(..., description="Bank account number")
    bank_name: str = Field(..., description="Bank institution name")
    account_name: str = Field(..., description="Descriptive account label")
    currency: str = Field(default="INR", description="Account currency ISO-4217")
    current_balance: float = Field(..., ge=0.0, description="Current simulated cash ledger balance")
    reserved_balance: float = Field(default=0.0, ge=0.0, description="Mandatory reserve funds balance")
    status: AccountStatus = Field(default=AccountStatus.ACTIVE)
    version: int = Field(default=1, ge=1, description="Optimistic locking version")
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def available_funds(self) -> float:
        """Calculates liquid cash available after holding minimum reserved balance."""
        return max(0.0, round(self.current_balance - self.reserved_balance, 2))
