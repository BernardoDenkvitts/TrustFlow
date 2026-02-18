"""
Setup script to create test users in the database.

This script creates the three test users needed for blockchain worker testing:
- Payer (matches _mock_auth.py MOCKED_USER_ID)
- Payee
- Arbitrator

Usage:
    python tests/integration/blockchain/setup_users.py
"""

import asyncio
import os

import asyncpg
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3


load_dotenv(".env.test")

DATABASE_URL = os.getenv("DATABASE_URL").replace("postgresql+asyncpg://", "postgresql://")

# Anvil default test accounts
PAYER_ADDRESS = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"  # Anvil account #0
PAYEE_ADDRESS = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"  # Anvil account #1
ARBITRATOR_ADDRESS = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"  # Anvil account #2

# Test user UUIDs (fixed for consistency)
MOCK_PAYER_ID = "11111111-1111-1111-1111-111111111111"
MOCK_PAYEE_ID = "22222222-2222-2222-2222-222222222222"
MOCK_ARBITRATOR_ID = "33333333-3333-3333-3333-333333333333"


async def create_test_users() -> None:
    """Create test users in the database."""
    print("=" * 80)
    print("  Creating Test Users")
    print("=" * 80)
    print()
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        users = [
            (MOCK_PAYER_ID, "payer@test.com", PAYER_ADDRESS.lower()),
            (MOCK_PAYEE_ID, "payee@test.com", PAYEE_ADDRESS.lower()),
            (MOCK_ARBITRATOR_ID, "arbitrator@test.com", ARBITRATOR_ADDRESS.lower()),
        ]
        
        for user_id, email, wallet in users:
            # Insert user if not exists
            query = """
                INSERT INTO users (id, email, wallet_address, oauth_provider, oauth_id, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                ON CONFLICT (email) DO UPDATE
                SET wallet_address = EXCLUDED.wallet_address
                RETURNING id
            """
            # Passing None for oauth_provider and oauth_id
            result = await conn.fetchval(query, user_id, email, wallet, None, None)
            
            if result:
                print(f"User: {email:25s} | ID: {user_id} | Wallet: {wallet[:16]}...")
        
        await conn.close()
        
        print()
        print("=" * 80)
        print("  Test users created successfully!")
        print("=" * 80)
        print()
        print("You can now run: python tests/integration/blockchain/interact.py")
        print()
        
    except Exception as e:
        print(f"Failed to create users: {e}")
        print()
        print("💡 Troubleshooting:")
        print("  1. Check DATABASE_URL in .env.test")
        print("  2. Ensure database is running and accessible")
        print("  3. Run migrations: alembic upgrade head")
        raise


if __name__ == "__main__":
    print("DATABASE_URL: ", DATABASE_URL)
    asyncio.run(create_test_users())
