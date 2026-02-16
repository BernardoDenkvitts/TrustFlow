# Users Module

This module handles user profile management for TrustFlow.

## Overview

Users in TrustFlow are linked to Supabase Auth. This module manages the domain-specific user profile data (wallet address) separate from authentication.

## Endpoints

| Method | Path              | Description                         |
|--------|-------------------|-------------------------------------|
| GET    | `/users/me`       | Get current user's profile          |
| PUT    | `/users/me`       | Update current user's wallet address|
| GET    | `/users/{id}`     | Get user by ID                      |


## Business Rules

1. **Wallet Address Format**: Must be `0x` followed by 40 lowercase hex characters
2. **Unique Constraints**: Email and wallet address must be unique per user

## Authentication
 
Uses JWT validation via `src.modules.auth`.

## Example Usage

```bash
# Get current user
curl http://localhost:8000/api/v1/users/me

# Update wallet address
curl -X PUT http://localhost:8000/api/v1/users/me \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "0x1234567890abcdef1234567890abcdef12345678"}'

# Get user by ID
curl http://localhost:8000/api/v1/users/00000000-0000-0000-0000-000000000001
```
