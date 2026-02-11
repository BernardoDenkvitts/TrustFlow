"""Tests for BlockchainEventService."""

from unittest.mock import AsyncMock, Mock

import pytest

from src.modules.agreements.core.enums import AgreementStatus
from src.modules.blockchain.core.services.blockchain_event_service import (
    BlockchainEventService,
)


@pytest.fixture
def mock_event_repo():
    return AsyncMock()


@pytest.fixture
def mock_agreement_repo():
    return AsyncMock()


@pytest.fixture
def mock_dispute_repo():
    return AsyncMock()


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_event_repo, mock_agreement_repo, mock_dispute_repo, mock_user_repo):
    return BlockchainEventService(
        event_repository=mock_event_repo,
        agreement_repository=mock_agreement_repo,
        dispute_repository=mock_dispute_repo,
        user_repository=mock_user_repo,
    )


@pytest.mark.asyncio
async def test_process_agreement_created(service, mock_event_repo, mock_agreement_repo):
    # Setup
    agreement_id_hex = "0x" + "ab" * 32
    event_data = {
        "chain_id": 31337,
        "address": "0x123",
        "transactionHash": b"txhash",
        "logIndex": 0,
        "blockNumber": 100,
        "blockHash": b"blockhash",
        "event": "AgreementCreated",
        "args": {"agreementId": agreement_id_hex},
    }
    
    # Mock create_if_not_exists to return True (new event)
    mock_event_repo.create_if_not_exists.return_value = True
    
    # Mock agreement finding
    agreement = Mock()
    agreement.status = AgreementStatus.DRAFT
    mock_agreement_repo.find_by_id.return_value = agreement

    # Act
    await service.process_event(event_data)

    # Assert
    mock_event_repo.create_if_not_exists.assert_called_once()
    mock_agreement_repo.find_by_id.assert_awaited_with(agreement_id_hex)
    mock_agreement_repo.update_status.assert_awaited_with(
        agreement, AgreementStatus.CREATED
    )
    assert agreement.created_tx_hash == b"txhash"


@pytest.mark.asyncio
async def test_process_duplicate_event(service, mock_event_repo, mock_agreement_repo):
    # Setup
    agreement_id_hex = "0x" + "ab" * 32
    event_data = {
        "chain_id": 31337,
        "address": "0x123",
        "transactionHash": b"txhash",
        "logIndex": 0,
        "blockNumber": 100,
        "blockHash": b"blockhash",
        "event": "AgreementCreated",
        "args": {"agreementId": agreement_id_hex},
    }
    
    # Mock create_if_not_exists to return False (duplicate)
    mock_event_repo.create_if_not_exists.return_value = False

    # Act
    await service.process_event(event_data)

    # Assert
    mock_event_repo.create_if_not_exists.assert_called_once()
    mock_agreement_repo.find_by_id.assert_not_called()


@pytest.mark.asyncio
async def test_process_payment_funded(service, mock_event_repo, mock_agreement_repo):
    # Setup
    agreement_id_hex = "0x" + "ab" * 32
    event_data = {
        "chain_id": 31337,
        "address": "0x123",
        "transactionHash": b"txhash",
        "logIndex": 0,
        "blockNumber": 100,
        "blockHash": b"blockhash",
        "event": "PaymentFunded",
        "args": {"agreementId": agreement_id_hex},
    }
    
    mock_event_repo.create_if_not_exists.return_value = True
    
    agreement = Mock()
    agreement.status = AgreementStatus.CREATED
    mock_agreement_repo.find_by_id.return_value = agreement

    # Act
    await service.process_event(event_data)

    # Assert
    mock_agreement_repo.update_status.assert_awaited_with(
        agreement, AgreementStatus.FUNDED
    )
