"""OnchainEvent repository."""

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.blockchain.core.models.onchain_event import OnchainEvent


class OnchainEventRepository:
    """Repository for accessing on-chain event data."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_if_not_exists(self, event: OnchainEvent) -> bool:
        """
        Tries to insert an event using PostgreSQL's ON CONFLICT.
        Returns True if created, False if duplicate.

        Idempotency is guaranteed by the unique constraint on (chain_id, tx_hash, log_index).
        Uses native PostgreSQL ON CONFLICT for better performance than
        savepoint-based approach.
        """
        stmt = (
            insert(OnchainEvent)
            .values(
                chain_id=event.chain_id,
                contract_address=event.contract_address,
                tx_hash=event.tx_hash,
                log_index=event.log_index,
                event_name=event.event_name,
                agreement_id=event.agreement_id,
                block_number=event.block_number,
                block_hash=event.block_hash,
                payload=event.payload,
                processed_at=event.processed_at,
            )
            .on_conflict_do_nothing(constraint="uq_onchain_events_idempotent")
            .returning(OnchainEvent.id)
        )

        result = await self._session.scalar(stmt)
        return result is not None

    async def get_latest_processed_block(self, chain_id: int, contract_address: str) -> int:
        """Returns the highest block number processed for a given contract."""
        stmt = (
            select(func.max(OnchainEvent.block_number))
            .where(OnchainEvent.chain_id == chain_id)
            .where(OnchainEvent.contract_address == contract_address)
        )
        result = await self._session.execute(stmt)
        max_block = result.scalar_one_or_none()
        return max_block or 0
