"""
Business logic for wallet operations.
Handles concurrent access with database-level locking.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Wallet
from app.schemas import OperationType


class WalletNotFoundError(Exception):
    """Raised when wallet is not found."""

    pass


class InsufficientFundsError(Exception):
    """Raised when trying to withdraw more than available balance."""

    pass


class WalletService:
    """
    Service for wallet operations.
    Implements pessimistic locking for concurrent access safety.
    """

    @staticmethod
    async def create_wallet(session: AsyncSession) -> Wallet:
        """
        Create a new wallet with zero balance.

        Args:
            session: Database session

        Returns:
            Created Wallet object
        """
        wallet = Wallet()
        session.add(wallet)
        await session.commit()
        await session.refresh(wallet)
        return wallet

    @staticmethod
    async def get_wallet(session: AsyncSession, wallet_id: str) -> Wallet:
        """
        Get wallet by ID.

        Args:
            session: Database session
            wallet_id: Wallet UUID

        Returns:
            Wallet object

        Raises:
            WalletNotFoundError: If wallet not found
        """
        result = await session.execute(select(Wallet).where(Wallet.id == wallet_id))
        wallet = result.scalar_one_or_none()

        if wallet is None:
            raise WalletNotFoundError(f"Wallet {wallet_id} not found")

        return wallet

    @staticmethod
    async def process_operation(
        session: AsyncSession,
        wallet_id: str,
        operation_type: OperationType,
        amount: Decimal,
    ) -> Wallet:
        """
        Process a wallet operation (DEPOSIT or WITHDRAW).

        Uses SELECT ... FOR UPDATE to implement pessimistic locking.
        This ensures that concurrent operations on the same wallet
        don't cause race conditions or balance inconsistencies.

        Flow:
        1. Start explicit transaction
        2. Execute SELECT ... FOR UPDATE (locks the row)
        3. Read current balance
        4. Validate operation (e.g., sufficient funds for WITHDRAW)
        5. Update balance
        6. Commit transaction (releases lock)

        Args:
            session: Database session
            wallet_id: Wallet UUID
            operation_type: DEPOSIT or WITHDRAW
            amount: Operation amount (positive)

        Returns:
            Updated Wallet object

        Raises:
            WalletNotFoundError: If wallet doesn't exist
            InsufficientFundsError: If trying to withdraw more than available

        Example:
            # Even if 100 concurrent requests hit this endpoint,
            # each will wait for the previous one to complete.
            # This guarantees balance consistency.
            wallet = await WalletService.process_operation(
                session, "uuid-123", OperationType.WITHDRAW, Decimal("50.00")
            )
        """
        # Start explicit transaction
        async with session.begin():
            # SELECT ... FOR UPDATE: Lock the row at the database level
            # This prevents other transactions from reading/writing to this row
            # until our transaction commits
            result = await session.execute(
                select(Wallet)
                .where(Wallet.id == wallet_id)
                .with_for_update()  # CRITICAL: Pessimistic locking
            )
            wallet = result.scalar_one_or_none()

            if wallet is None:
                raise WalletNotFoundError(f"Wallet {wallet_id} not found")

            # Perform the operation
            if operation_type == OperationType.DEPOSIT:
                wallet.balance += amount
            elif operation_type == OperationType.WITHDRAW:
                # Check if sufficient funds AFTER acquiring lock
                if wallet.balance < amount:
                    raise InsufficientFundsError(
                        f"Insufficient funds. Current balance: {wallet.balance}, "
                        f"requested: {amount}"
                    )
                wallet.balance -= amount

            # Update timestamp
            wallet.updated_at = datetime.utcnow()

            # Session.commit() happens automatically when exiting `async with session.begin()`
            # The lock is released here

        # After commit, refresh to get the latest state
        await session.refresh(wallet)
        return wallet
