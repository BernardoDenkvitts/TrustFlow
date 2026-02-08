import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from src.modules.agreements.core.enums import AgreementStatus, ArbitrationPolicy
from src.modules.agreements.core.models import Agreement
from src.modules.agreements.persistence import AgreementRepository
from src.modules.disputes.core.enums import DisputeResolution, DisputeStatus
from src.modules.disputes.core.exceptions import (
    DisputeNotFoundError, 
    UnauthorizedArbitratorError, 
    DisputeAlreadyResolvedError
)
from src.modules.disputes.core.models import Dispute
from src.modules.disputes.core.services import DisputeService
from src.modules.disputes.persistence import DisputeRepository
from src.modules.users.persistence import UserRepository


@pytest.fixture
def mock_dispute_repo():
    return AsyncMock(spec=DisputeRepository)


@pytest.fixture
def mock_agreement_repo():
    return AsyncMock(spec=AgreementRepository)


@pytest.fixture
def mock_user_repo():
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def dispute_service(mock_dispute_repo, mock_agreement_repo):
    return DisputeService(mock_dispute_repo, mock_agreement_repo)


@pytest.mark.asyncio
async def test_resolve_dispute_success_release(
    dispute_service, mock_dispute_repo, mock_agreement_repo
):
    """Test resolving a dispute successfully."""
    # Setup
    agreement_id = Decimal("123")
    arbitrator_id = uuid.uuid4()
    payer_id = uuid.uuid4()
    payee_id = uuid.uuid4()
    dispute_id = uuid.uuid4()

    # Mock Agreement
    agreement = Agreement(
        agreement_id=agreement_id,
        payer_id=payer_id,
        payee_id=payee_id,
        arbitrator_id=arbitrator_id,
        arbitration_policy=ArbitrationPolicy.WITH_ARBITRATOR,
        status=AgreementStatus.DISPUTED,
        amount_wei=Decimal("1000"),
    )

    # Mock Dispute
    dispute = Dispute(
        id=dispute_id,
        agreement_id=agreement_id,
        opened_by=payer_id,
        status=DisputeStatus.OPEN,
        opened_at=None,
    )

    # Configure mocks
    mock_agreement_repo.find_by_id.return_value = agreement
    mock_dispute_repo.find_by_agreement_id.return_value = dispute
    mock_dispute_repo.resolve.return_value = dispute

    # Action
    resolution_tx_hash = "0x" + "a" * 64
    result = await dispute_service.resolve_dispute(
        agreement_id=agreement_id,
        user_id=arbitrator_id,
        resolution=DisputeResolution.RELEASE,
        justification="Valid justification",
        resolution_tx_hash=resolution_tx_hash,
    )

    # Assert
    mock_dispute_repo.resolve.assert_called_once_with(
        dispute=dispute,
        resolution=DisputeResolution.RELEASE,
        justification="Valid justification",
        resolution_tx_hash=resolution_tx_hash,
    )
    assert result == dispute


@pytest.mark.asyncio
async def test_resolve_dispute_unauthorized(
    dispute_service, mock_dispute_repo, mock_agreement_repo
):
    """Test that non-arbitrator cannot resolve dispute."""
    # Setup
    agreement_id = Decimal("123")
    arbitrator_id = uuid.uuid4()
    other_user_id = uuid.uuid4()

    agreement = Agreement(
        agreement_id=agreement_id,
        arbitrator_id=arbitrator_id,
        status=AgreementStatus.DISPUTED,
    )
    
    mock_agreement_repo.find_by_id.return_value = agreement

    # Action & Assert
    with pytest.raises(UnauthorizedArbitratorError):
        await dispute_service.resolve_dispute(
            agreement_id=agreement_id,
            user_id=other_user_id,
            resolution=DisputeResolution.REFUND,
            justification="I am not the arbitrator",
            resolution_tx_hash="0x...",
        )


@pytest.mark.asyncio
async def test_resolve_dispute_already_resolved(
    dispute_service, mock_dispute_repo, mock_agreement_repo
):
    """Test resolving a dispute that is already resolved."""
    # Setup
    agreement_id = Decimal("123")
    arbitrator_id = uuid.uuid4()
    dispute_id = uuid.uuid4()

    agreement = Agreement(
        agreement_id=agreement_id,
        arbitrator_id=arbitrator_id,
        status=AgreementStatus.DISPUTED,
    )
    
    dispute = Dispute(
        id=dispute_id,
        agreement_id=agreement_id,
        status=DisputeStatus.RESOLVED, # Already resolved
    )

    mock_agreement_repo.find_by_id.return_value = agreement
    mock_dispute_repo.find_by_agreement_id.return_value = dispute

    # Action & Assert
    with pytest.raises(DisputeAlreadyResolvedError):
        await dispute_service.resolve_dispute(
            agreement_id=agreement_id,
            user_id=arbitrator_id,
            resolution=DisputeResolution.REFUND,
            justification="Trying to resolve again",
            resolution_tx_hash="0x...",
        )
