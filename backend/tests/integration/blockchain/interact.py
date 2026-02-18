"""
End-to-end test script for blockchain worker.

This script simulates complete user workflows by:
1. Calling FastAPI endpoints to create agreements
2. Interacting with the smart contract on local blockchain (Anvil)
3. Allowing the worker to process events
4. Verifying the results in the database

Usage:
    # Ensure Anvil, API, and Worker are running first
    uv run python tests/integration/blockchain/interact.py
"""

import asyncio
import os
import time
from typing import Any
from datetime import datetime, timedelta, timezone

import asyncpg
from jose import jwt
import requests
from dotenv import load_dotenv
from web3 import Web3
from web3.contract import Contract


# Load test environment variables
load_dotenv(".env.test")

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")
CONTRACT_ADDRESS = os.getenv("ESCROW_CONTRACT_ADDRESS")
DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Test wallets (Anvil default accounts)
PAYER_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
PAYEE_KEY = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
ARBITRATOR_KEY = "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a"

PAYER = w3.eth.account.from_key(PAYER_KEY)
PAYEE = w3.eth.account.from_key(PAYEE_KEY)
ARBITRATOR = w3.eth.account.from_key(ARBITRATOR_KEY)

# Contract ABI (minimal, only functions we need)
CONTRACT_ABI = [
    {
        "inputs": [
            {"name": "agreementId", "type": "bytes32"},
            {"name": "payee", "type": "address"},
            {"name": "arbitrator", "type": "address"},
            {"name": "amount", "type": "uint256"},
            {"name": "policy", "type": "uint8"}
        ],
        "name": "createAgreement",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "agreementId", "type": "bytes32"}],
        "name": "fund",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [{"name": "agreementId", "type": "bytes32"}],
        "name": "openDispute",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "agreementId", "type": "bytes32"}],
        "name": "release",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "agreementId", "type": "bytes32"}],
        "name": "refund",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]


def print_section(title: str) -> None:
    """Print section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


async def reset_blockchain_state() -> None:
    """Reset blockchain-related tables so the worker starts fresh."""
    print_section("Resetting Blockchain State")

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Order matters due to FK constraints
        deleted_events = await conn.execute("DELETE FROM onchain_events")
        deleted_sync = await conn.execute("DELETE FROM chain_sync_state")
        deleted_disputes = await conn.execute("DELETE FROM disputes")
        deleted_agreements = await conn.execute("DELETE FROM agreements")

        print(f"onchain_events:  {deleted_events}")
        print(f"chain_sync_state: {deleted_sync}")
        print(f"disputes:         {deleted_disputes}")
        print(f"agreements:       {deleted_agreements}")
        print("\nDatabase state reset complete!")
    finally:
        await conn.close()


def hex_to_bytes32(hex_str: str) -> bytes:
    """Convert hex string (0x-prefixed) to bytes32."""
    return bytes.fromhex(hex_str.removeprefix("0x").zfill(64))


def create_access_token(user_id: str) -> str:
    """Create a valid JWT access token for the test user."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {"sub": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def api_call(method: str, endpoint: str, token: str | None = None, **kwargs) -> dict[str, Any]:
    """Make API call and return JSON response.
    
    Args:
        method: HTTP method (GET, POST, etc)
        endpoint: API endpoint (e.g. /api/v1/agreements)
        token: Optional JWT token for Authorization header
        **kwargs: Additional arguments passed to requests.request
    """
    url = f"{API_BASE_URL}{endpoint}"
    headers = kwargs.pop("headers", {})
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    response = requests.request(method, url, headers=headers, **kwargs)
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        print(f"API Error: {e.response.status_code} - {e.response.text}")
        raise
        
    return response.json()


def send_transaction(contract: Contract, account: Any, function_name: str, *args, **tx_params) -> str:
    """Send a transaction and wait for receipt."""
    tx = getattr(contract.functions, function_name)(*args).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 300000,
        "gasPrice": w3.eth.gas_price,
        **tx_params
    })
    
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    status_icon = "✅" if receipt['status'] == 1 else "❌"
    print(f"  {function_name}() | TX: {tx_hash.hex()[:16]}... | Block: {receipt['blockNumber']} | Status: {status_icon}")
    
    if receipt['status'] != 1:
        print(f"  ERROR: Transaction {function_name} reverted!")
        # Try to get revert reason (basic attempt)
        try:
            w3.eth.call(tx, receipt['blockNumber'])
        except Exception as e:
            print(f"  Revert reason: {e}")
            
    # Mine extra blocks to satisfy worker confirmation requirement
    mine_blocks(2)
            
    return tx_hash.hex()
    
    
