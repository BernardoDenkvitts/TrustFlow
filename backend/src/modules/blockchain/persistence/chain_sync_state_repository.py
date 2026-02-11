"""ChainSyncState repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.blockchain.core.models.chain_sync_state import ChainSyncState


class ChainSyncStateRepository:
    """Repository for managing blockchain synchronization state."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_state(self, chain_id: int, contract_address: str) -> ChainSyncState | None:
        """Fetches the current sync state for a given contract."""
        stmt = (
            select(ChainSyncState)
            .where(ChainSyncState.chain_id == chain_id)
            .where(ChainSyncState.contract_address == contract_address)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def initialize_state_if_needed(
        self, chain_id: int, contract_address: str, start_block: int = 0
    ) -> ChainSyncState:
        """
        Creates an initial sync state if one doesn't exist.
        Returns existing state if found.
        """
        existing = await self.get_state(chain_id, contract_address)
        if existing:
            return existing

        state = ChainSyncState(
            chain_id=chain_id,
            contract_address=contract_address,
            last_processed_block=start_block,
            last_finalized_block=start_block,
        )
        self._session.add(state)
        await self._session.flush()
        return state

    async def update_state(self, state: ChainSyncState) -> ChainSyncState:
        """Persists updates to the sync state."""
        self._session.add(state)
        await self._session.flush()
        return state
