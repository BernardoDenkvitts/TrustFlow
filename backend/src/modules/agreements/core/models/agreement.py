"""Agreement domain model"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.agreements.core.enums import AgreementStatus, ArbitrationPolicy
from src.shared.database.base import Base


class Agreement(Base):
    """Agreement entity representing a payment agreement in escrow."""

    __tablename__ = "agreements"

    # Primary key: bytes32 identifier from smart contract (hex string)
    agreement_id: Mapped[str] = mapped_column(
        String(66),
        primary_key=True,
        autoincrement=False,
    )

    # Participants (foreign keys to users)
    payer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    payee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    arbitrator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    # Agreement details
    arbitration_policy: Mapped[ArbitrationPolicy] = mapped_column(
        ENUM(ArbitrationPolicy, name="arbitration_policy_enum", create_type=False),
        nullable=False,
    )
    amount_wei: Mapped[Decimal] = mapped_column(
        Numeric(78, 0),
        nullable=False,
    )
    status: Mapped[AgreementStatus] = mapped_column(
        ENUM(AgreementStatus, name="agreement_status_enum", create_type=False),
        nullable=False,
        server_default="DRAFT",
    )

    # Transaction hashes (populated by blockchain events)
    created_tx_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    funded_tx_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    released_tx_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    refunded_tx_hash: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Blockchain timestamps (populated by blockchain events)
    created_onchain_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    funded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    released_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    refunded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Database timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    payer = relationship("User", foreign_keys=[payer_id], lazy="joined")
    payee = relationship("User", foreign_keys=[payee_id], lazy="joined")
    arbitrator = relationship("User", foreign_keys=[arbitrator_id], lazy="joined")

    __table_args__ = (
        CheckConstraint("payer_id <> payee_id", name="ck_agreements_no_self_deal"),
        CheckConstraint("amount_wei > 0", name="ck_agreements_positive_amount"),
        CheckConstraint(
            "(arbitration_policy = 'NONE' AND arbitrator_id IS NULL) OR "
            "(arbitration_policy = 'WITH_ARBITRATOR' AND arbitrator_id IS NOT NULL)",
            name="ck_agreements_policy_arbitrator",
        ),
        Index("idx_agreements_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Agreement(id={self.agreement_id}, "
            f"status={self.status.value}, "
            f"amount_wei={self.amount_wei})>"
        )
