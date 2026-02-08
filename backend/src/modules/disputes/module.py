"""Disputes module wiring and dependency injection."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.agreements import get_agreement_repository
from src.modules.agreements.persistence import AgreementRepository
from src.modules.disputes.core.services import DisputeService
from src.modules.disputes.persistence import DisputeRepository
from src.shared.database.session import get_session


async def get_dispute_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncGenerator[DisputeRepository, None]:
    """Dependency that provides a DisputeRepository.

    Args:
        session: The async database session.

    Yields:
        A DisputeRepository instance.
    """
    yield DisputeRepository(session)


async def get_dispute_service(
    dispute_repository: Annotated[
        DisputeRepository, Depends(get_dispute_repository)
    ],
    agreement_repository: Annotated[
        AgreementRepository, Depends(get_agreement_repository)
    ],
) -> AsyncGenerator[DisputeService, None]:
    """Dependency that provides a DisputeService.

    Args:
        dispute_repository: The dispute repository.
        agreement_repository: The agreement repository for authorization checks.

    Yields:
        A DisputeService instance.
    """
    yield DisputeService(dispute_repository, agreement_repository)
