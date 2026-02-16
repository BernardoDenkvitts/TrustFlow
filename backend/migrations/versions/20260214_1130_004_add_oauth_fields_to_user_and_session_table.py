"""Add OAuth fields to User

Revision ID: 004_add_oauth_fields_to_user_and_session_table
Revises: 003_remove_pending_funding_enum
Create Date: 2026-02-14 11:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_add_oauth_fields_to_user"
down_revision: str | None = "003_remove_pending_funding_enum"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    oauth_provider_enum = postgresql.ENUM(
        "GOOGLE", name="oauth_provider_enum", create_type=True
    )
    oauth_provider_enum.create(op.get_bind(), checkfirst=True)

    op.add_column("users", sa.Column("oauth_provider", oauth_provider_enum, nullable=True))
    op.add_column("users", sa.Column("oauth_id", sa.Text(), nullable=True))
    op.alter_column("users", "wallet_address", existing_type=sa.TEXT(), nullable=True)
    op.create_unique_constraint("uq_users_oauth_id", "users", ["oauth_id"])
    
    # Drop unused indexes as requested
    op.drop_index("idx_agreements_payer_status", table_name="agreements")
    op.drop_index("idx_agreements_payee_status", table_name="agreements")

    # Create sessions table
    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("refresh_token_hash", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("refresh_token_hash", name="uq_sessions_refresh_token_hash"),
    )
    op.create_index(
        "idx_sessions_user_id", "sessions", ["user_id"], unique=False
    )


def downgrade() -> None:
    # Drop sessions table
    op.drop_index("idx_sessions_user_id", table_name="sessions")
    op.drop_table("sessions")

    # Re-create indexes
    op.create_index("idx_agreements_payee_status", "agreements", ["payee_id", "status"])
    op.create_index("idx_agreements_payer_status", "agreements", ["payer_id", "status"])

    op.drop_constraint("uq_users_oauth_id", "users", type_="unique")
    op.alter_column("users", "wallet_address", existing_type=sa.TEXT(), nullable=False)
    op.drop_column("users", "oauth_id")
    op.drop_column("users", "oauth_provider")
    
    op.execute("DROP TYPE IF EXISTS oauth_provider_enum")