import uuid
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.modules.agreements.core.enums import AgreementStatus, ArbitrationPolicy
from src.modules.agreements.core.models import Agreement
from src.modules.agreements.persistence import AgreementRepository
from src.modules.disputes.core.enums import DisputeResolution, DisputeStatus
from src.modules.disputes.core.exceptions import (
    DisputeAlreadyResolvedError,
    DisputeNotYetResolvedError,
    UnauthorizedArbitratorError,
)
from src.modules.disputes.core.models import Dispute
from src.modules.disputes.core.services import DisputeService
from src.modules.disputes.persistence import DisputeRepository


@pytest.fixture
def mock_dispute_repo():
    return AsyncMock(spec=DisputeRepository)


@pytest.fixture
def mock_agreement_repo():
    return AsyncMock(spec=AgreementRepository)


@pytest.fixture
def dispute_service(mock_dispute_repo, mock_agreement_repo):
    return DisputeService(mock_dispute_repo, mock_agreement_repo)


def _make_agreement(agreement_id: str, arbitrator_id: uuid.UUID) -> Agreement:
    """Helper to build a minimal Agreement for testing."""
    return Agreement(
        agreement_id=agreement_id,
        payer_id=uuid.uuid4(),
        payee_id=uuid.uuid4(),
        arbitrator_id=arbitrator_id,
        arbitration_policy=ArbitrationPolicy.WITH_ARBITRATOR,
        status=AgreementStatus.DISPUTED,
        amount_wei=Decimal("1000"),
    )


def _make_dispute(
    agreement_id: str,
    resolution: DisputeResolution | None = DisputeResolution.RELEASE,
    justification: str | None = None,
) -> Dispute:
    """Helper to build a Dispute for testing."""
    return Dispute(
        id=uuid.uuid4(),
        agreement_id=agreement_id,
        opened_by=uuid.uuid4(),
        status=DisputeStatus.RESOLVED if resolution else DisputeStatus.OPEN,
        resolution=resolution,
        justification=justification,
        opened_at=None,
    )


@pytest.mark.asyncio
async def test_submit_justification_success(
    dispute_service, mock_dispute_repo, mock_agreement_repo
):
    """Arbitrator submits justification after worker has resolved the dispute on-chain."""
    agreement_id = "0x" + "a1" * 32
    arbitrator_id = uuid.uuid4()

    agreement = _make_agreement(agreement_id, arbitrator_id)
    dispute = _make_dispute(agreement_id, resolution=DisputeResolution.RELEASE)

    mock_agreement_repo.find_by_id.return_value = agreement
    mock_dispute_repo.find_by_agreement_id.return_value = dispute
    mock_dispute_repo.set_justification.return_value = dispute

    result = await dispute_service.submit_justification(
        agreement_id=agreement_id,
        user_id=arbitrator_id,
        justification="The payee delivered the service as agreed.",
    )

    mock_dispute_repo.set_justification.assert_called_once_with(
        dispute=dispute,
        justification="The payee delivered the service as agreed.",
    )
    assert result == dispute


@pytest.mark.asyncio
async def test_submit_justification_not_yet_resolved(
    dispute_service, mock_dispute_repo, mock_agreement_repo
):
    """Arbitrator cannot submit justification if the worker has not resolved the dispute yet."""
    agreement_id = "0x" + "a1" * 32
    arbitrator_id = uuid.uuid4()

    agreement = _make_agreement(agreement_id, arbitrator_id)
    # resolution is None — worker has not processed the on-chain event yet
    dispute = _make_dispute(agreement_id, resolution=None)

    mock_agreement_repo.find_by_id.return_value = agreement
    mock_dispute_repo.find_by_agreement_id.return_value = dispute

    with pytest.raises(DisputeNotYetResolvedError):
        await dispute_service.submit_justification(
            agreement_id=agreement_id,
            user_id=arbitrator_id,
            justification="The payee delivered the service as agreed.",
        )


@pytest.mark.asyncio
async def test_submit_justification_already_submitted(
    dispute_service, mock_dispute_repo, mock_agreement_repo
):
    """Arbitrator cannot submit justification twice."""
    agreement_id = "0x" + "a1" * 32
    arbitrator_id = uuid.uuid4()

    agreement = _make_agreement(agreement_id, arbitrator_id)
    # justification already set
    dispute = _make_dispute(
        agreement_id,
        resolution=DisputeResolution.RELEASE,
        justification="Already submitted.",
    )

    mock_agreement_repo.find_by_id.return_value = agreement
    mock_dispute_repo.find_by_agreement_id.return_value = dispute

    with pytest.raises(DisputeAlreadyResolvedError):
        await dispute_service.submit_justification(
            agreement_id=agreement_id,
            user_id=arbitrator_id,
            justification="Trying to overwrite.",
        )


@pytest.mark.asyncio
async def test_submit_justification_unauthorized(
    dispute_service, mock_dispute_repo, mock_agreement_repo
):
    """Non-arbitrator cannot submit justification."""
    agreement_id = "0x" + "a1" * 32
    arbitrator_id = uuid.uuid4()
    other_user_id = uuid.uuid4()

    agreement = _make_agreement(agreement_id, arbitrator_id)

    mock_agreement_repo.find_by_id.return_value = agreement

    with pytest.raises(UnauthorizedArbitratorError):
        await dispute_service.submit_justification(
            agreement_id=agreement_id,
            user_id=other_user_id,
            justification="I am not the arbitrator.",
        )
