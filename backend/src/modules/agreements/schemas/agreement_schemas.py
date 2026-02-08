"""Agreement schemas for API request/response validation."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.modules.agreements.core.enums import AgreementStatus, ArbitrationPolicy


class CreateAgreementRequest(BaseModel):
    """Request schema for creating a new agreement."""

    payee_id: uuid.UUID = Field(
        description="UUID of the payee who will receive the payment"
    )
    arbitrator_id: uuid.UUID | None = Field(
        default=None,
        description="UUID of the arbitrator (required if policy is WITH_ARBITRATOR)",
    )
    arbitration_policy: ArbitrationPolicy = Field(
        description="Arbitration policy for the agreement"
    )
    amount_wei: Decimal = Field(
        description="Amount in wei (must be positive)",
        examples=["1000000000000000000"],  # 1 ETH
    )

    @field_validator("amount_wei")
    @classmethod
    def validate_positive_amount(cls, v: Decimal) -> Decimal:
        """Validate that amount is positive."""
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


class AgreementResponse(BaseModel):
    """Response schema for agreement data."""

    model_config = ConfigDict(from_attributes=True)

    agreement_id: Decimal = Field(description="Unique agreement identifier (uint256)")
    payer_id: uuid.UUID = Field(description="UUID of the payer")
    payee_id: uuid.UUID = Field(description="UUID of the payee")
    arbitrator_id: uuid.UUID | None = Field(
        description="UUID of the arbitrator (if applicable)"
    )
    arbitration_policy: ArbitrationPolicy = Field(
        description="Arbitration policy for the agreement"
    )
    amount_wei: Decimal = Field(description="Amount in wei")
    status: AgreementStatus = Field(description="Current status of the agreement")

    # Transaction hashes
    created_tx_hash: str | None = Field(
        description="Transaction hash for on-chain creation"
    )
    funded_tx_hash: str | None = Field(
        description="Transaction hash for funding"
    )
    released_tx_hash: str | None = Field(
        description="Transaction hash for release"
    )
    refunded_tx_hash: str | None = Field(
        description="Transaction hash for refund"
    )

    # Blockchain timestamps
    created_onchain_at: datetime | None = Field(
        description="When the agreement was created on-chain"
    )
    funded_at: datetime | None = Field(
        description="When the agreement was funded"
    )
    released_at: datetime | None = Field(
        description="When the payment was released"
    )
    refunded_at: datetime | None = Field(
        description="When the payment was refunded"
    )

    # Database timestamps
    created_at: datetime = Field(description="When the agreement was created")
    updated_at: datetime = Field(description="When the agreement was last updated")


class AgreementListResponse(BaseModel):
    """Response schema for a list of agreements."""

    items: list[AgreementResponse] = Field(description="List of agreements")
    total: int = Field(description="Total number of agreements")
