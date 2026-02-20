# Worker Testing - Complete Guide

This guide provides step-by-step instructions for testing the blockchain synchronization worker locally.

## Prerequisites

- Docker & Docker Compose
- Foundry (forge CLI)
- PostgreSQL test database

## Quick Start

### 1. Start Anvil

```bash
cd backend
docker-compose up -d
```

Leave running - note the test accounts shown in output.

### 2. Deploy Contract

```bash
cd smart_contract
forge script script/Deploy.s.sol --rpc-url http://127.0.0.1:8545 --broadcast
```

Copy the deployed contract address from the output.

### 3. Configure Environment

```bash
cd backend/tests/
# Edit .env.test:
# - Set ESCROW_CONTRACT_ADDRESS=<address from step 2>
# - Set DATABASE_URL to your test database

# ALSO edit backend/src/config.py:
# - Set escrow_contract_address = "<address from step 2>"
```

> **Important**: The contract address must be set in **both** `.env.test` AND `backend/src/config.py`.

### 4. Setup Database and Users

```bash
cd backend
uv run alembic upgrade head

# Create test users
cd backend/tests/
uv run python integration/blockchain/setup_users.py
```

Expected output:
```
================================================================================
  Creating Test Users
================================================================================

✅ User: payer@test.com           | ID: 11111111-... | Wallet: 0xf39fd6e51aad...
✅ User: payee@test.com           | ID: 22222222-... | Wallet: 0x70997970c518...
✅ User: arbitrator@test.com      | ID: 33333333-... | Wallet: 0x3c44cdddb6a9...

================================================================================
  ✅ Test users created successfully!
================================================================================
```

### 5. Start API

```bash
# Terminal 2
cd backend
uv run uvicorn src.main:app
```

### 6. Start Worker

```bash
# Terminal 3
cd backend
uv run python -m src.modules.blockchain.worker.run_worker
```

### 7. Run Tests

```bash
# Terminal 4
cd backend/tests/
uv run python integration/blockchain/interact.py
```

### 8. Verify Results

```bash
cd backend/tests/
uv run python integration/blockchain/verify_worker.py
```

Expected: "All verifications passed!"

## Test Scenarios

The `interact.py` script runs these scenarios:

1. **Happy Path**: DRAFT → PENDING_FUNDING → CREATED → FUNDED → RELEASED
2. **Dispute Flow**: Agreement with arbitrator, dispute opened, arbitrator releases payment
3. **Refund Flow**: Dispute resolved with refund

## Troubleshooting

**Worker not processing:**
- Check worker logs for connection errors
- Verify RPC_URL connects to Anvil (http://127.0.0.1:8545)
- Ensure ESCROW_CONTRACT_ADDRESS is correct

**API calls failing:**
- Check if test users exist in database
- Verify API is running on localhost:8000
- Check API logs for errors

**Verification fails:**
- Wait 10-15 seconds for worker to catch up
- Check worker terminal for processing logs
- Query database directly to inspect state

## Clean Up for Repeat Tests

```bash
# 1. Stop worker (Ctrl+C)
# 2. Reset database
psql $DATABASE_URL -c "TRUNCATE onchain_events, agreements, disputes, users, chain_sync_state CASCADE;"
```
