# Disputes Module

This module handles the management of disputes that arise within agreements. It tracks the status of disputes and records resolutions made by arbitrators.

## Overview

Disputes occur when a Payer or Payee contests an agreement. The full resolution lifecycle is split between two actors:

- **`ChainSyncWorker`** — listens for on-chain events and syncs state to the database. Upon detecting `PaymentReleased` / `PaymentRefunded`, it sets the `resolution`, `resolution_tx_hash`, and `status` on the dispute record.
- **Arbitrator (via API)** — after the on-chain resolution is detected and synced by the worker, the arbitrator submits a `justification` text through our API for audit purposes.

### Resolution Pipeline

```
1. (On-chain)  Payer or Payee opens dispute        → Worker syncs: creates Dispute (OPEN)
2. (On-chain)  Arbitrator resolves (release/refund) → Worker syncs: sets resolution + resolution_tx_hash + status (RESOLVED)
3. (API)       Arbitrator submits justification      → Our system: saves justification text
```

## Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| GET | `/agreements/{agreement_id}/dispute` | Get dispute details for a specific agreement |
| POST | `/agreements/{agreement_id}/dispute/resolve` | Submit arbitrator justification (after on-chain resolution) |

## Business Rules

1. **Creation**: Disputes are opened on-chain. The worker creates the dispute record in the database upon detecting a `DisputeOpened` event.
2. **One Dispute Per Agreement**: Only one dispute is supported per agreement.
3. **Access Control**:
    - Only participants (Payer, Payee, Arbitrator) can view dispute details.
    - Only the assigned **Arbitrator** of the agreement can submit a justification.
4. **Justification Submission**:
    - The dispute **must already be synced as resolved** (worker has detected the on-chain event and set `resolution`) before the arbitrator can submit a justification.
    - Justification can only be submitted **once** — overwriting is not allowed.
    - Resolution outcome (`RELEASE` or `REFUND`) and `resolution_tx_hash` are sourced exclusively from the blockchain event by the worker.

## Authentication

All endpoints require authentication (JWT) via `src.modules.auth`.

## Example Usage

```bash
# Get dispute details
curl http://localhost:8000/api/v1/agreements/0x123...abc/dispute \
  -H "Authorization: Bearer <token>"

# Submit justification (Arbitrator only, after the worker syncs the on-chain resolution)
curl -X POST http://localhost:8000/api/v1/agreements/0x123...abc/dispute/resolve \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "justification": "Payee provided valid proof of work."
  }'
```
