"""Dispute service implementing business logic."""

import uuid

from src.modules.agreements.core.exceptions import AgreementNotFoundError
from src.modules.agreements.persistence import AgreementRepository
from src.modules.disputes.core.enums import DisputeResolution, DisputeStatus
from src.modules.disputes.core.exceptions import (
    DisputeAlreadyResolvedError,
    DisputeNotFoundError,
    UnauthorizedArbitratorError,
    UnauthorizedDisputeAccessError,
)
from src.modules.disputes.core.models import Dispute
from src.modules.disputes.persistence import DisputeRepository


class DisputeService:
    """Service class for dispute-related business logic."""

    def __init__(
        self,
        dispute_repository: DisputeRepository,
        agreement_repository: AgreementRepository,
    ) -> None:
        """Initialize the service with repositories.

        Args:
            dispute_repository: The dispute repository for data access.
            agreement_repository: The agreement repository for authorization checks.
        """
        self._dispute_repo = dispute_repository
        self._agreement_repo = agreement_repository

    def _is_participant(
        self,
        agreement: object,
        user_id: uuid.UUID,
    ) -> bool:
        """Check if a user is a participant in an agreement.

        A participant is the payer, payee, or arbitrator.

        Args:
            agreement: The agreement to check.
            user_id: The user ID to check.

        Returns:
            True if the user is a participant, False otherwise.
        """
        return user_id in (
            agreement.payer_id,  # type: ignore[attr-defined]
            agreement.payee_id,  # type: ignore[attr-defined]
            agreement.arbitrator_id,  # type: ignore[attr-defined]
        )

    async def get_dispute_for_agreement(
        self,
        agreement_id: str,
        user_id: uuid.UUID,
    ) -> Dispute:
        """Get the dispute for an agreement.

        Args:
            agreement_id: The agreement identifier.
            user_id: The user requesting the dispute.

        Returns:
            The Dispute entity.

        Raises:
            AgreementNotFoundError: If the agreement doesn't exist.
            UnauthorizedDisputeAccessError: If user is not a participant.
            DisputeNotFoundError: If no dispute exists for the agreement.
        """
        # Verify agreement exists
        agreement = await self._agreement_repo.find_by_id(agreement_id)
        if agreement is None:
            raise AgreementNotFoundError(agreement_id)

        # Authorization: user must be a participant
        if not self._is_participant(agreement, user_id):
            raise UnauthorizedDisputeAccessError(str(user_id), agreement_id)

        # Get dispute
        dispute = await self._dispute_repo.find_by_agreement_id(agreement_id)
        if dispute is None:
            raise DisputeNotFoundError(agreement_id)

        return dispute

    async def resolve_dispute(
        self,
        agreement_id: str,
        user_id: uuid.UUID,
        resolution: DisputeResolution,
        justification: str,
        resolution_tx_hash: str,
    ) -> Dispute:
        """Resolve a dispute.

        Records the arbitrator's decision. This is for audit purposes only -
        the actual on-chain release/refund is executed separately.

        Args:
            agreement_id: The agreement identifier.
            user_id: The user resolving the dispute (must be arbitrator).
            resolution: The resolution outcome (RELEASE or REFUND).
            justification: The arbitrator's reasoning.
            resolution_tx_hash: The transaction hash from on-chain resolution.

        Returns:
            The updated Dispute entity.

        Raises:
            AgreementNotFoundError: If the agreement doesn't exist.
            UnauthorizedArbitratorError: If user is not the arbitrator.
            DisputeNotFoundError: If no dispute exists for the agreement.
            DisputeAlreadyResolvedError: If dispute is already resolved.
        """
        # Verify agreement exists
        agreement = await self._agreement_repo.find_by_id(agreement_id)
        if agreement is None:
            raise AgreementNotFoundError(agreement_id)

        # Authorization: user must be the arbitrator
        if agreement.arbitrator_id != user_id:
            raise UnauthorizedArbitratorError(str(user_id), agreement_id)

        # Get dispute
        dispute = await self._dispute_repo.find_by_agreement_id(agreement_id)
        if dispute is None:
            raise DisputeNotFoundError(agreement_id)

        # Verify dispute is still open
        if dispute.status != DisputeStatus.OPEN:
            raise DisputeAlreadyResolvedError(dispute.id)

        # Record resolution
        updated_dispute = await self._dispute_repo.resolve(
            dispute=dispute,
            resolution=resolution,
            justification=justification,
            resolution_tx_hash=resolution_tx_hash,
        )

        return updated_dispute
