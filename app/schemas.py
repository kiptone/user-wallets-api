"""
Pydantic schemas for request/response validation.
"""

from decimal import Decimal
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class OperationType(str, Enum):
    """Enum for wallet operation types."""

    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class OperationRequest(BaseModel):
    """
    Schema for wallet operation requests.

    Attributes:
        operation_type: Either DEPOSIT or WITHDRAW
        amount: Non-negative amount for operation
    """

    operation_type: OperationType = Field(
        ..., description="Type of operation: DEPOSIT or WITHDRAW"
    )
    amount: Decimal = Field(
        ..., decimal_places=2, description="Amount for operation (positive)"
    )

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        """Validate that amount is positive."""
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


class WalletResponse(BaseModel):
    """
    Schema for wallet response.

    Attributes:
        id: Wallet UUID
        balance: Current balance
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: str = Field(..., description="Wallet UUID")
    balance: Decimal = Field(..., description="Current wallet balance")
    created_at: datetime = Field(..., description="Wallet creation time")
    updated_at: datetime = Field(..., description="Last update time")

    class Config:
        from_attributes = True  # Allow ORM model conversion


class OperationResponse(BaseModel):
    """
    Schema for operation response.

    Attributes:
        id: Wallet UUID
        new_balance: Balance after operation
        operation_type: Type of operation performed
        amount: Amount of operation
        timestamp: When operation was performed
    """

    id: str = Field(..., description="Wallet UUID")
    new_balance: Decimal = Field(..., description="Balance after operation")
    operation_type: OperationType = Field(..., description="Operation type")
    amount: Decimal = Field(..., description="Operation amount")
    timestamp: datetime = Field(..., description="Operation timestamp")


class ErrorResponse(BaseModel):
    """
    Schema for error responses.

    Attributes:
        status_code: HTTP status code
        message: Error message
    """

    status_code: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Error description")
