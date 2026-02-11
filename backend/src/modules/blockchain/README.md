# Blockchain Module

This module handles the synchronization between the TrustFlow Escrow smart contract and the off-chain database.

## Overview

The Blockchain module runs a background worker that polls the Ethereum-compatible blockchain for events emitted by the Escrow contract. It ensures that the state of Agreements and Disputes in the database reflects the on-chain reality.

## Architecture

### Why a Separate Process?

The worker runs as an **independent process** from the FastAPI application so that FastAPI can scale horizontally with `--workers N` without duplicate blockchain processing

## Components

### 1. ChainSyncWorker
- Connects to the RPC URL specified in settings.
- Polls for logs in batches (default 1000 blocks).
- Handles reorgs by keeping a "safe" confirmation margin.
- Decodes raw logs into structured event data.
- **Polling**: Worker polls the blockchain RPC every `SYNC_INTERVAL_SECONDS`
- **Batch Processing**: Processes up to 1000 blocks per batch for efficiency
- **Catch-up Mode**: When behind, processes multiple batches per DB session (up to 20 batches)
- **State Tracking**: Stores last processed block in `chain_sync_state` table

### 2. BlockchainEventService
- Receives decoded events from the worker.
- Guarantees idempotency using `OnchainEvent` unique constraints.
- Updates `Agreement` status based on events.
- Creates/Resolves `Dispute` records automatically.

### 3. run_worker.py
- Standalone script to run the worker as a separate process
- Handles graceful shutdown on SIGINT/SIGTERM

## Database

The worker interacts with the following tables:

- **`chain_sync_state`**: Tracks sync progress per chain/contract
- **`onchain_events`**: Stores raw blockchain events with unique constraint on `(chain_id, tx_hash, log_index)`
- **`agreements`**: Updated based on contract events
- **`disputes`**: Updated based on dispute events
- **`users`**: Created/updated based on user participation

## Event Processing Rules

| Event Name | Action | Details |
|------------|--------|---------|
| `AgreementCreated` | Update Status | Sets Agreement status to `CREATED`. |
| `PaymentFunded` | Update Status | Sets Agreement status to `FUNDED`. |
| `DisputeOpened` | Create Dispute | Sets Agreement to `DISPUTED` and creates a standard Dispute record. |
| `PaymentReleased` | Resolve Dispute | Sets Agreement to `RELEASED`. If a dispute exists, marks it as resolved by RELEASE. |
| `PaymentRefunded` | Resolve Dispute | Sets Agreement to `REFUNDED`. If a dispute exists, marks it as resolved by REFUND. |

## Idempotency

The module is designed to be replay-safe:
- All events are stored in the `onchain_events` table with a unique constraint on `(chain_id, tx_hash, log_index)`.
- If an event is re-processed, the service detects the duplicate and skips business logic execution.
- Uses `ON CONFLICT DO NOTHING` to safely handle duplicate events

## Running the Worker

Run the worker and API in separate terminals:

```bash
# Terminal 1: Run the blockchain sync worker
python -m src.modules.blockchain.worker.run_worker

# Terminal 2: Run the FastAPI application
uvicorn src.main:app --reload
```

**Important**: Only one instance of the worker should run to avoid duplicate processing, but the API can scale with multiple workers.

## Configuration

Environment variables (defined in `src/config.py`):

- `RPC_URL`: Blockchain RPC endpoint
- `ESCROW_CONTRACT_ADDRESS`: Address of the deployed TrustFlow contract
- `CHAIN_ID`: Expected Chain ID for validation
- `SYNC_INTERVAL_SECONDS`: Polling interval in seconds (default: 12)
- `CONFIRMATIONS`: Number of confirmations to wait (default: 3)

## Error Handling

- **Transient Errors**: Worker logs and retries on next interval
- **Fatal Errors**: Worker logs and exits (process manager should restart)
- **Duplicate Events**: Silently ignored via database constraints
- **Invalid Events**: Logged and skipped, doesn't halt processing

## Monitoring

The worker provides structured logging:

- `INFO`: Batch completions, state updates, startup/shutdown
- `ERROR`: Connection failures, processing errors
- `DEBUG`: Block ranges, individual event details
