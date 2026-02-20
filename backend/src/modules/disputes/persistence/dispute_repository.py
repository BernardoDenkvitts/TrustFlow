"""Dispute repository for database access."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.disputes.core.enums import DisputeResolution, DisputeStatus
from src.modules.disputes.core.exceptions import DisputeAlreadyExistsError
from src.modules.disputes.core.models import Dispute


class DisputeRepository:
    """Repository class for Dispute data access operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: The async database session.
        """
        self._session = session

    async def find_by_id(self, dispute_id: uuid.UUID) -> Dispute | None:
        """Find a dispute by its ID.

        Args:
            dispute_id: The dispute identifier.

        Returns:
            The Dispute entity if found, None otherwise.
        """
        stmt = select(Dispute).where(Dispute.id == dispute_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_agreement_id(self, agreement_id: str) -> Dispute | None:
        """Find a dispute by its agreement ID.

        Args:
            agreement_id: The agreement identifier.

        Returns:
            The Dispute entity if found, None otherwise.
        """
        stmt = select(Dispute).where(Dispute.agreement_id == agreement_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        agreement_id: str,
        opened_by: uuid.UUID,
    ) -> Dispute:
        """Create a new dispute.

        Args:
            agreement_id: The agreement identifier.
            opened_by: UUID of the user who opened the dispute.

        Returns:
            The created Dispute entity.

        Raises:
            DisputeAlreadyExistsError: If a dispute already exists for this agreement.
        """
        dispute = Dispute(
            agreement_id=agreement_id,
            opened_by=opened_by,
            status=DisputeStatus.OPEN,
        )
        self._session.add(dispute)
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            raise DisputeAlreadyExistsError(agreement_id) from e
        return dispute

    async def resolve(
        self,
        dispute: Dispute,
        resolution: DisputeResolution,
        justification: str | None,
        resolution_tx_hash: str,
    ) -> Dispute:
        """Resolve a dispute.

        Args:
            dispute: The dispute entity to resolve.
            resolution: The resolution outcome (RELEASE or REFUND).
            justification: The arbitrator's justification.
            resolution_tx_hash: The transaction hash from on-chain resolution.

        Returns:
            The updated Dispute entity.
        """
        dispute.status = DisputeStatus.RESOLVED
        dispute.resolution = resolution
        dispute.justification = justification
        dispute.resolution_tx_hash = resolution_tx_hash
        dispute.resolved_at = datetime.now()
        await self._session.flush()
        await self._session.refresh(dispute)
        return dispute

    async def set_justification(
        self,
        dispute: Dispute,
        justification: str,
    ) -> Dispute:
        """Set the arbitrator's justification on an already-synced dispute.

        Args:
            dispute: The dispute entity to update.
            justification: The arbitrator's reasoning for the resolution.

        Returns:
            The updated Dispute entity.
        """
        dispute.justification = justification
        await self._session.flush()
        await self._session.refresh(dispute)
        return dispute
