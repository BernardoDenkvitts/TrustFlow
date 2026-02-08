"""Agreements API router."""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.modules.agreements.core.enums import AgreementStatus
from src.modules.agreements.core.services import AgreementService
from src.modules.agreements.module import get_agreement_service
from src.modules.agreements.schemas import (
    AgreementListResponse,
    AgreementResponse,
    CreateAgreementRequest,
)

router = APIRouter(prefix="/agreements", tags=["agreements"])


@router.post(
    "",
    response_model=AgreementResponse,
    status_code=201,
    summary="Create a new agreement",
    description="Create a new draft agreement. The current user becomes the payer.",
)
async def create_agreement(
    request: CreateAgreementRequest,
    service: Annotated[AgreementService, Depends(get_agreement_service)],
) -> AgreementResponse:
    """Create a new draft agreement."""
    # TODO: Replace with real user ID from JWT token
    from src.modules.users.http._mock_auth import get_mock_current_user_id

    payer_id = get_mock_current_user_id()

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
    status: Annotated[
        AgreementStatus | None,
        Query(description="Filter by agreement status"),
    ] = None,
) -> AgreementListResponse:
    """List all agreements where the user is a participant."""
    # TODO: Replace with real user ID from JWT token
    from src.modules.users.http._mock_auth import get_mock_current_user_id

    user_id = get_mock_current_user_id()

    agreements = await service.list_user_agreements(user_id, status)

    return AgreementListResponse(
        items=[AgreementResponse.model_validate(a) for a in agreements],
        total=len(agreements),
    )


@router.get(
    "/{agreement_id}",
    response_model=AgreementResponse,
    summary="Get agreement by ID",
    description="Get an agreement by its ID. User must be a participant.",
)
async def get_agreement(
    agreement_id: Decimal,
    service: Annotated[AgreementService, Depends(get_agreement_service)],
) -> AgreementResponse:
    """Get an agreement by ID."""
    # TODO: Replace with real user ID from JWT token
    from src.modules.users.http._mock_auth import get_mock_current_user_id

    user_id = get_mock_current_user_id()

    agreement = await service.get_agreement_by_id(agreement_id, user_id)

    return AgreementResponse.model_validate(agreement)


@router.post(
    "/{agreement_id}/submit",
    response_model=AgreementResponse,
    summary="Submit agreement for on-chain creation",
    description="Submit a draft agreement for on-chain creation (Locks agreement terms).",
)
async def submit_agreement(
    agreement_id: Decimal,
    service: Annotated[AgreementService, Depends(get_agreement_service)],
) -> AgreementResponse:
    """Locks agreement terms and awaits on-chain funding."""
    # TODO: Replace with real user ID from JWT token
    from src.modules.users.http._mock_auth import get_mock_current_user_id

    user_id = get_mock_current_user_id()

    agreement = await service.submit_agreement(agreement_id, user_id)

    return AgreementResponse.model_validate(agreement)
