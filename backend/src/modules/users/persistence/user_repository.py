"""User repository for database access."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

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

    async def create(self, user_id: uuid.UUID, email: str, wallet_address: str) -> User:
        """Create a new user.

        Args:
            user_id: The UUID for the new user (from Supabase Auth).
            email: The user's email address.
            wallet_address: The user's wallet address (will be normalized).

        Returns:
            The created user entity.

        Raises:
            UserAlreadyExistsError: If a user with the same email or wallet exists.
        """
        user = User(
            id=user_id,
            email=email,
            wallet_address=wallet_address.lower(),
        )
        self._session.add(user)

        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            error_msg = str(e.orig)
            if "email" in error_msg:
                raise UserAlreadyExistsError("email", email) from e
            if "wallet_address" in error_msg:
                raise UserAlreadyExistsError("wallet_address", wallet_address) from e
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

