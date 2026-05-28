#!/usr/bin/env python3
"""
Quick test script for wallet API.
Run this to test the application manually.

Usage:
    python manual_test.py
"""

import asyncio
import httpx
from decimal import Decimal


async def main():
    """Run manual tests."""
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient() as client:
        print("=" * 50)
        print("User Wallets API - Manual Test")
        print("=" * 50)

        # 1. Health check
        print("\n1. Health check...")
        response = await client.get(f"{base_url}/health")
        print(f"   Status: {response.json()['status']}")

        # 2. Create wallet
        print("\n2. Creating wallet...")
        response = await client.post(f"{base_url}/api/v1/wallets")
        wallet = response.json()
        wallet_id = wallet["id"]
        print(f"   Created wallet: {wallet_id}")
        print(f"   Initial balance: {wallet['balance']}")

        # 3. Get wallet
        print("\n3. Getting wallet...")
        response = await client.get(f"{base_url}/api/v1/wallets/{wallet_id}")
        print(f"   Balance: {response.json()['balance']}")

        # 4. Deposit
        print("\n4. Depositing 1000...")
        response = await client.post(
            f"{base_url}/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": 1000},
        )
        data = response.json()
        print(f"   New balance: {data['new_balance']}")

        # 5. Withdraw
        print("\n5. Withdrawing 300...")
        response = await client.post(
            f"{base_url}/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "WITHDRAW", "amount": 300},
        )
        data = response.json()
        print(f"   New balance: {data['new_balance']}")

        # 6. Concurrent operations
        print("\n6. Testing concurrent operations (5 deposits of 100)...")
        tasks = [
            client.post(
                f"{base_url}/api/v1/wallets/{wallet_id}/operation",
                json={"operation_type": "DEPOSIT", "amount": 100},
            )
            for _ in range(5)
        ]
        responses = await asyncio.gather(*tasks)
        print(f"   All concurrent requests completed: {len(responses)}")

        # 7. Final balance
        print("\n7. Final balance check...")
        response = await client.get(f"{base_url}/api/v1/wallets/{wallet_id}")
        final_balance = Decimal(response.json()["balance"])
        expected = Decimal("1700.00")  # 1000 - 300 + 500 (5*100)
        print(f"   Final balance: {final_balance}")
        print(f"   Expected: {expected}")
        print(f"   Correct: {final_balance == expected}")

        print("\n" + "=" * 50)
        print("✓ All manual tests passed!")
        print("=" * 50)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nMake sure the application is running on http://localhost:8000")
        print("Run: docker-compose up -d")
