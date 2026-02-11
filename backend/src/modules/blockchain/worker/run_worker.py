"""
Standalone script to run the blockchain synchronization worker.

This script should be run as a separate process from the FastAPI application,
allowing the API to scale horizontally with multiple workers while maintaining
a single blockchain sync worker to avoid duplicate processing.

Usage:
    python -m src.modules.blockchain.worker.run_worker
"""

import asyncio
import logging
import signal
import sys

from src.modules.blockchain.worker.sync_worker import ChainSyncWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


async def main() -> None:
    """Main entry point for the blockchain sync worker."""
    worker = ChainSyncWorker()
    
    # Setup graceful shutdown
    shutdown_event = asyncio.Event()
    
    def signal_handler(sig: int, frame) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {sig}, initiating graceful shutdown...")
        shutdown_event.set()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await worker.start()
        logger.info("Blockchain sync worker is running. Press Ctrl+C to stop.")

        await shutdown_event.wait()
        
    except Exception as e:
        logger.error(f"Fatal error in blockchain sync worker: {e}", exc_info=True)
        raise
    finally:
        # Graceful shutdown
        logger.info("Stopping blockchain sync worker...")
        await worker.stop()
        logger.info("Blockchain sync worker stopped successfully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Worker failed: {e}", exc_info=True)
        sys.exit(1)
