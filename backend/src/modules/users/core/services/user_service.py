"""User service implementing business logic."""

import re
import uuid

from src.modules.users.core.exceptions import (
    InvalidWalletAddressError,
    UserNotFoundError,
)
from src.modules.users.core.models import User
from src.modules.users.persistence.user_repository import UserRepository

# Wallet address regex pattern: 0x followed by 40 lowercase hex characters
WALLET_ADDRESS_PATTERN = re.compile(r"^0x[0-9a-f]{40}$")


class UserService:
    """Service class for user-related business logic."""

    def __init__(self, repository: UserRepository) -> None:
        """Initialize the service with a repository.

        Args:
            repository: The user repository for data access.
        """
        self._repository = repository

    async def get_user_by_id(self, user_id: uuid.UUID) -> User:
        """Get a user by their ID.

        Args:
            user_id: The UUID of the user.

        Returns:
            The user entity.

        Raises:
            UserNotFoundError: If the user is not found.
        """
        user = await self._repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))
        return user

    async def update_wallet_address(
        self, user_id: uuid.UUID, wallet_address: str
    ) -> User:
        """Update a user's wallet address.

        Args:
            user_id: The UUID of the user.
            wallet_address: The new wallet address (will be normalized to lowercase).

        Returns:
            The updated user entity.

        Raises:
            UserNotFoundError: If the user is not found.
            InvalidWalletAddressError: If the wallet address format is invalid.
        """
        # Normalize wallet address to lowercase
        normalized_address = wallet_address.lower()

        # Validate wallet address format
        if not WALLET_ADDRESS_PATTERN.match(normalized_address):
            raise InvalidWalletAddressError(wallet_address)

        # Get existing user
        user = await self._repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))

        # Update wallet address
        updated_user = await self._repository.update_wallet_address(
            user, normalized_address
        )
        return updated_user
