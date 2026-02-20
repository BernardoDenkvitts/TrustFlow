"""Disputes API router."""


import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from src.modules.auth.module import get_current_user_id
from src.modules.disputes.core.services import DisputeService
from src.modules.disputes.module import get_dispute_service
from src.modules.disputes.schemas import DisputeResponse, SubmitJustificationRequest

router = APIRouter(prefix="/agreements", tags=["disputes"])


@router.get(
    "/{agreement_id}/dispute",
    response_model=DisputeResponse,
    summary="Get dispute for agreement",
    description="Get the dispute details for an agreement. User must be a participant.",
)
async def get_dispute(
    agreement_id: str,
    service: Annotated[DisputeService, Depends(get_dispute_service)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> DisputeResponse:
    """Get the dispute for an agreement."""
    dispute = await service.get_dispute_for_agreement(agreement_id, user_id)

    return DisputeResponse.model_validate(dispute)


@router.post(
    "/{agreement_id}/dispute/resolve",
    response_model=DisputeResponse,
    summary="Submit dispute justification",
    description=(
        "Submit the arbitrator's justification for a resolved dispute. "
        "The dispute must already be resolved on-chain before this can be called."
    ),
)
async def submit_justification(
    agreement_id: str,
    request: SubmitJustificationRequest,
    service: Annotated[DisputeService, Depends(get_dispute_service)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> DisputeResponse:
    """Submit the arbitrator's justification for an on-chain resolved dispute."""
    dispute = await service.submit_justification(
        agreement_id=agreement_id,
        user_id=user_id,
        justification=request.justification,
    )

    return DisputeResponse.model_validate(dispute)
