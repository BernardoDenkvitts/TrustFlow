"""User repository for database access."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.users.core.enums.user_enums import OAuthProvider
from src.modules.users.core.exceptions import UserAlreadyExistsError
from src.modules.users.core.models import User


class UserRepository:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        """Find a user by their ID.

        Args:
            user_id: The UUID of the user.

        Returns:
            The user entity if found, None otherwise.
        """
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_email(self, email: str) -> User | None:
        """Find a user by their email.

        Args:
            email: The email address.

        Returns:
            The user entity if found, None otherwise.
        """
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_wallet_address(self, wallet_address: str) -> User | None:
        """Find a user by their wallet address.

        Args:
            wallet_address: The wallet address (lowercase normalized).

        Returns:
            The user entity if found, None otherwise.
        """
        stmt = select(User).where(User.wallet_address == wallet_address.lower())
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_oauth(
        self, provider: OAuthProvider, oauth_id: str
    ) -> User | None:
        """Find a user by their OAuth provider and ID.

        Args:
            provider: The OAuth provider.
            oauth_id: The provider's unique user ID.

        Returns:
            The user entity if found, None otherwise.
        """
        print(provider)
        print("ID", oauth_id)
        stmt = select(User).where(
            User.oauth_provider == provider,
            User.oauth_id == oauth_id,
        )
        print(stmt)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: uuid.UUID,
        email: str,
        wallet_address: str | None = None,
        oauth_provider: OAuthProvider | None = None,
        oauth_id: str | None = None,
    ) -> User:
        """Create a new user.

        Args:
            user_id: The UUID for the new user.
            email: The user's email address.
            wallet_address: The user's wallet address (lowercase normalized, optional).
            oauth_provider: The OAuth provider (optional).
            oauth_id: The OAuth ID (optional).

        Returns:
            The created user entity.

        Raises:
            UserAlreadyExistsError: If a user with the same email or wallet exists.
        """
        user = User(
            id=user_id,
            email=email,
            wallet_address=wallet_address.lower() if wallet_address else None,
            oauth_provider=oauth_provider,
            oauth_id=oauth_id,
        )
        self._session.add(user)

        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            error_msg = str(e.orig)
            if "email" in error_msg:
                raise UserAlreadyExistsError("email", email) from e
            if "wallet_address" in error_msg and wallet_address:
                raise UserAlreadyExistsError("wallet_address", wallet_address) from e
            if "oauth_id" in error_msg:
                raise UserAlreadyExistsError("oauth_id", str(oauth_id)) from e
            raise

        return user

    async def update_wallet_address(self, user: User, wallet_address: str) -> User:
        """Update a user's wallet address.

        Args:
            user: The user entity to update.
            wallet_address: The new wallet address (already normalized).

        Returns:
            The updated user entity.

        Raises:
            UserAlreadyExistsError: If another user has this wallet address.
        """
        user.wallet_address = wallet_address

        try:
            await self._session.flush()
            await self._session.refresh(user)  # Reload database-generated values
        except IntegrityError as e:
            await self._session.rollback()
            raise UserAlreadyExistsError("wallet_address", wallet_address) from e

        return user

    async def update_oauth_info(
        self, user: User, provider: OAuthProvider, oauth_id: str
    ) -> User:
        """Update a user's OAuth info.

        Args:
            user: The user entity to update.
            provider: The OAuth provider.
            oauth_id: The OAuth ID.

        Returns:
            The updated user entity.
        """
        user.oauth_provider = provider
        user.oauth_id = oauth_id

        try:
            await self._session.flush()
            await self._session.refresh(user)
        except IntegrityError as e:
            await self._session.rollback()
            raise UserAlreadyExistsError("oauth_id", oauth_id) from e

        return user
