"""Users API router."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

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
) -> UserResponse:
    """Get the current authenticated user's profile."""
    # TODO: Replace with real user ID from JWT token in from Supa Base Auth
    # For now, use a mocked user ID for testing
    from src.modules.users.http._mock_auth import get_mock_current_user_id

    user_id = get_mock_current_user_id()
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
) -> UserResponse:
    """Update the current user's wallet address.

    The wallet address will be normalized to lowercase before storage.
    """
    # TODO: Replace with real user ID from JWT token
    from src.modules.users.http._mock_auth import get_mock_current_user_id

    user_id = get_mock_current_user_id()
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
