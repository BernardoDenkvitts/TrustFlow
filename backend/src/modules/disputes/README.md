# Disputes Module

This module handles the management of disputes that arise within agreements. It tracks the status of disputes and records resolutions made by arbitrators.

## Overview

Disputes occur when a Payer or Payee contests an agreement. In the TrustFlow system, the actual dispute opening and fund locking happen on-chain. This module synchronizes that state and provides an interface for Arbitrators to record their resolution decisions and justifications.

## Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| GET | `/agreements/{agreement_id}/dispute` | Get dispute details for a specific agreement |
| POST | `/agreements/{agreement_id}/dispute/resolve` | Record a dispute resolution (Arbitrator only) |

## Business Rules

1.  **Creation**: Disputes are primarily opened on-chain. The system reflects this state.
2.  **One Dispute Per Agreement**: Currently, only one dispute is supported per agreement.
3.  **Access Control**:
    *   Only participants (Payer, Payee, Arbitrator) can view dispute details.
    *   Only the assigned **Arbitrator** of the agreement can resolve the dispute.
4.  **Resolution**:
    *   Arbitrator must provide a justification.
    *   Arbitrator must provide the transaction hash of the on-chain resolution (`resolution_tx_hash`).
    *   Resolution outcome must be either `RELEASE` (funds to Payee) or `REFUND` (funds to Payer).

## Authentication

All endpoints require authentication (JWT) via `src.modules.auth`.

## Example Usage

```bash
# Get dispute details
curl http://localhost:8000/api/v1/agreements/0x123...abc/dispute \
  -H "Authorization: Bearer <token>"

# Resolve a dispute (Arbitrator only)
curl -X POST http://localhost:8000/api/v1/agreements/0x123...abc/dispute/resolve \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "resolution": "RELEASE",
    "justification": "Payee provided valid proof of work.",
    "resolution_tx_hash": "0xdef...456"
  }'
```
