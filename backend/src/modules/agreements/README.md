# Agreements Module

This module handles the lifecycle of payment agreements, including creation, listing, and retrieval of agreement details.

## Overview

Agreements are the core entities in TrustFlow's escrow system. They represent a contract between a Payer and a Payee, optionally involving an Arbitrator. The module manages the state transitions (DRAFT, CREATED, FUNDED, etc.) and ensures business rules are enforced.

## Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| POST | `/agreements` | Create a new draft agreement |
| GET | `/agreements` | List agreements where the user is a participant |
| GET | `/agreements/{agreement_id}` | Get agreement details by ID |

## Business Rules

1.  **Participants**:
    *   **Payer** and **Payee** cannot be the same user.
    *   Users can only access agreements they are a participant in (Payer, Payee, or Arbitrator).
2.  **Arbitration Policy**:
    *   `NONE`: No arbitrator involved. `arbitrator_id` must be null.
    *   `WITH_ARBITRATOR`: An arbitrator is required. `arbitrator_id` must be provided and valid.
3.  **Amounts**: Must be a positive value in Wei.
4.  **Identifiers**: Agreement IDs are 256-bit identifiers represented as `0x` followed by 64 hex characters.
5.  **Limits**:
    *   **Max Drafts**: A user can have at most 30 agreements in `DRAFT` status as a Payer.

## Authentication

All endpoints require authentication (JWT) via `src.modules.auth`. The authenticated user is automatically assigned as the Payer when creating an agreement.

## Example Usage

```bash
# Create a new agreement
curl -X POST http://localhost:8000/api/v1/agreements \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "payee_id": "00000000-0000-0000-0000-000000000002",
    "amount_wei": 1000000000000000000,
    "arbitration_policy": "NONE"
  }'

# List my agreements (optional status filter)
curl "http://localhost:8000/api/v1/agreements?status=DRAFT" \
  -H "Authorization: Bearer <token>"

# Get agreement details
curl http://localhost:8000/api/v1/agreements/0x123...abc \
  -H "Authorization: Bearer <token>"
```
