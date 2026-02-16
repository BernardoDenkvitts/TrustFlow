"""ChainSyncState model."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Integer,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.database.base import Base


class ChainSyncState(Base):
    """Tracks blockchain synchronization state."""

    __tablename__ = "chain_sync_state"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    chain_id: Mapped[int] = mapped_column(Integer, nullable=False)
    contract_address: Mapped[str] = mapped_column(Text, nullable=False)

    last_processed_block: Mapped[int] = mapped_column(
        BigInteger, server_default=text("0"), nullable=False
    )
    last_finalized_block: Mapped[int] = mapped_column(
        BigInteger, server_default=text("0"), nullable=False
    )
    confirmations: Mapped[int] = mapped_column(
        Integer, server_default=text("3"), nullable=False
    )
    reorg_buffer: Mapped[int] = mapped_column(
        Integer, server_default=text("10"), nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "chain_id", "contract_address", name="uq_chain_sync_state_chain_contract"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ChainSyncState(chain_id={self.chain_id}, "
            f"contract={self.contract_address}, "
            f"last_block={self.last_processed_block})>"
        )
