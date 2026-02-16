"""User schemas for API request/response validation."""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Wallet address regex pattern:
# 0x followed by 40 hex characters (case-insensitive input)
WALLET_ADDRESS_PATTERN = re.compile(r"^0x[0-9a-fA-F]{40}$")


class UserResponse(BaseModel):
    """Response schema for user data."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(
        description="User's unique identifier (same as Supabase Auth)"
    )
    email: str = Field(description="User's email address")
    wallet_address: str | None = Field(
        description="User's Ethereum wallet address (lowercase normalized)"
    )
    created_at: datetime = Field(description="When the user was created")
    updated_at: datetime = Field(description="When the user was last updated")


class UpdateWalletRequest(BaseModel):
    """Request schema for updating a user's wallet address."""

    wallet_address: str = Field(
        min_length=42,
        max_length=42,
        description="New Ethereum wallet address (0x + 40 hex characters)",
        examples=["0x1234567890abcdef1234567890abcdef12345678"],
    )

    @field_validator("wallet_address")
    @classmethod
    def validate_wallet_address(cls, v: str) -> str:
        """Validate wallet address format."""
        if not WALLET_ADDRESS_PATTERN.match(v):
            raise ValueError(
                "Invalid wallet address format. "
                "Expected: 0x followed by 40 hex characters"
            )
        return v.lower()  # Normalize to lowercase
