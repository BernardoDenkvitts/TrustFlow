"""Dispute schemas for API request/response validation."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.modules.disputes.core.enums import DisputeResolution, DisputeStatus


class DisputeResponse(BaseModel):
    """Response schema for dispute data."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Unique dispute identifier")
    agreement_id: str = Field(description="Agreement ID this dispute belongs to")
    opened_by: uuid.UUID = Field(description="UUID of the user who opened the dispute")
    status: DisputeStatus = Field(description="Current status of the dispute")
    resolution: DisputeResolution | None = Field(
        description="Resolution outcome (if resolved)"
    )
    resolution_tx_hash: str | None = Field(
        description="Transaction hash of on-chain resolution"
    )
    justification: str | None = Field(
        description="Arbitrator's justification for the resolution"
    )
    opened_at: datetime = Field(description="When the dispute was opened")
    resolved_at: datetime | None = Field(description="When the dispute was resolved")


class SubmitJustificationRequest(BaseModel):
    """Request schema for submitting an arbitrator's justification."""

    justification: str = Field(
        description="Arbitrator's reasoning for the resolution",
        min_length=10,
        max_length=2000,
    )
