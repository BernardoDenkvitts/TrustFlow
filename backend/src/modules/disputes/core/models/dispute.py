"""Dispute domain model"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.disputes.core.enums import DisputeResolution, DisputeStatus
from src.shared.database.base import Base


class Dispute(Base):
    """Dispute entity representing a payment dispute in the system.

    A dispute is created when either the payer or payee opens a dispute
    on-chain via openDispute(). Only one dispute per agreement is allowed
    in the MVP.
    """

    __tablename__ = "disputes"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Foreign key to agreement (unique - 1 dispute per agreement)
    agreement_id: Mapped[str] = mapped_column(
        String(66),
        ForeignKey("agreements.agreement_id"),
        nullable=False,
        unique=True,
    )

    # Who opened the dispute (payer or payee)
    opened_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    # Dispute status
    status: Mapped[DisputeStatus] = mapped_column(
        ENUM(DisputeStatus, name="dispute_status_enum", create_type=False),
        nullable=False,
        server_default="OPEN",
    )

    # Resolution (set when dispute is resolved)
    resolution: Mapped[DisputeResolution | None] = mapped_column(
        ENUM(DisputeResolution, name="dispute_resolution_enum", create_type=False),
        nullable=True,
    )

    # Transaction hash from on-chain resolution
    resolution_tx_hash: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Arbitrator's justification for the resolution
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    opened_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    agreement = relationship("Agreement", lazy="joined")
    opener = relationship("User", foreign_keys=[opened_by], lazy="joined")

    __table_args__ = (
        # Constraint: OPEN disputes must not have resolution fields set
        # RESOLVED disputes must have all resolution fields set
        CheckConstraint(
            "(status = 'OPEN' "
            "AND resolved_at IS NULL "
            "AND resolution IS NULL "
            "AND resolution_tx_hash IS NULL "
            "AND justification IS NULL) "
            "OR "
            "(status = 'RESOLVED' "
            "AND resolved_at IS NOT NULL "
            "AND resolution IS NOT NULL "
            "AND resolution_tx_hash IS NOT NULL "
            "AND justification IS NOT NULL)",
            name="ck_disputes_status_consistency",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Dispute(id={self.id}, "
            f"agreement_id={self.agreement_id}, "
            f"status={self.status.value})>"
        )
