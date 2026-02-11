"""Blockchain synchronization worker."""

import asyncio
import logging
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from web3 import AsyncHTTPProvider, AsyncWeb3
from web3.middleware import ExtraDataToPOAMiddleware

from src.config import settings
from src.modules.agreements.persistence.agreement_repository import AgreementRepository
from src.modules.blockchain.core.abi import TRUSTFLOW_ESCROW_ABI
from src.modules.blockchain.core.services.blockchain_event_service import (
    BlockchainEventService,
)
from src.modules.blockchain.persistence.chain_sync_state_repository import (
    ChainSyncStateRepository,
)
from src.modules.blockchain.persistence.onchain_event_repository import (
    OnchainEventRepository,
)
from src.modules.disputes.persistence.dispute_repository import DisputeRepository
from src.modules.users.persistence.user_repository import UserRepository
from src.shared.database.session import async_session_factory

logger = logging.getLogger(__name__)


def _hexbytes_to_json(obj: Any) -> Any:
    """
    Recursively convert HexBytes and bytes objects to hex strings for JSON serialization.
    
    Args:
        obj: Object to convert (can be dict, list, HexBytes, bytes, or any other type)
        
    Returns:
        Object with all HexBytes and bytes converted to hex strings
    """
    from hexbytes import HexBytes
    
    if isinstance(obj, HexBytes):
        return obj.hex()
    elif isinstance(obj, bytes):
        # Regular bytes object - convert to hex string
        return obj.hex()
    elif isinstance(obj, dict):
        return {key: _hexbytes_to_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_hexbytes_to_json(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(_hexbytes_to_json(item) for item in obj)
    else:
        return obj


class ChainSyncWorker:
    """Worker to synchronize blockchain events with the database."""

    def __init__(self) -> None:
        self._w3 = AsyncWeb3(AsyncHTTPProvider(settings.rpc_url))
        self._w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        self._contract = self._w3.eth.contract(
            address=settings.escrow_contract_address, abi=TRUSTFLOW_ESCROW_ABI
        )
        self._running = False
        self._task: asyncio.Task | None = None
        
        # Cache topic hashes for faster lookup
        self._event_topics: dict[str, str] = {}
        for abi_item in TRUSTFLOW_ESCROW_ABI:
            if abi_item["type"] == "event":
                # Construct signature: Name(type1,type2,...)
                inputs = [param["type"] for param in abi_item["inputs"]]
                signature = f"{abi_item['name']}({','.join(inputs)})"
                # Calculate keccak hash of signature
                topic_hash = self._w3.keccak(text=signature).hex()
                self._event_topics[topic_hash] = abi_item["name"]

    async def start(self) -> None:
        """Start the worker in a background task."""
        if self._running:
            return
        
        if await self._w3.is_connected():
            logger.info(f"Connected to blockchain at {settings.rpc_url}")
        else:
            logger.error(f"Failed to connect to blockchain at {settings.rpc_url}")

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Blockchain sync worker started.")

    async def stop(self) -> None:
        """Stop the worker."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Blockchain sync worker stopped.")

    async def _run_loop(self) -> None:
        """
        Main polling loop with efficient catch-up mechanism.
        
        Uses a two-level loop structure:
        - Outer loop: Runs continuously while worker is active
        - Inner loop: Processes multiple batches per DB session for efficiency
        
        This design minimizes DB connection overhead during catch-up scenarios
        (e.g., when thousands of blocks are behind) by reusing the same session
        and repository instances across multiple batches.
        """
        while self._running:
            try:
                # Limit batches per session to prevent:
                # - Excessively long-lived DB sessions (memory leaks, lock escalation)
                # - Connection pool starvation (other app components need connections)
                # - Unbounded processing if chain produces blocks faster than we consume
                # With 1000 blocks/batch, this processes up to 20,000 blocks per session.
                MAX_BATCHES_PER_SESSION = 20
                batch_count = 0
                
                # Open a single DB session for processing multiple batches.
                # Session lifecycle: created once per outer loop iteration, reused for
                # up to MAX_BATCHES_PER_SESSION batches, then closed to free resources.
                async with async_session_factory() as session:
                    # Instantiate repositories and service ONCE per session.
                    sync_repo = ChainSyncStateRepository(session)
                    event_repo = OnchainEventRepository(session)
                    agreement_repo = AgreementRepository(session)
                    dispute_repo = DisputeRepository(session)
                    user_repo = UserRepository(session)
                    service = BlockchainEventService(
                        event_repository=event_repo,
                        agreement_repository=agreement_repo,
                        dispute_repository=dispute_repo,
                        user_repository=user_repo,
                    )
                    
                    # Inner loop: Process batches sequentially until one of:
                    # 1. Worker is stopped (_running = False)
                    # 2. Batch limit reached (prevents session from being too long)
                    # 3. Chain tip reached (no more blocks to process)
                    # 4. No blocks were processed (error or already synchronized)
                    while self._running and batch_count < MAX_BATCHES_PER_SESSION:
                        # Process one batch (up to 1000 blocks).
                        # Returns: (blocks_processed, reached_top)
                        blocks_processed, reached_top = await self._process_batch(
                            session, sync_repo, service
                        )
                        
                        if blocks_processed > 0:
                            batch_count += 1
                            logger.info(
                                f"Processed batch {batch_count}: {blocks_processed} blocks"
                            )
                            
                            # Commit after each batch to:
                            # - Persist progress (idempotency on restart)
                            # - Release DB locks (allow other workers/processes)
                            # - Clear SQLAlchemy session cache (prevent memory growth)
                            await session.commit()
                            session.expire_all()  # Detach all ORM objects from session
                        
                        # Yield control to the event loop, allowing other async tasks
                        # (e.g., API requests, health checks) to execute.
                        # Without this, we could starve other coroutines during catch-up.
                        await asyncio.sleep(0)
                        
                        # Exit conditions for inner loop:
                        # - reached_top: We've caught up to (current_block - confirmations)
                        # - blocks_processed == 0: No work done (error or already synced)
                        if reached_top or blocks_processed == 0:
                            logger.debug("Reached chain tip or no blocks to process")
                            break

            except Exception as e:
                logger.error(f"Error in sync loop: {e}", exc_info=True)
            
            # Sleep before next outer loop iteration.
            await asyncio.sleep(settings.sync_interval_seconds)

    async def _process_batch(
        self, 
        session: AsyncSession,
        sync_repo: ChainSyncStateRepository, 
        service: BlockchainEventService,
    ) -> tuple[int, bool]:
        """
        Process a batch of blocks.
        
        Returns:
            tuple[int, bool]: (blocks_processed, reached_top)
        """
        # Get Sync State
        state = await sync_repo.initialize_state_if_needed(
            chain_id=settings.chain_id,
            contract_address=settings.escrow_contract_address,
            start_block=0
        )
        
        # Determine Range
        try:
            current_block = await self._w3.eth.block_number
        except Exception as e:
            logger.error(f"Failed to get block number: {e}")
            return (0, False)

        confirmations = settings.confirmations
        to_block = current_block - confirmations
        
        if to_block < state.last_processed_block:
            return (0, True)  # Already synced, we're at the top

        MAX_BATCH = 1000
        from_block = state.last_processed_block + 1
        
        if to_block - from_block > MAX_BATCH:
            to_block = from_block + MAX_BATCH
        
        if from_block > to_block:
            return (0, True)  # No blocks to process

        logger.debug(f"Syncing blocks {from_block} to {to_block}")

        # Fetch Logs
        try:
            logs = await self._w3.eth.get_logs({
                "fromBlock": from_block,
                "toBlock": to_block,
                "address": settings.escrow_contract_address,
            })
        except Exception as e:
            logger.error(f"Failed to fetch logs: {e}")
            return (0, False)

        # Process Logs
        for log in logs:
            # Identify event from topic[0]
            if not log["topics"]:
                continue
                
            topic0 = log["topics"][0].hex()
            event_name = self._event_topics.get(topic0)
            
            if not event_name:
                # Unknown event
                continue

            try:
                # process_log returns EventData
                decoded_event = self._contract.events[event_name]().process_log(log)
            except Exception:
                logger.warning(f"Failed to decode known event {event_name}")
                continue
            
            # Convert to dict
            event_data = {
                "chain_id": settings.chain_id,
                "address": log["address"],
                "transactionHash": log["transactionHash"],
                "logIndex": log["logIndex"],
                "blockNumber": log["blockNumber"],
                "blockHash": log["blockHash"],
                "event": decoded_event["event"],
                "args": dict(decoded_event["args"]),
            }
            
            # Convert HexBytes to hex strings for JSON serialization
            event_data = _hexbytes_to_json(event_data)
                
            # Process event inside a SAVEPOINT so that a failure (e.g. FK
            # violation for an orphaned on-chain event) only rolls back this
            # single event, leaving all previously processed events intact.
            try:
                async with session.begin_nested():
                    await service.process_event(event_data)
            except IntegrityError:
                # FK violation: agreement_id not found in agreements table.
                # This can hapens when someone calls the smart contract directly
                # with an agreementId that was never created by our backend.
                # The SAVEPOINT was already rolled back by begin_nested(),
                # so the session remains usable for subsequent events.
                agreement_id = event_data.get("args", {}).get("agreementId", "unknown")
                logger.warning(
                    f"Skipping orphaned on-chain event: "
                    f"agreement_id={agreement_id}, tx={event_data.get('transactionHash')}"
                )

        # Update State
        state.last_processed_block = to_block
        state.last_finalized_block = to_block
        await sync_repo.update_state(state)
        
        # Calculate blocks processed and check if we've reached the top
        blocks_processed = to_block - from_block + 1
        reached_top = (to_block >= current_block - confirmations)
        
        return (blocks_processed, reached_top)
