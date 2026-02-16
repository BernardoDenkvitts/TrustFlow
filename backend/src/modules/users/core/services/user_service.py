"""User service implementing business logic."""

import re
import uuid

from src.modules.users.core.enums.user_enums import OAuthProvider
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

    async def get_user_by_oauth(
        self, provider: OAuthProvider, oauth_id: str
    ) -> User | None:
        """Get a user by their OAuth provider and ID.

        Args:
            provider: The OAuth provider.
            oauth_id: The OAuth ID.

        Returns:
            The user entity if found, None otherwise.
        """
        return await self._repository.find_by_oauth(provider, oauth_id)

    async def get_user_by_email(self, email: str) -> User | None:
        """Get a user by their email.

        Args:
            email: The email address.

        Returns:
            The user entity if found, None otherwise.
        """
        return await self._repository.find_by_email(email)

    async def create_user_oauth(
        self, email: str, oauth_provider: OAuthProvider, oauth_id: str
    ) -> User:
        """Create a new user via OAuth.

        Args:
            email: The user's email address.
            oauth_provider: The OAuth provider.
            oauth_id: The OAuth ID.

        Returns:
            The created user entity.

        Raises:
            UserAlreadyExistsError: If a user with the same email exists.
        """
        # Generate a new UUID for the user
        user_id = uuid.uuid4()

        return await self._repository.create(
            user_id=user_id,
            email=email,
            oauth_provider=oauth_provider,
            oauth_id=oauth_id,
        )

    async def update_oauth_info(
        self, user_id: uuid.UUID, provider: OAuthProvider, oauth_id: str
    ) -> User:
        """Update a user's OAuth info.

        Args:
            user_id: The UUID of the user.
            provider: The OAuth provider.
            oauth_id: The OAuth ID.

        Returns:
            The updated user entity.

        Raises:
            UserNotFoundError: If the user is not found.
        """
        user = await self._repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))

        return await self._repository.update_oauth_info(user, provider, oauth_id)
