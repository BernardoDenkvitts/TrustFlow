"""Relax disputes justification constraint

Revision ID: 005_relax_disputes_constraints
Revises: 004_add_oauth_fields_to_user
Create Date: 2026-02-20

Justification is now submitted by the arbitrator separately via API,
after the sync worker has already resolved the dispute. The CheckConstraint
previously required justification IS NOT NULL for RESOLVED disputes.

New constraint: RESOLVED disputes require only resolved_at, resolution,
and resolution_tx_hash to be set. justification is allowed to be NULL.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005_relax_disputes_constraints"
down_revision: str | None = "004_add_oauth_fields_to_user"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OLD_CONSTRAINT = (
    "(status = 'OPEN' AND resolved_at IS NULL AND resolution IS NULL "
    "AND resolution_tx_hash IS NULL AND justification IS NULL) OR "
    "(status = 'RESOLVED' AND resolved_at IS NOT NULL AND resolution IS NOT NULL "
    "AND resolution_tx_hash IS NOT NULL AND justification IS NOT NULL)"
)

_NEW_CONSTRAINT = (
    "(status = 'OPEN' AND resolved_at IS NULL AND resolution IS NULL "
    "AND resolution_tx_hash IS NULL AND justification IS NULL) OR "
    "(status = 'RESOLVED' AND resolved_at IS NOT NULL AND resolution IS NOT NULL "
    "AND resolution_tx_hash IS NOT NULL)"
)


def upgrade() -> None:
    op.drop_constraint(
        "ck_disputes_status_consistency",
        "disputes",
        type_="check",
    )
    op.create_check_constraint(
        "ck_disputes_status_consistency",
        "disputes",
        _NEW_CONSTRAINT,
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_disputes_status_consistency",
        "disputes",
        type_="check",
    )
    op.create_check_constraint(
        "ck_disputes_status_consistency",
        "disputes",
        _OLD_CONSTRAINT,
    )
