"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2026-02-02

Creates all tables:
- users
- agreements
- disputes
- onchain_events
- chain_sync_state
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    arbitration_policy_enum = postgresql.ENUM(
        "NONE", "WITH_ARBITRATOR", name="arbitration_policy_enum", create_type=True
    )
    agreement_status_enum = postgresql.ENUM(
        "DRAFT",
        "PENDING_FUNDING",
        "CREATED",
        "FUNDED",
        "DISPUTED",
        "RELEASED",
        "REFUNDED",
        name="agreement_status_enum",
        create_type=True,
    )
    dispute_status_enum = postgresql.ENUM(
        "OPEN", "RESOLVED", name="dispute_status_enum", create_type=True
    )
    dispute_resolution_enum = postgresql.ENUM(
        "RELEASE", "REFUND", name="dispute_resolution_enum", create_type=True
    )
    onchain_event_name_enum = postgresql.ENUM(
        "AGREEMENT_CREATED",
        "PAYMENT_FUNDED",
        "DISPUTE_OPENED",
        "PAYMENT_RELEASED",
        "PAYMENT_REFUNDED",
        name="onchain_event_name_enum",
        create_type=True,
    )

    # users table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("wallet_address", sa.Text(), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "wallet_address ~ '^0x[0-9a-f]{40}$'",
            name="ck_users_wallet_address_format",
        ),
    )

    # agreements table
    op.create_table(
        "agreements",
        sa.Column(
            "agreement_id", sa.Numeric(78, 0), primary_key=True, autoincrement=False
        ),
        sa.Column("payer_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("payee_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("arbitrator_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column(
            "arbitration_policy",
            arbitration_policy_enum,
            nullable=False,
        ),
        sa.Column("amount_wei", sa.Numeric(78, 0), nullable=False),
        sa.Column(
            "status",
            agreement_status_enum,
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("created_tx_hash", sa.Text(), nullable=True),
        sa.Column("funded_tx_hash", sa.Text(), nullable=True),
        sa.Column("released_tx_hash", sa.Text(), nullable=True),
        sa.Column("refunded_tx_hash", sa.Text(), nullable=True),
        sa.Column("created_onchain_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("funded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # Constraints
        sa.CheckConstraint("payer_id <> payee_id", name="ck_agreements_no_self_deal"),
        sa.CheckConstraint("amount_wei > 0", name="ck_agreements_positive_amount"),
        sa.CheckConstraint(
            "(arbitration_policy = 'NONE' AND arbitrator_id IS NULL) OR "
            "(arbitration_policy = 'WITH_ARBITRATOR' AND arbitrator_id IS NOT NULL)",
            name="ck_agreements_policy_arbitrator",
        ),
    )

    # disputes table
    op.create_table(
        "disputes",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("agreement_id", sa.Numeric(78, 0), nullable=False, unique=True),
        sa.Column("opened_by", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            dispute_status_enum,
            nullable=False,
            server_default="OPEN",
        ),
        sa.Column("resolution", dispute_resolution_enum, nullable=True),
        sa.Column("resolution_tx_hash", sa.Text(), nullable=True),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column(
            "opened_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        # Constraint for OPEN vs RESOLVED consistency
        sa.CheckConstraint(
            "(status = 'OPEN' AND resolved_at IS NULL AND resolution IS NULL "
            "AND resolution_tx_hash IS NULL AND justification IS NULL) OR "
            "(status = 'RESOLVED' AND resolved_at IS NOT NULL AND resolution IS NOT NULL "
            "AND resolution_tx_hash IS NOT NULL AND justification IS NOT NULL)",
            name="ck_disputes_status_consistency",
        ),
        # Foreign keys defined explicitly to avoid type inference issues with Numeric
        sa.ForeignKeyConstraint(
            ["agreement_id"], ["agreements.agreement_id"], name="fk_disputes_agreement_id"
        ),
        sa.ForeignKeyConstraint(
            ["opened_by"], ["users.id"], name="fk_disputes_opened_by"
        ),
    )

    # onchain_events table
    op.create_table(
        "onchain_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("chain_id", sa.Integer(), nullable=False),
        sa.Column("contract_address", sa.Text(), nullable=False),
        sa.Column("tx_hash", sa.Text(), nullable=False),
        sa.Column("log_index", sa.Integer(), nullable=False),
        sa.Column("event_name", onchain_event_name_enum, nullable=False),
        sa.Column(
            "agreement_id",
            sa.Numeric(78, 0),
            sa.ForeignKey("agreements.agreement_id"),
            nullable=False,
        ),
        sa.Column("block_number", sa.BigInteger(), nullable=False),
        sa.Column("block_hash", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # Idempotency constraint
        sa.UniqueConstraint(
            "chain_id", "tx_hash", "log_index", name="uq_onchain_events_idempotent"
        ),
    )

    # chain_sync_state table
    op.create_table(
        "chain_sync_state",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("chain_id", sa.Integer(), nullable=False),
        sa.Column("contract_address", sa.Text(), nullable=False),
        sa.Column(
            "last_processed_block", sa.BigInteger(), nullable=False, server_default="0"
        ),
        sa.Column(
            "last_finalized_block", sa.BigInteger(), nullable=False, server_default="0"
        ),
        sa.Column("confirmations", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("reorg_buffer", sa.Integer(), nullable=False, server_default="10"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # One checkpoint per contract per chain
        sa.UniqueConstraint(
            "chain_id", "contract_address", name="uq_chain_sync_state_chain_contract"
        ),
    )

    # Create indexes
    op.create_index("idx_agreements_status", "agreements", ["status"])
    op.create_index(
        "idx_agreements_payer_status", "agreements", ["payer_id", "status"]
    )
    op.create_index(
        "idx_agreements_payee_status", "agreements", ["payee_id", "status"]
    )
    op.create_index(
        "idx_onchain_events_chain_block_log",
        "onchain_events",
        ["chain_id", "block_number", "log_index"],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_onchain_events_chain_block_log", table_name="onchain_events")
    op.drop_index("idx_agreements_payee_status", table_name="agreements")
    op.drop_index("idx_agreements_payer_status", table_name="agreements")
    op.drop_index("idx_agreements_status", table_name="agreements")

    # Drop tables
    op.drop_table("chain_sync_state")
    op.drop_table("onchain_events")
    op.drop_table("disputes")
    op.drop_table("agreements")
    op.drop_table("users")

    # Drop ENUMs using raw SQL for asyncpg compatibility
    op.execute("DROP TYPE IF EXISTS onchain_event_name_enum")
    op.execute("DROP TYPE IF EXISTS dispute_resolution_enum")
    op.execute("DROP TYPE IF EXISTS dispute_status_enum")
    op.execute("DROP TYPE IF EXISTS agreement_status_enum")
    op.execute("DROP TYPE IF EXISTS arbitration_policy_enum")
