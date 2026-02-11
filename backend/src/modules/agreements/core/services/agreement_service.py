"""Agreement service implementing business logic."""

import secrets
import uuid

from src.modules.agreements.core.enums import AgreementStatus, ArbitrationPolicy
from src.modules.agreements.core.exceptions import (
    AgreementNotFoundError,
    InvalidArbitrationPolicyError,
    InvalidStateTransitionError,
    SelfDealError,
    UnauthorizedAgreementAccessError,
)
from src.modules.agreements.core.models import Agreement
from src.modules.agreements.persistence import AgreementRepository
from src.modules.users.core.exceptions import UserNotFoundError
from src.modules.users.persistence import UserRepository


class AgreementService:
    """Service class for agreement-related business logic."""

    def __init__(
        self,
        agreement_repository: AgreementRepository,
        user_repository: UserRepository,
    ) -> None:
        """Initialize the service with repositories.

        Args:
            agreement_repository: The agreement repository for data access.
            user_repository: The user repository for validating user existence.
        """
        self._agreement_repo = agreement_repository
        self._user_repo = user_repository

    def _generate_agreement_id(self) -> str:
        """Generate a unique agreement ID as a hex string.

        Returns:
            A random 256-bit identifier as '0x' + 64 hex chars.
        """
        return "0x" + secrets.token_bytes(32).hex()

    def _is_participant(self, agreement: Agreement, user_id: uuid.UUID) -> bool:
        """Check if a user is a participant in an agreement.

        A participant is the payer, payee, or arbitrator.

        Args:
            agreement: The agreement to check.
            user_id: The user ID to check.

        Returns:
            True if the user is a participant, False otherwise.
        """
        return user_id in (
            agreement.payer_id,
            agreement.payee_id,
            agreement.arbitrator_id,
        )

    async def _validate_user_exists(self, user_id: uuid.UUID) -> None:
        """Validate that a user exists.

        Args:
            user_id: The user ID to validate.

        Raises:
            UserNotFoundError: If the user does not exist.
        """
        user = await self._user_repo.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))

    async def create_agreement(
        self,
        payer_id: uuid.UUID,
        payee_id: uuid.UUID,
        amount_wei: Decimal,
        arbitration_policy: ArbitrationPolicy,
        arbitrator_id: uuid.UUID | None = None,
    ) -> Agreement:
        """Create a new agreement in DRAFT status.

        Args:
            payer_id: UUID of the payer.
            payee_id: UUID of the payee.
            amount_wei: Amount in wei.
            arbitration_policy: The arbitration policy.
            arbitrator_id: UUID of the arbitrator (if applicable).

        Returns:
            The created Agreement entity.

        Raises:
            SelfDealError: If payer and payee are the same.
            InvalidArbitrationPolicyError: If policy constraints are violated.
            UserNotFoundError: If any referenced user doesn't exist.
        """
        # Validate payer != payee
        if payer_id == payee_id:
            raise SelfDealError(str(payer_id))

        # Validate arbitration policy constraints
        if arbitration_policy == ArbitrationPolicy.NONE and arbitrator_id is not None:
            raise InvalidArbitrationPolicyError(
                policy=arbitration_policy,
                has_arbitrator=True,
            )
        if (
            arbitration_policy == ArbitrationPolicy.WITH_ARBITRATOR
            and arbitrator_id is None
        ):
            raise InvalidArbitrationPolicyError(
                policy=arbitration_policy,
                has_arbitrator=False,
            )

        # Validate all users exist
        await self._validate_user_exists(payer_id)
        await self._validate_user_exists(payee_id)
        if arbitrator_id is not None:
            await self._validate_user_exists(arbitrator_id)

        # Generate unique agreement ID
        agreement_id = self._generate_agreement_id()

        # Create agreement
        agreement = await self._agreement_repo.create(
            agreement_id=agreement_id,
            payer_id=payer_id,
            payee_id=payee_id,
            amount_wei=amount_wei,
            arbitration_policy=arbitration_policy,
            arbitrator_id=arbitrator_id,
        )

        return agreement

    async def get_agreement_by_id(
        self,
        agreement_id: str,
        user_id: uuid.UUID,
    ) -> Agreement:
        """Get an agreement by ID with authorization check.

        Args:
            agreement_id: The agreement identifier.
            user_id: The user requesting the agreement.

        Returns:
            The Agreement entity.

        Raises:
            AgreementNotFoundError: If the agreement is not found.
            UnauthorizedAgreementAccessError: If user is not a participant.
        """
        agreement = await self._agreement_repo.find_by_id(agreement_id)
        if agreement is None:
            raise AgreementNotFoundError(agreement_id)

        if not self._is_participant(agreement, user_id):
            raise UnauthorizedAgreementAccessError(str(user_id), agreement_id)

        return agreement

    async def list_user_agreements(
        self,
        user_id: uuid.UUID,
        status_filter: AgreementStatus | None = None,
    ) -> list[Agreement]:
        """List all agreements where the user is a participant.

        Args:
            user_id: The user's UUID.
            status_filter: Optional status to filter by.

        Returns:
            List of Agreement entities.
        """
        return await self._agreement_repo.list_by_user(user_id, status_filter)

    async def submit_agreement(
        self,
        agreement_id: str,
        user_id: uuid.UUID,
    ) -> Agreement:
        """Locks agreement terms and awaits on-chain funding.

        Transitions the agreement from DRAFT to PENDING_FUNDING.
        Only the payer can submit an agreement.

        Args:
            agreement_id: The agreement identifier.
            user_id: The user submitting the agreement.

        Returns:
            The updated Agreement entity.

        Raises:
            AgreementNotFoundError: If the agreement is not found.
            UnauthorizedAgreementAccessError: If user is not a participant.
            InvalidStateTransitionError: If not in DRAFT status or user is not payer.
        """
        # Get agreement with authorization check
        agreement = await self.get_agreement_by_id(agreement_id, user_id)

        # Only payer can submit
        if agreement.payer_id != user_id:
            raise InvalidStateTransitionError(
                current_status=agreement.status,
                target_status=AgreementStatus.PENDING_FUNDING,
                reason="Only the payer can submit an agreement",
            )

        # Only from DRAFT status
        if agreement.status != AgreementStatus.DRAFT:
            raise InvalidStateTransitionError(
                current_status=agreement.status,
                target_status=AgreementStatus.PENDING_FUNDING,
                reason="Agreement can only be submitted from DRAFT status",
            )

        # Transition to PENDING_FUNDING
        updated_agreement = await self._agreement_repo.update_status(
            agreement, AgreementStatus.PENDING_FUNDING
        )

        return updated_agreement
