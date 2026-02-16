"""Disputes API router."""


import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from src.modules.auth.module import get_current_user_id
from src.modules.disputes.core.services import DisputeService
from src.modules.disputes.module import get_dispute_service
from src.modules.disputes.schemas import DisputeResponse, ResolveDisputeRequest

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
    summary="Resolve a dispute",
    description="Resolve a dispute. Only the arbitrator can resolve disputes.",
)
async def resolve_dispute(
    agreement_id: str,
    request: ResolveDisputeRequest,
    service: Annotated[DisputeService, Depends(get_dispute_service)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> DisputeResponse:
    """Resolve a dispute as the arbitrator."""
    dispute = await service.resolve_dispute(
        agreement_id=agreement_id,
        user_id=user_id,
        resolution=request.resolution,
        justification=request.justification,
        resolution_tx_hash=request.resolution_tx_hash,
    )

    return DisputeResponse.model_validate(dispute)
