"""Users module wiring and dependency injection."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.users.core.services import UserService
from src.modules.users.persistence import UserRepository
from src.shared.database.session import get_session


async def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncGenerator[UserRepository, None]:
    """Dependency that provides a UserRepository.

    Args:
        session: The async database session.

    Yields:
        A UserRepository instance.
    """
    yield UserRepository(session)


async def get_user_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> AsyncGenerator[UserService, None]:
    """Dependency that provides a UserService.

    Args:
        repository: The user repository.

    Yields:
        A UserService instance.
    """
    yield UserService(repository)
