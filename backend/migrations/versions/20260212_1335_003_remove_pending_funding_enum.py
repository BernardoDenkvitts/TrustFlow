"""Remove PENDING_FUNDING status

Revision ID: 003_remove_pending_funding_enum
Revises: 002_agreement_id_hex
Create Date: 2026-02-14 12:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "003_remove_pending_funding_enum"
down_revision: str | None = "002_agreement_id_hex"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD_TYPE = "agreement_status_enum"
TMP_TYPE = "agreement_status_enum__tmp"


def upgrade() -> None:
    op.execute("""
        ALTER TABLE agreements
        ALTER COLUMN status DROP DEFAULT
    """)

    op.execute(f"""
        CREATE TYPE {TMP_TYPE} AS ENUM (
            'DRAFT',
            'CREATED',
            'FUNDED',
            'DISPUTED',
            'RELEASED',
            'REFUNDED'
        )
    """)

    op.execute(f"""
        ALTER TABLE agreements
        ALTER COLUMN status
        TYPE {TMP_TYPE}
        USING status::text::{TMP_TYPE}
    """)

    op.execute(f"DROP TYPE {OLD_TYPE}")

    op.execute(f"ALTER TYPE {TMP_TYPE} RENAME TO {OLD_TYPE}")

    op.execute("""
        ALTER TABLE agreements
        ALTER COLUMN status SET DEFAULT 'DRAFT'
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE agreements
        ALTER COLUMN status DROP DEFAULT
    """)

    op.execute(f"""
        CREATE TYPE {TMP_TYPE} AS ENUM (
            'DRAFT',
            'PENDING_FUNDING',
            'CREATED',
            'FUNDED',
            'DISPUTED',
            'RELEASED',
            'REFUNDED'
        )
    """)

    op.execute(f"""
        ALTER TABLE agreements
        ALTER COLUMN status
        TYPE {TMP_TYPE}
        USING status::text::{TMP_TYPE}
    """)

    op.execute(f"DROP TYPE {OLD_TYPE}")

    op.execute(f"ALTER TYPE {TMP_TYPE} RENAME TO {OLD_TYPE}")

    op.execute("""
        ALTER TABLE agreements
        ALTER COLUMN status SET DEFAULT 'DRAFT'
    """)