def mine_blocks(num_blocks: int) -> None:
    """Mine empty blocks to advance chain tip."""
    print(f"  Mining {num_blocks} empty blocks for confirmation...")
    for _ in range(num_blocks):
        w3.provider.make_request("evm_mine", [])


def scenario_happy_path(contract: Contract) -> None:
    """Test happy path: Create → Submit → createAgreement → fund → release."""
    print_section("Scenario 1: Happy Path (DRAFT → FUNDED → RELEASED)")
    
    payer_id = "11111111-1111-1111-1111-111111111111"
    token = create_access_token(payer_id)
    
    # Step 1: Create agreement via API
    print("Step 1: POST /agreements (DRAFT)")
    agreement_data = {
        "payee_id": "22222222-2222-2222-2222-222222222222",  # Matches setup_users.py
        "amount_wei": "1000000000000000000",  # 1 ETH
        "arbitration_policy": "NONE",
        "arbitrator_id": None
    }
    
    # Note: Run setup_users.py first to create these test users
    try:
        response = api_call("POST", "/api/v1/agreements", token=token, json=agreement_data)
        agreement_id = response["agreement_id"]
        print(f"  Created agreement {agreement_id}")
    except Exception as e:
        print(f"  Failed to create agreement: {e}")
        print("  Make sure the API is running and users exist")
        return
    
    # Step 2: Create agreement on-chain
    print("\nStep 2: createAgreement() on smart contract")
    agreement_id_bytes = hex_to_bytes32(agreement_id)
    send_transaction(
        contract, PAYER, "createAgreement",
        agreement_id_bytes,
        PAYEE.address,
        "0x0000000000000000000000000000000000000000",  # No arbitrator
        int(agreement_data["amount_wei"]),
        0  # ArbitrationPolicy.NONE
    )
    
    # Wait for worker to process
    print("\nWaiting 10 seconds for worker to process AgreementCreated event...")
    time.sleep(10)
    
    # Step 3: Fund agreement on-chain
    print("\nStep 3: fund() on smart contract")
    send_transaction(
        contract, PAYER, "fund",
        agreement_id_bytes,
        value=int(agreement_data["amount_wei"])
    )
    
    print("\nWaiting 10 seconds for worker to process PaymentFunded event...")
    time.sleep(10)
    
    # Step 4: Release payment
    print("\nStep 4: release() on smart contract")
    send_transaction(contract, PAYER, "release", agreement_id_bytes)
    
    print("\nWaiting 10 seconds for worker to process PaymentReleased event...")
    time.sleep(10)
    
    print(f"\nScenario 1 complete! Agreement {agreement_id} should be RELEASED")


def scenario_dispute_flow(contract: Contract) -> None:
    """Test dispute flow: Create → createAgreement → fund → dispute → arbitrator release."""
    print_section("Scenario 2: Dispute Flow (Arbitrator Releases Payment)")
    
    payer_id = "11111111-1111-1111-1111-111111111111"
    token = create_access_token(payer_id)
    
    print("Step 1: POST /agreements (DRAFT)")
    agreement_data = {
        "payee_id": "22222222-2222-2222-2222-222222222222",
        "amount_wei": "2000000000000000000",  # 2 ETH
        "arbitration_policy": "WITH_ARBITRATOR",
        "arbitrator_id": "33333333-3333-3333-3333-333333333333"
    }
    
    try:
        response = api_call("POST", "/api/v1/agreements", token=token, json=agreement_data)
        agreement_id = response["agreement_id"]
        print(f"  Created agreement {agreement_id}")
    except Exception as e:
        print(f"  API call failed: {e}")
        return
    
    agreement_id_bytes = hex_to_bytes32(agreement_id)
    
    print("\nStep 2: createAgreement() with arbitrator")
    send_transaction(
        contract, PAYER, "createAgreement",
        agreement_id_bytes,
        PAYEE.address,
        ARBITRATOR.address,
        int(agreement_data["amount_wei"]),
        1  # ArbitrationPolicy.WITH_ARBITRATOR
    )

    print("\nWaiting 10 seconds for worker to process AgreementCreated event...")
    time.sleep(10)
    
    print("\nStep 3: fund()")
    send_transaction(
        contract, PAYER, "fund",
        agreement_id_bytes,
        value=int(agreement_data["amount_wei"])
    )

    print("\nWaiting 10 seconds for worker to process PaymentFunded event...")
    time.sleep(10)
    
    print("\nStep 4: openDispute() by payer")
    send_transaction(contract, PAYER, "openDispute", agreement_id_bytes)
    
    time.sleep(10)
    
    print("\nStep 5: release() by arbitrator")
    send_transaction(contract, ARBITRATOR, "release", agreement_id_bytes)
    
    time.sleep(10)
    
    print(f"\nScenario 2 complete! Agreement {agreement_id} should be DISPUTED → RELEASED")


