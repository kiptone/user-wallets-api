"""
API endpoints for wallet operations.
"""

from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    OperationRequest,
    OperationResponse,
    OperationType,
    WalletResponse,
)
from app.services import (
    InsufficientFundsError,
    WalletNotFoundError,
    WalletService,
)

router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])


@router.post(
    "",
    response_model=WalletResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new wallet",
    responses={201: {"description": "Wallet created successfully"}},
)
async def create_wallet(
    session: AsyncSession = Depends(get_db),
) -> WalletResponse:
    """
    Create a new wallet with zero balance.

    Returns:
        WalletResponse: Created wallet data
    """
    wallet = await WalletService.create_wallet(session)
    return WalletResponse.model_validate(wallet)


@router.get(
    "/{wallet_id}",
    response_model=WalletResponse,
    status_code=status.HTTP_200_OK,
    summary="Get wallet balance",
    responses={
        200: {"description": "Wallet found"},
        404: {"description": "Wallet not found"},
    },
)
async def get_wallet_balance(
    wallet_id: str,
    session: AsyncSession = Depends(get_db),
) -> WalletResponse:
    """
    Get current balance of a wallet.

    Args:
        wallet_id: Wallet UUID
        session: Database session (injected by FastAPI)

    Returns:
        WalletResponse: Wallet data with current balance

    Raises:
        HTTPException: 404 if wallet not found
    """
    try:
        wallet = await WalletService.get_wallet(session, wallet_id)
        return WalletResponse.model_validate(wallet)
    except WalletNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/{wallet_id}/operation",
    response_model=OperationResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform wallet operation",
    responses={
        200: {"description": "Operation successful"},
        400: {"description": "Invalid operation (insufficient funds, invalid amount)"},
        404: {"description": "Wallet not found"},
    },
)
async def perform_operation(
    wallet_id: str,
    operation: OperationRequest,
    session: AsyncSession = Depends(get_db),
) -> OperationResponse:
    """
    Perform a DEPOSIT or WITHDRAW operation on a wallet.

    This endpoint handles concurrent requests safely using database-level locking.
    Multiple simultaneous requests to the same wallet are processed sequentially,
    ensuring no race conditions occur.

    Args:
        wallet_id: Wallet UUID
        operation: OperationRequest with operation_type and amount
        session: Database session (injected by FastAPI)

    Returns:
        OperationResponse: Operation details and new balance

    Raises:
        HTTPException:
            - 404 if wallet not found
            - 400 if insufficient funds for WITHDRAW
            - 400 if invalid amount

    Example:
        POST /api/v1/wallets/123e4567-e89b-12d3-a456-426614174000/operation
        {
            "operation_type": "DEPOSIT",
            "amount": 1000.00
        }

        Response:
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "new_balance": 1000.00,
            "operation_type": "DEPOSIT",
            "amount": 1000.00,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    """
    try:
        # Process operation with database-level locking
        wallet = await WalletService.process_operation(
            session=session,
            wallet_id=wallet_id,
            operation_type=operation.operation_type,
            amount=operation.amount,
        )

        # Return operation response
        return OperationResponse(
            id=wallet.id,
            new_balance=wallet.balance,
            operation_type=operation.operation_type,
            amount=operation.amount,
            timestamp=wallet.updated_at,
        )

    except WalletNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InsufficientFundsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
