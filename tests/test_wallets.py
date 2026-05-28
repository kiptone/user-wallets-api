"""Tests for wallet API endpoints."""

import asyncio
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.models import Wallet
from app.schemas import OperationType


class TestWalletCreation:
    """Tests for wallet creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_wallet(self, async_client: AsyncClient):
        """Test creating a new wallet returns 201 with zero balance."""
        response = await async_client.post("/api/v1/wallets")

        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["balance"] == "0.00"
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_wallet_has_uuid(self, async_client: AsyncClient):
        """Test created wallet ID is a valid UUID format."""
        response = await async_client.post("/api/v1/wallets")
        data = response.json()

        # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        wallet_id = data["id"]
        assert len(wallet_id) == 36  # UUID string length
        assert wallet_id.count("-") == 4


class TestWalletRetrieval:
    """Tests for wallet balance retrieval endpoint."""

    @pytest.mark.asyncio
    async def test_get_wallet_success(self, async_client: AsyncClient):
        """Test getting an existing wallet returns 200 with balance."""
        # Create a wallet
        create_response = await async_client.post("/api/v1/wallets")
        wallet_id = create_response.json()["id"]

        # Get the wallet
        get_response = await async_client.get(f"/api/v1/wallets/{wallet_id}")

        assert get_response.status_code == 200
        data = get_response.json()

        assert data["id"] == wallet_id
        assert data["balance"] == "0.00"

    @pytest.mark.asyncio
    async def test_get_wallet_not_found(self, async_client: AsyncClient):
        """Test getting non-existent wallet returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await async_client.get(f"/api/v1/wallets/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestWalletOperations:
    """Tests for wallet deposit/withdraw operations."""

    @pytest.mark.asyncio
    async def test_deposit_operation(self, async_client: AsyncClient):
        """Test depositing money increases balance."""
        # Create wallet
        create_response = await async_client.post("/api/v1/wallets")
        wallet_id = create_response.json()["id"]

        # Deposit 1000
        operation_response = await async_client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": 25000},
        )

        assert operation_response.status_code == 200
        data = operation_response.json()

        assert data["id"] == wallet_id
        assert data["new_balance"] == "25000.00"
        assert data["operation_type"] == "DEPOSIT"
        assert data["amount"] == "25000.00"

    @pytest.mark.asyncio
    async def test_withdraw_operation_success(self, async_client: AsyncClient):
        """Test withdrawing money with sufficient funds."""
        # Create and deposit
        create_response = await async_client.post("/api/v1/wallets")
        wallet_id = create_response.json()["id"]

        await async_client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": 25000},
        )

        # Withdraw 500
        withdraw_response = await async_client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "WITHDRAW", "amount": 500},
        )

        assert withdraw_response.status_code == 200
        data = withdraw_response.json()

        assert data["new_balance"] == "24500.00"
        assert data["operation_type"] == "WITHDRAW"

    @pytest.mark.asyncio
    async def test_withdraw_insufficient_funds(self, async_client: AsyncClient):
        """Test withdrawing more than available balance returns 400."""
        # Create wallet
        create_response = await async_client.post("/api/v1/wallets")
        wallet_id = create_response.json()["id"]

        # Try to withdraw without deposit
        response = await async_client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "WITHDRAW", "amount": 100},
        )

        assert response.status_code == 400
        assert "insufficient" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_operation_with_invalid_amount(self, async_client: AsyncClient):
        """Test operation with negative or zero amount returns 422."""
        create_response = await async_client.post("/api/v1/wallets")
        wallet_id = create_response.json()["id"]

        # Try with zero amount
        response = await async_client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": 0},
        )

        assert response.status_code == 422  # Pydantic validation error

    @pytest.mark.asyncio
    async def test_operation_on_nonexistent_wallet(self, async_client: AsyncClient):
        """Test operation on non-existent wallet returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await async_client.post(
            f"/api/v1/wallets/{fake_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": 100},
        )

        assert response.status_code == 404


class TestConcurrency:
    """
    Tests for concurrent operations.

    These tests ensure that the database-level locking (SELECT ... FOR UPDATE)
    prevents race conditions and maintains balance consistency.
    """

    @pytest.mark.asyncio
    async def test_concurrent_deposits(self, async_client: AsyncClient):
        """
        Test concurrent deposits don't lose money.

        Scenario: 10 concurrent deposits of 100 to the same wallet.
        Expected: Final balance = 1000 (not less due to race conditions)
        """
        # Create wallet with initial balance
        create_response = await async_client.post("/api/v1/wallets")
        wallet_id = create_response.json()["id"]

        # Perform 10 concurrent deposits
        tasks = [
            async_client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={"operation_type": "DEPOSIT", "amount": 100},
            )
            for _ in range(10)
        ]

        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == 200

        # Check final balance
        final_response = await async_client.get(f"/api/v1/wallets/{wallet_id}")
        final_balance = Decimal(final_response.json()["balance"])

        assert final_balance == Decimal("25000.00")

    @pytest.mark.asyncio
    async def test_concurrent_withdrawals_with_insufficient_funds(
        self, async_client: AsyncClient
    ):
        """
        Test concurrent withdrawals with insufficient funds.

        Scenario: Wallet with balance 100.
                 10 concurrent withdrawal requests of 50 each.
        Expected: 2 succeed, 8 fail with 400 (insufficient funds)
                 Final balance = 0 (exactly 2 succeeded)

        This tests that the pessimistic locking prevents race conditions
        where multiple requests would think there's enough balance.
        """
        # Create wallet and deposit 100
        create_response = await async_client.post("/api/v1/wallets")
        wallet_id = create_response.json()["id"]

        await async_client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": 100},
        )

        # Perform 10 concurrent withdrawals of 50 each (each would deplete balance)
        tasks = [
            async_client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={"operation_type": "WITHDRAW", "amount": 50},
            )
            for _ in range(10)
        ]

        responses = await asyncio.gather(*tasks)

        # Count successes and failures
        successful = sum(1 for r in responses if r.status_code == 200)
        failed = sum(1 for r in responses if r.status_code == 400)

        # Exactly 2 should succeed (100 / 50), rest fail
        assert successful == 2
        assert failed == 8

        # Check final balance is 0
        final_response = await async_client.get(f"/api/v1/wallets/{wallet_id}")
        final_balance = Decimal(final_response.json()["balance"])
        assert final_balance == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_mixed_concurrent_operations(self, async_client: AsyncClient):
        """
        Test mix of concurrent deposits and withdrawals.

        Scenario: Wallet balance starts at 500.
                 5 deposits of 100 and 5 withdrawals of 100 (total 10 operations).
        Expected: Final balance = 500 (net change is 0)
        """
        # Create wallet with initial 500
        create_response = await async_client.post("/api/v1/wallets")
        wallet_id = create_response.json()["id"]

        await async_client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": 500},
        )

        # Create 5 deposit and 5 withdrawal tasks
        tasks = []
        for i in range(5):
            tasks.append(
                async_client.post(
                    f"/api/v1/wallets/{wallet_id}/operation",
                    json={"operation_type": "DEPOSIT", "amount": 100},
                )
            )
            tasks.append(
                async_client.post(
                    f"/api/v1/wallets/{wallet_id}/operation",
                    json={"operation_type": "WITHDRAW", "amount": 100},
                )
            )

        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == 200

        # Check final balance is still 500
        final_response = await async_client.get(f"/api/v1/wallets/{wallet_id}")
        final_balance = Decimal(final_response.json()["balance"])
        assert final_balance == Decimal("500.00")

    @pytest.mark.asyncio
    async def test_sequential_operations_correctness(self, async_client: AsyncClient):
        """
        Test that operations are applied sequentially and correctly.

        Scenario:
        - Start with 0
        - Deposit 100 -> 100
        - Withdraw 30 -> 70
        - Deposit 50 -> 120
        - Withdraw 20 -> 100
        """
        create_response = await async_client.post("/api/v1/wallets")
        wallet_id = create_response.json()["id"]

        operations = [
            ("DEPOSIT", 100),
            ("WITHDRAW", 30),
            ("DEPOSIT", 50),
            ("WITHDRAW", 20),
        ]

        expected_balance = Decimal("0.00")
        for op_type, amount in operations:
            response = await async_client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={"operation_type": op_type, "amount": amount},
            )

            assert response.status_code == 200

            if op_type == "DEPOSIT":
                expected_balance += Decimal(str(amount))
            else:
                expected_balance -= Decimal(str(amount))

            actual_balance = Decimal(response.json()["new_balance"])
            assert actual_balance == expected_balance

        # Final verification
        final_response = await async_client.get(f"/api/v1/wallets/{wallet_id}")
        assert Decimal(final_response.json()["balance"]) == expected_balance
