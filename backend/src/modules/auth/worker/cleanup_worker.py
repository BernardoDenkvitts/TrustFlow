"""Session cleanup worker."""

import asyncio
import logging

from src.config import settings
from src.modules.auth.persistence.session_repository import SessionRepository
from src.shared.database.session import async_session_factory

logger = logging.getLogger(__name__)


class SessionCleanupWorker:
    """Worker to periodically clean up expired sessions."""

    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the worker in a background task."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Session cleanup worker started.")

    async def stop(self) -> None:
        """Stop the worker."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Session cleanup worker stopped.")

    async def _run_loop(self) -> None:
        """Main cleanup loop."""
        while self._running:
            try:
                async with async_session_factory() as session:
                    repository = SessionRepository(session)
                    deleted_count = await repository.delete_expired()
                    await session.commit()
                    
                    if deleted_count > 0:
                        logger.info(f"Cleaned up {deleted_count} expired sessions")

            except Exception as e:
                logger.error(f"Error in session cleanup loop: {e}", exc_info=True)

            # Sleep for the configured interval
            await asyncio.sleep(settings.session_cleanup_interval_seconds)
