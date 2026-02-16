"""Agreement repository for database access."""

import uuid
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.agreements.core.enums import AgreementStatus, ArbitrationPolicy
from src.modules.agreements.core.models import Agreement


class AgreementRepository:
    """Repository class for Agreement data access operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: The async database session.
        """
        self._session = session

    async def create(
        self,
        agreement_id: str,
        payer_id: uuid.UUID,
        payee_id: uuid.UUID,
        amount_wei: Decimal,
        arbitration_policy: ArbitrationPolicy,
        arbitrator_id: uuid.UUID | None = None,
    ) -> Agreement:
        """Create a new agreement.

        Args:
            agreement_id: Unique agreement identifier (uint256).
            payer_id: UUID of the payer.
            payee_id: UUID of the payee.
            amount_wei: Amount in wei.
            arbitration_policy: The arbitration policy.
            arbitrator_id: UUID of the arbitrator (if applicable).

        Returns:
            The created Agreement entity.
        """
        agreement = Agreement(
            agreement_id=agreement_id,
            payer_id=payer_id,
            payee_id=payee_id,
            amount_wei=amount_wei,
            arbitration_policy=arbitration_policy,
            arbitrator_id=arbitrator_id,
            status=AgreementStatus.DRAFT,
        )
        self._session.add(agreement)
        await self._session.flush()
        return agreement

    async def find_by_id(self, agreement_id: str) -> Agreement | None:
        """Find an agreement by its ID.

        Args:
            agreement_id: The agreement identifier.

        Returns:
            The Agreement entity if found, None otherwise.
        """
        stmt = select(Agreement).where(Agreement.agreement_id == agreement_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        status_filter: AgreementStatus | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[list[Agreement], int]:
        """List agreements where the user is a participant.

        A user is a participant if they are the payer, payee, or arbitrator.

        Args:
            user_id: The user's UUID.
            status_filter: Optional status to filter by.
            limit: Maximum number of agreements to return.
            offset: Number of agreements to skip.

        Returns:
            A tuple containing:
            - List of Agreement entities.
            - Total count of agreements matching the filter.
        """
        # Base condition
        where_clause = or_(
            Agreement.payer_id == user_id,
            Agreement.payee_id == user_id,
            Agreement.arbitrator_id == user_id,
        )

        if status_filter is not None:
            where_clause = (where_clause) & (Agreement.status == status_filter)

        # Count query
        count_stmt = select(func.count()).where(where_clause)
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        # Data query
        stmt = (
            select(Agreement)
            .where(where_clause)
            .order_by(Agreement.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def count_by_user_and_status(
        self,
        user_id: uuid.UUID,
        status: AgreementStatus,
    ) -> int:
        """Count agreements for a user with a specific status.

        Args:
            user_id: The user's UUID (checked against payer_id).
            status: The status to filter by.

        Returns:
            The count of agreements.
        """
        stmt = select(func.count()).where(
            Agreement.payer_id == user_id,
            Agreement.status == status,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def update_status(
        self,
        agreement: Agreement,
        new_status: AgreementStatus,
    ) -> Agreement:
        """Update the status of an agreement.

        Args:
            agreement: The agreement entity to update.
            new_status: The new status.

        Returns:
            The updated Agreement entity.
        """
        agreement.status = new_status
        await self._session.flush()
        await self._session.refresh(agreement)
        return agreement
