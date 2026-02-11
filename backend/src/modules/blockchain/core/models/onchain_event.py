"""OnchainEvent model."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.blockchain.core.enums.onchain_event_name import OnchainEventName
from src.shared.database.base import Base


class OnchainEvent(Base):
    """Immutable ledger of on-chain events."""

    __tablename__ = "onchain_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    chain_id: Mapped[int] = mapped_column(Integer, nullable=False)

    contract_address: Mapped[str] = mapped_column(Text, nullable=False)

    tx_hash: Mapped[str] = mapped_column(Text, nullable=False)

    log_index: Mapped[int] = mapped_column(Integer, nullable=False)

    event_name: Mapped[OnchainEventName] = mapped_column(
        ENUM(OnchainEventName, name="onchain_event_name_enum", create_type=False),
        nullable=False,
    )

    agreement_id: Mapped[str] = mapped_column(
        String(66), ForeignKey("agreements.agreement_id"), nullable=False
    )

    block_number: Mapped[int] = mapped_column(BigInteger, nullable=False)

    block_hash: Mapped[str] = mapped_column(Text, nullable=False)

    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    processed_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    agreement = relationship("Agreement", foreign_keys=[agreement_id], lazy="joined")

    __table_args__ = (
        UniqueConstraint(
            "chain_id", "tx_hash", "log_index", name="uq_onchain_events_idempotent"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<OnchainEvent(chain={self.chain_id}, "
            f"event={self.event_name}, "
            f"tx={self.tx_hash}, "
            f"log={self.log_index})>"
        )
