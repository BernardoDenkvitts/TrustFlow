"""Blockchain event service."""

import logging
from datetime import UTC, datetime
from typing import Any

from src.modules.agreements.core.enums import AgreementStatus
from src.modules.agreements.persistence import AgreementRepository
from src.modules.blockchain.core.enums.onchain_event_name import OnchainEventName
from src.modules.blockchain.core.models.onchain_event import OnchainEvent
from src.modules.blockchain.persistence.onchain_event_repository import (
    OnchainEventRepository,
)
from src.modules.disputes.core.enums import DisputeResolution
from src.modules.disputes.persistence.dispute_repository import DisputeRepository
from src.modules.users.persistence.user_repository import UserRepository

logger = logging.getLogger(__name__)


class BlockchainEventService:
    """Service to process on-chain events and update off-chain state."""

    def __init__(
        self,
        event_repository: OnchainEventRepository,
        agreement_repository: AgreementRepository,
        dispute_repository: DisputeRepository,
        user_repository: UserRepository,
    ) -> None:
        self._event_repo = event_repository
        self._agreement_repo = agreement_repository
        self._dispute_repo = dispute_repository
        self._user_repo = user_repository

    async def process_event(self, event_data: dict[str, Any]) -> None:
        """
        Process a single event log.

        Args:
            event_data: Dictionary containing event details (name, args, etc).
        """
        # Prepare OnchainEvent record
        agreement_id_hex = event_data["args"]["agreementId"]
        if not agreement_id_hex.startswith("0x"):
            agreement_id_hex = "0x" + agreement_id_hex
        
        event = OnchainEvent(
            chain_id=event_data["chain_id"],
            contract_address=event_data["address"],
            tx_hash=event_data["transactionHash"],  # Already hex string from worker
            log_index=event_data["logIndex"],
            event_name=event_data["event"],
            agreement_id=agreement_id_hex,
            block_number=event_data["blockNumber"],
            block_hash=event_data["blockHash"],  # Already hex string from worker
            payload=event_data,
            processed_at=datetime.now(UTC).replace(tzinfo=None),
        )

        is_new = await self._event_repo.create_if_not_exists(event)
        
        if not is_new:
            logger.info(
                f"Event already processed: {event.tx_hash} index {event.log_index}"
            )
            return

        # Process business logic
        # If this fails, the exception will propagate up.
        # The `event` inserted above is FLUSHED but NOT COMMITTED.
        # The caller (worker) manages the main transaction.
        # If caller catches exception and continues, it MUST rollback the session
        # or at least not commit this event. 
        # Ideally, we should wrap THIS logic in a nested transaction too if we want
        # to isolate failures, but for now we rely on the worker loop design:
        # "If processing fails, we don't advance cursor".
        
        logger.info(f"Processing event: {event.event_name} for agreement {event.agreement_id}")
        
        if event.event_name == OnchainEventName.AGREEMENT_CREATED:
            await self._handle_agreement_created(event)
        elif event.event_name == OnchainEventName.PAYMENT_FUNDED:
            await self._handle_payment_funded(event)
        elif event.event_name == OnchainEventName.DISPUTE_OPENED:
            await self._handle_dispute_opened(event)
        elif event.event_name == OnchainEventName.PAYMENT_RELEASED:
            await self._handle_payment_released(event)
        elif event.event_name == OnchainEventName.PAYMENT_REFUNDED:
            await self._handle_payment_refunded(event)
        else:
            logger.warning(f"Unknown event type: {event.event_name}")

    async def _handle_agreement_created(self, event: OnchainEvent) -> None:
        """Handle AgreementCreated event."""
        agreement = await self._agreement_repo.find_by_id(event.agreement_id)
        if not agreement:
            logger.error(f"Agreement {event.agreement_id} not found for CREATED event")
            return

        if agreement.status == AgreementStatus.DRAFT:
            agreement.created_tx_hash = event.tx_hash
            agreement.created_onchain_at = event.processed_at  # Approximate
            await self._agreement_repo.update_status(agreement, AgreementStatus.CREATED)

    async def _handle_payment_funded(self, event: OnchainEvent) -> None:
        """Handle PaymentFunded event."""
        agreement = await self._agreement_repo.find_by_id(event.agreement_id)
        if not agreement:
            return

        # Idempotency: only update if not already funded or further
        if agreement.status == AgreementStatus.CREATED:
            agreement.funded_tx_hash = event.tx_hash
            agreement.funded_at = event.processed_at
            await self._agreement_repo.update_status(agreement, AgreementStatus.FUNDED)

    async def _handle_dispute_opened(self, event: OnchainEvent) -> None:
        """Handle DisputeOpened event."""
        agreement = await self._agreement_repo.find_by_id(event.agreement_id)
        if not agreement:
            return

        # Update Agreement Status
        if agreement.status != AgreementStatus.DISPUTED:
            await self._agreement_repo.update_status(
                agreement, AgreementStatus.DISPUTED
            )

        # Create Dispute Record
        opener_address = event.payload["args"]["openedBy"] # Arguments are named in ABI
        # Using "openedBy" as per ABI provided in plan/JSON.
        
        opener = await self._user_repo.find_by_wallet_address(opener_address)
        
        if not opener:
            # Should not happen as per domain rules (only Payer/Payee can dispute)
            logger.warning(
                f"Dispute opened by {opener_address} but user not found. "
                f"Agreement {agreement.agreement_id} status updated to DISPUTED."
            )
            return

        existing_dispute = await self._dispute_repo.find_by_agreement_id(
            agreement.agreement_id
        )
        if not existing_dispute:
            await self._dispute_repo.create(
                agreement_id=agreement.agreement_id,
                opened_by=opener.id
            )

    async def _handle_payment_released(self, event: OnchainEvent) -> None:
        """Handle PaymentReleased event."""
        agreement = await self._agreement_repo.find_by_id(event.agreement_id)
        if not agreement:
            return

        agreement.released_tx_hash = event.tx_hash
        agreement.released_at = event.processed_at
        await self._agreement_repo.update_status(agreement, AgreementStatus.RELEASED)

        # If there was a dispute, resolve it
        dispute = await self._dispute_repo.find_by_agreement_id(agreement.agreement_id)
        if dispute and not dispute.resolution:
            await self._dispute_repo.resolve(
                dispute=dispute,
                resolution=DisputeResolution.RELEASE,
                justification="Resolved on-chain via release",
                resolution_tx_hash=event.tx_hash
            )

    async def _handle_payment_refunded(self, event: OnchainEvent) -> None:
        """Handle PaymentRefunded event."""
        agreement = await self._agreement_repo.find_by_id(event.agreement_id)
        if not agreement:
            return

        agreement.refunded_tx_hash = event.tx_hash
        agreement.refunded_at = event.processed_at
        await self._agreement_repo.update_status(agreement, AgreementStatus.REFUNDED)

        # If there was a dispute, resolve it
        dispute = await self._dispute_repo.find_by_agreement_id(agreement.agreement_id)
        if dispute and not dispute.resolution:
            await self._dispute_repo.resolve(
                dispute=dispute,
                resolution=DisputeResolution.REFUND,
                justification="Resolved on-chain via refund",
                resolution_tx_hash=event.tx_hash
            )
