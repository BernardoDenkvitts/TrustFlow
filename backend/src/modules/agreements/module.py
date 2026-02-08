"""Agreements module wiring and dependency injection."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.agreements.core.services import AgreementService
from src.modules.agreements.persistence import AgreementRepository
from src.modules.users import get_user_repository
from src.modules.users.persistence import UserRepository
from src.shared.database.session import get_session


async def get_agreement_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncGenerator[AgreementRepository, None]:
    """Dependency that provides an AgreementRepository.

    Args:
        session: The async database session.

    Yields:
        An AgreementRepository instance.
    """
    yield AgreementRepository(session)


async def get_agreement_service(
    agreement_repository: Annotated[
        AgreementRepository, Depends(get_agreement_repository)
    ],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> AsyncGenerator[AgreementService, None]:
    """Dependency that provides an AgreementService.

    Args:
        agreement_repository: The agreement repository.
        user_repository: The user repository for validating user existence.

    Yields:
        An AgreementService instance.
    """
    yield AgreementService(agreement_repository, user_repository)
