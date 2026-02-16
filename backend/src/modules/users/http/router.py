"""Users API router."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from src.modules.auth.module import get_current_user_id
from src.modules.users.core.services import UserService
from src.modules.users.module import get_user_service
from src.modules.users.schemas import UpdateWalletRequest, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Retrieve the profile of the currently authenticated user.",
)
async def get_current_user(
    service: Annotated[UserService, Depends(get_user_service)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> UserResponse:
    """Get the current authenticated user's profile."""
    user = await service.get_user_by_id(user_id)
    return UserResponse.model_validate(user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user's wallet address",
    description="Update the wallet address of the currently authenticated user.",
)
async def update_current_user_wallet(
    request: UpdateWalletRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> UserResponse:
    """Update the current user's wallet address.

    The wallet address will be normalized to lowercase before storage.
    """
    user = await service.update_wallet_address(user_id, request.wallet_address)
    return UserResponse.model_validate(user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Retrieve a user's public profile by their ID.",
)
async def get_user_by_id(
    user_id: uuid.UUID,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """Get a user by their ID."""
    user = await service.get_user_by_id(user_id)
    return UserResponse.model_validate(user)
