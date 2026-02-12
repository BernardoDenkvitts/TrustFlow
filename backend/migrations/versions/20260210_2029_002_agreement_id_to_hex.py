"""Migrate agreement_id from NUMERIC(78,0) to VARCHAR(66) hex string.

Revision ID: 002_agreement_id_hex
Revises: 001_initial_schema
Create Date: 2026-02-10

The agreement_id is a bytes32 identifier on-chain, not a numeric value.
Storing as hex string eliminates unnecessary conversions and aligns
with the blockchain ecosystem.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "002_agreement_id_hex"
down_revision: str | None = "001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop FK constraints referencing agreements.agreement_id
    op.drop_constraint(
        "onchain_events_agreement_id_fkey",
        "onchain_events",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_disputes_agreement_id",
        "disputes",
        type_="foreignkey",
    )

    # Alter column types from NUMERIC(78,0) to VARCHAR(66)
    op.alter_column(
        "agreements",
        "agreement_id",
        type_=type_from_string("VARCHAR(66)"),
        postgresql_using="'0x' || lpad(to_hex(agreement_id::bigint), 64, '0')",
    )
    op.alter_column(
        "disputes",
        "agreement_id",
        type_=type_from_string("VARCHAR(66)"),
        postgresql_using="'0x' || lpad(to_hex(agreement_id::bigint), 64, '0')",
    )
    op.alter_column(
        "onchain_events",
        "agreement_id",
        type_=type_from_string("VARCHAR(66)"),
        postgresql_using="'0x' || lpad(to_hex(agreement_id::bigint), 64, '0')",
    )

    # Re-create FK constraints
    op.create_foreign_key(
        "fk_disputes_agreement_id",
        "disputes",
        "agreements",
        ["agreement_id"],
        ["agreement_id"],
    )
    op.create_foreign_key(
        "onchain_events_agreement_id_fkey",
        "onchain_events",
        "agreements",
        ["agreement_id"],
        ["agreement_id"],
    )


def downgrade() -> None:
    # Drop FK constraints
    op.drop_constraint(
        "onchain_events_agreement_id_fkey",
        "onchain_events",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_disputes_agreement_id",
        "disputes",
        type_="foreignkey",
    )

    conversion = "('x' || replace(agreement_id, '0x', ''))::bit(256)::numeric"

    # Revert to NUMERIC(78,0)
    op.alter_column(
        "agreements",
        "agreement_id",
        type_=type_from_string("NUMERIC(78,0)"),
        postgresql_using=conversion,
    )
    op.alter_column(
        "disputes",
        "agreement_id",
        type_=type_from_string("NUMERIC(78,0)"),
        postgresql_using=conversion,
    )
    op.alter_column(
        "onchain_events",
        "agreement_id",
        type_=type_from_string("NUMERIC(78,0)"),
        postgresql_using=conversion,
    )

    # Re-create FK constraints
    op.create_foreign_key(
        "fk_disputes_agreement_id",
        "disputes",
        "agreements",
        ["agreement_id"],
        ["agreement_id"],
    )
    op.create_foreign_key(
        "onchain_events_agreement_id_fkey",
        "onchain_events",
        "agreements",
        ["agreement_id"],
        ["agreement_id"],
    )


def type_from_string(type_str: str):
    """Helper to create SA type from string for alter_column."""
    import sqlalchemy as sa

    if type_str.startswith("VARCHAR"):
        length = int(type_str.split("(")[1].rstrip(")"))
        return sa.String(length)
    elif type_str.startswith("NUMERIC"):
        parts = type_str.split("(")[1].rstrip(")").split(",")
        return sa.Numeric(int(parts[0]), int(parts[1]))
    raise ValueError(f"Unsupported type: {type_str}")
