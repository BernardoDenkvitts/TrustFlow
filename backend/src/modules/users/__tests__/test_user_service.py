"""Unit tests for UserService."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.users.core.exceptions import (
    InvalidWalletAddressError,
    UserNotFoundError,
)
from src.modules.users.core.models import User
from src.modules.users.core.services import UserService


@pytest.fixture
def mock_repository() -> MagicMock:
    """Create a mock UserRepository."""
    return MagicMock()


@pytest.fixture
def user_service(mock_repository: MagicMock) -> UserService:
    """Create a UserService with mocked repository."""
    return UserService(mock_repository)


@pytest.fixture
def sample_user() -> User:
    """Create a sample user for testing."""
    user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email="test@example.com",
        wallet_address="0x1234567890abcdef1234567890abcdef12345678",
    )
    return user


class TestGetUserById:
    """Tests for UserService.get_user_by_id method."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(
        self,
        user_service: UserService,
        mock_repository: MagicMock,
        sample_user: User,
    ) -> None:
        """Should return user when found."""
        mock_repository.find_by_id = AsyncMock(return_value=sample_user)

        result = await user_service.get_user_by_id(sample_user.id)

        assert result == sample_user
        mock_repository.find_by_id.assert_awaited_once_with(sample_user.id)

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(
        self,
        user_service: UserService,
        mock_repository: MagicMock,
    ) -> None:
        """Should raise UserNotFoundError when user doesn't exist."""
        user_id = uuid.UUID("00000000-0000-0000-0000-000000000999")
        mock_repository.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(UserNotFoundError) as exc_info:
            await user_service.get_user_by_id(user_id)

        assert str(user_id) in str(exc_info.value)
        mock_repository.find_by_id.assert_awaited_once_with(user_id)


class TestUpdateWalletAddress:
    """Tests for UserService.update_wallet_address method."""

    @pytest.mark.asyncio
    async def test_update_wallet_address_success(
        self,
        user_service: UserService,
        mock_repository: MagicMock,
        sample_user: User,
    ) -> None:
        """Should update wallet address and normalize to lowercase."""
        new_wallet = "0xABCDEF1234567890ABCDEF1234567890ABCDEF12"
        normalized_wallet = new_wallet.lower()

        mock_repository.find_by_id = AsyncMock(return_value=sample_user)
        mock_repository.update_wallet_address = AsyncMock(return_value=sample_user)

        result = await user_service.update_wallet_address(sample_user.id, new_wallet)

        assert result == sample_user
        mock_repository.find_by_id.assert_awaited_once_with(sample_user.id)
        mock_repository.update_wallet_address.assert_awaited_once_with(
            sample_user, normalized_wallet
        )

    @pytest.mark.asyncio
    async def test_update_wallet_address_user_not_found(
        self,
        user_service: UserService,
        mock_repository: MagicMock,
    ) -> None:
        """Should raise UserNotFoundError when user doesn't exist."""
        user_id = uuid.UUID("00000000-0000-0000-0000-000000000999")
        mock_repository.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(UserNotFoundError):
            await user_service.update_wallet_address(
                user_id,
                "0x1234567890abcdef1234567890abcdef12345678",
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "invalid_wallet",
        [
            "invalid",
            "0x123",  # Too short
            "0x1234567890abcdef1234567890abcdef1234567890",  # Too long
            "0xGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",  # Invalid hex
            "1234567890abcdef1234567890abcdef12345678",  # Missing 0x
        ],
    )
    async def test_update_wallet_address_invalid_format(
        self,
        user_service: UserService,
        mock_repository: MagicMock,
        sample_user: User,
        invalid_wallet: str,
    ) -> None:
        """Should raise InvalidWalletAddressError for invalid formats."""
        mock_repository.find_by_id = AsyncMock(return_value=sample_user)

        with pytest.raises(InvalidWalletAddressError):
            await user_service.update_wallet_address(sample_user.id, invalid_wallet)
