"""Unit tests for AgreementService."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.agreements.core.enums import AgreementStatus, ArbitrationPolicy
from src.modules.agreements.core.exceptions import (
    AgreementNotFoundError,
    InvalidArbitrationPolicyError,
    InvalidStateTransitionError,
    SelfDealError,
    UnauthorizedAgreementAccessError,
)
from src.modules.agreements.core.models import Agreement
from src.modules.agreements.core.services import AgreementService


@pytest.fixture
def mock_agreement_repo() -> MagicMock:
    """Create a mock AgreementRepository."""
    return MagicMock()


@pytest.fixture
def mock_user_repo() -> MagicMock:
    """Create a mock UserRepository."""
    return MagicMock()


@pytest.fixture
def agreement_service(
    mock_agreement_repo: MagicMock, mock_user_repo: MagicMock
) -> AgreementService:
    """Create an AgreementService with mocked repositories."""
    return AgreementService(mock_agreement_repo, mock_user_repo)


@pytest.fixture
def sample_agreement() -> Agreement:
    """Create a sample agreement for testing."""
    agreement = MagicMock(spec=Agreement)
    agreement.agreement_id = Decimal("123456789")
    agreement.payer_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    agreement.payee_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    agreement.arbitrator_id = None
    agreement.arbitration_policy = ArbitrationPolicy.NONE
    agreement.amount_wei = Decimal("1000000000000000000")
    agreement.status = AgreementStatus.DRAFT
    agreement.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    agreement.updated_at = datetime(2026, 1, 1, tzinfo=UTC)
    return agreement


@pytest.fixture
def sample_user() -> MagicMock:
    """Create a sample user for testing."""
    user = MagicMock()
    user.id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    return user


class TestCreateAgreement:
    """Tests for AgreementService.create_agreement method."""

    @pytest.mark.asyncio
    async def test_create_agreement_success(
        self,
        agreement_service: AgreementService,
        mock_agreement_repo: MagicMock,
        mock_user_repo: MagicMock,
        sample_agreement: Agreement,
        sample_user: MagicMock,
    ) -> None:
        """Should create agreement successfully."""
        payer_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        payee_id = uuid.UUID("00000000-0000-0000-0000-000000000002")

        mock_user_repo.find_by_id = AsyncMock(return_value=sample_user)
        mock_agreement_repo.create = AsyncMock(return_value=sample_agreement)

        with patch.object(
            agreement_service,
            "_generate_agreement_id",
            return_value=Decimal("123456789"),
        ):
            result = await agreement_service.create_agreement(
                payer_id=payer_id,
                payee_id=payee_id,
                amount_wei=Decimal("1000000000000000000"),
                arbitration_policy=ArbitrationPolicy.NONE,
            )

        assert result == sample_agreement
        mock_agreement_repo.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_agreement_self_deal(
        self,
        agreement_service: AgreementService,
    ) -> None:
        """Should raise SelfDealError when payer == payee."""
        user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

        with pytest.raises(SelfDealError) as exc_info:
            await agreement_service.create_agreement(
                payer_id=user_id,
                payee_id=user_id,
                amount_wei=Decimal("1000000000000000000"),
                arbitration_policy=ArbitrationPolicy.NONE,
            )

        assert str(user_id) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_agreement_policy_none_with_arbitrator(
        self,
        agreement_service: AgreementService,
    ) -> None:
        """Should fail when policy is NONE but arbitrator is provided."""
        payer_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        payee_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
        arbitrator_id = uuid.UUID("00000000-0000-0000-0000-000000000003")

        with pytest.raises(InvalidArbitrationPolicyError) as exc_info:
            await agreement_service.create_agreement(
                payer_id=payer_id,
                payee_id=payee_id,
                amount_wei=Decimal("1000000000000000000"),
                arbitration_policy=ArbitrationPolicy.NONE,
                arbitrator_id=arbitrator_id,
            )

        assert exc_info.value.policy == ArbitrationPolicy.NONE
        assert exc_info.value.has_arbitrator is True

    @pytest.mark.asyncio
    async def test_create_agreement_policy_arbitrator_without_arbitrator(
        self,
        agreement_service: AgreementService,
    ) -> None:
        """Should fail when policy is WITH_ARBITRATOR but no arbitrator provided."""
        payer_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        payee_id = uuid.UUID("00000000-0000-0000-0000-000000000002")

        with pytest.raises(InvalidArbitrationPolicyError) as exc_info:
            await agreement_service.create_agreement(
                payer_id=payer_id,
                payee_id=payee_id,
                amount_wei=Decimal("1000000000000000000"),
                arbitration_policy=ArbitrationPolicy.WITH_ARBITRATOR,
                arbitrator_id=None,
            )

        assert exc_info.value.policy == ArbitrationPolicy.WITH_ARBITRATOR
        assert exc_info.value.has_arbitrator is False


class TestGetAgreementById:
    """Tests for AgreementService.get_agreement_by_id method."""

    @pytest.mark.asyncio
    async def test_get_agreement_success(
        self,
        agreement_service: AgreementService,
        mock_agreement_repo: MagicMock,
        sample_agreement: Agreement,
    ) -> None:
        """Should return agreement when user is participant."""
        mock_agreement_repo.find_by_id = AsyncMock(return_value=sample_agreement)

        result = await agreement_service.get_agreement_by_id(
            agreement_id=sample_agreement.agreement_id,
            user_id=sample_agreement.payer_id,
        )

        assert result == sample_agreement

    @pytest.mark.asyncio
    async def test_get_agreement_not_found(
        self,
        agreement_service: AgreementService,
        mock_agreement_repo: MagicMock,
    ) -> None:
        """Should raise AgreementNotFoundError when agreement doesn't exist."""
        mock_agreement_repo.find_by_id = AsyncMock(return_value=None)
        agreement_id = Decimal("999999")

        with pytest.raises(AgreementNotFoundError) as exc_info:
            await agreement_service.get_agreement_by_id(
                agreement_id=agreement_id,
                user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            )

        assert exc_info.value.agreement_id == agreement_id

    @pytest.mark.asyncio
    async def test_get_agreement_unauthorized(
        self,
        agreement_service: AgreementService,
        mock_agreement_repo: MagicMock,
        sample_agreement: Agreement,
    ) -> None:
        """Should raise UnauthorizedAgreementAccessError for non-participants."""
        mock_agreement_repo.find_by_id = AsyncMock(return_value=sample_agreement)
        non_participant_id = uuid.UUID("00000000-0000-0000-0000-000000000999")

        with pytest.raises(UnauthorizedAgreementAccessError) as exc_info:
            await agreement_service.get_agreement_by_id(
                agreement_id=sample_agreement.agreement_id,
                user_id=non_participant_id,
            )

        assert str(non_participant_id) in str(exc_info.value.user_id)


