"""Agreements API router."""


import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.modules.agreements.core.enums import AgreementStatus
from src.modules.agreements.core.services import AgreementService
from src.modules.agreements.module import get_agreement_service
from src.modules.agreements.schemas import (
    AgreementListResponse,
    AgreementResponse,
    CreateAgreementRequest,
)
from src.modules.auth.module import get_current_user_id

router = APIRouter(prefix="/agreements", tags=["agreements"])


@router.post(
    "",
    response_model=AgreementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agreement",
    description="Create a new draft agreement. The current user becomes the payer.",
)
async def create_agreement(
    request: CreateAgreementRequest,
    service: Annotated[AgreementService, Depends(get_agreement_service)],
    payer_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> AgreementResponse:
    """Create a new draft agreement."""
    agreement = await service.create_agreement(
        payer_id=payer_id,
        payee_id=request.payee_id,
        amount_wei=request.amount_wei,
        arbitration_policy=request.arbitration_policy,
        arbitrator_id=request.arbitrator_id,
    )

    return AgreementResponse.model_validate(agreement)


@router.get(
    "",
    response_model=AgreementListResponse,
    summary="List user's agreements",
    description="List all agreements where the current user is a participant.",
)
async def list_agreements(
    service: Annotated[AgreementService, Depends(get_agreement_service)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    status: Annotated[
        AgreementStatus | None,
        Query(description="Filter by agreement status"),
    ] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 10,
) -> AgreementListResponse:
    """List all agreements where the user is a participant."""
    agreements, total = await service.list_user_agreements(
        user_id, status, page, page_size
    )

    return AgreementListResponse(
        items=[AgreementResponse.model_validate(a) for a in agreements],
        total=total,
    )


@router.get(
    "/{agreement_id}",
    response_model=AgreementResponse,
    summary="Get agreement by ID",
    description="Get an agreement by its ID. User must be a participant.",
)
async def get_agreement(
    agreement_id: str,
    service: Annotated[AgreementService, Depends(get_agreement_service)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> AgreementResponse:
    """Get an agreement by ID."""
    agreement = await service.get_agreement_by_id(agreement_id, user_id)

    return AgreementResponse.model_validate(agreement)