def scenario_refund_flow(contract: Contract) -> None:
    """Test refund flow: Create → createAgreement → fund → dispute → arbitrator refund."""
    print_section("Scenario 3: Refund Flow (Arbitrator Refunds Payer)")
    
    payer_id = "11111111-1111-1111-1111-111111111111"
    token = create_access_token(payer_id)
    
    print("Step 1: POST /agreements (DRAFT)")
    agreement_data = {
        "payee_id": "22222222-2222-2222-2222-222222222222",
        "amount_wei": "3000000000000000000",  # 3 ETH
        "arbitration_policy": "WITH_ARBITRATOR",
        "arbitrator_id": "33333333-3333-3333-3333-333333333333"
    }
    
    try:
        response = api_call("POST", "/api/v1/agreements", token=token, json=agreement_data)
        agreement_id = response["agreement_id"]
        print(f"  Created agreement {agreement_id}")
    except Exception as e:
        print(f"  API call failed: {e}")
        return
    
    agreement_id_bytes = hex_to_bytes32(agreement_id)
    
    print("\nStep 2: createAgreement() with arbitrator")
    send_transaction(
        contract, PAYER, "createAgreement",
        agreement_id_bytes,
        PAYEE.address,
        ARBITRATOR.address,
        int(agreement_data["amount_wei"]),
        1  # ArbitrationPolicy.WITH_ARBITRATOR
    )

    print("\nWaiting 10 seconds for worker to process AgreementCreated event...")
    time.sleep(10)
    
    print("\nStep 3: fund()")
    send_transaction(
        contract, PAYER, "fund",
        agreement_id_bytes,
        value=int(agreement_data["amount_wei"])
    )

    print("\nWaiting 10 seconds for worker to process PaymentFunded event...")
    time.sleep(10)
    
    print("\nStep 4: openDispute() by payer")
    send_transaction(contract, PAYER, "openDispute", agreement_id_bytes)
    
    time.sleep(10)
    
    print("\nStep 5: refund() by arbitrator")
    send_transaction(contract, ARBITRATOR, "refund", agreement_id_bytes)
    
    time.sleep(10)
    
    print(f"\nScenario 3 complete! Agreement {agreement_id} should be DISPUTED → REFUNDED")


def main() -> None:
    """Main test execution."""
    print_section("Blockchain Worker End-to-End Test Suite")
    
    if not CONTRACT_ADDRESS:
        print("ERROR: ESCROW_CONTRACT_ADDRESS not set in .env.test")
        print("Deploy the contract first and update .env.test")
        return
    
    if not w3.is_connected():
        print("ERROR: Cannot connect to Anvil RPC")
        print(f"Make sure Anvil is running on {RPC_URL}")
        return
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        response.raise_for_status()
    except Exception:
        print(f"ERROR: Cannot connect to API at {API_BASE_URL}")
        print("Make sure FastAPI is running")
        return
    
    print(f"Connected to Anvil (Chain ID: {w3.eth.chain_id})")
    print(f"Connected to API ({API_BASE_URL})")
    print(f"Contract: {CONTRACT_ADDRESS}")

    # Reset database state before running scenarios
    asyncio.run(reset_blockchain_state())
    
    # Initialize contract
    contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI)

    scenario_happy_path(contract)
    scenario_dispute_flow(contract)
    scenario_refund_flow(contract)
    
    print_section("Test Execution Complete")
    print("Now run verify_worker.py to check the results!")


if __name__ == "__main__":
    main()