class TestSubmitAgreement:
    """Tests for AgreementService.submit_agreement method."""

    @pytest.mark.asyncio
    async def test_submit_agreement_success(
        self,
        agreement_service: AgreementService,
        mock_agreement_repo: MagicMock,
        sample_agreement: Agreement,
    ) -> None:
        """Should transition DRAFT -> PENDING_FUNDING when payer submits."""
        sample_agreement.status = AgreementStatus.DRAFT
        updated_agreement = MagicMock(spec=Agreement)
        updated_agreement.status = AgreementStatus.PENDING_FUNDING

        mock_agreement_repo.find_by_id = AsyncMock(return_value=sample_agreement)
        mock_agreement_repo.update_status = AsyncMock(return_value=updated_agreement)

        result = await agreement_service.submit_agreement(
            agreement_id=sample_agreement.agreement_id,
            user_id=sample_agreement.payer_id,
        )

        assert result.status == AgreementStatus.PENDING_FUNDING
        mock_agreement_repo.update_status.assert_awaited_once_with(
            sample_agreement, AgreementStatus.PENDING_FUNDING
        )

    @pytest.mark.asyncio
    async def test_submit_agreement_wrong_status(
        self,
        agreement_service: AgreementService,
        mock_agreement_repo: MagicMock,
        sample_agreement: Agreement,
    ) -> None:
        """Should fail when agreement is not in DRAFT status."""
        sample_agreement.status = AgreementStatus.PENDING_FUNDING
        mock_agreement_repo.find_by_id = AsyncMock(return_value=sample_agreement)

        with pytest.raises(InvalidStateTransitionError) as exc_info:
            await agreement_service.submit_agreement(
                agreement_id=sample_agreement.agreement_id,
                user_id=sample_agreement.payer_id,
            )

        assert exc_info.value.current_status == AgreementStatus.PENDING_FUNDING
        assert exc_info.value.target_status == AgreementStatus.PENDING_FUNDING

    @pytest.mark.asyncio
    async def test_submit_agreement_not_payer(
        self,
        agreement_service: AgreementService,
        mock_agreement_repo: MagicMock,
        sample_agreement: Agreement,
    ) -> None:
        """Should fail when non-payer tries to submit."""
        sample_agreement.status = AgreementStatus.DRAFT
        mock_agreement_repo.find_by_id = AsyncMock(return_value=sample_agreement)

        with pytest.raises(InvalidStateTransitionError) as exc_info:
            await agreement_service.submit_agreement(
                agreement_id=sample_agreement.agreement_id,
                user_id=sample_agreement.payee_id,  # payee, not payer
            )

        assert "Only the payer can submit" in str(exc_info.value.reason)
