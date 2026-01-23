"""Auth support tables: invitations, password resets, sessions.

Revision ID: 0004
Revises: 0003
Create Date: 2024-01-04 00:00:00.000000

This migration creates:
- user_invitations table for admin-driven user onboarding
- password_reset_tokens table for forgotten password flow
- user_sessions table for server-side session tracking
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # user_invitations
    # =========================================================================
    op.create_table(
        "user_invitations",
        sa.Column("invitation_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("token", sa.String(64), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.clinic_id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, comment="Role to assign upon acceptance"),
        sa.Column("title", sa.String(50), nullable=True),
        sa.Column("specialty", sa.String(100), nullable=True),
        sa.Column("license_number", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("invited_by_user_id", sa.Integer(), sa.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_user_id", sa.Integer(), sa.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("invitation_id"),
        comment="User invitations for onboarding new users",
    )

    op.create_index("idx_invitations_token", "user_invitations", ["token"])
    op.create_index("idx_invitations_email", "user_invitations", ["email"])
    op.create_index("idx_invitations_status", "user_invitations", ["status"])
    op.create_index("idx_invitations_clinic", "user_invitations", ["clinic_id"])

    # =========================================================================
    # password_reset_tokens
    # =========================================================================
    op.create_table(
        "password_reset_tokens",
        sa.Column("token_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("token", sa.String(64), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("token_id"),
        comment="Password reset tokens for forgotten password flow",
    )

    op.create_index("idx_reset_tokens_token", "password_reset_tokens", ["token"])
    op.create_index("idx_reset_tokens_user", "password_reset_tokens", ["user_id"])

    # =========================================================================
    # user_sessions
    # =========================================================================
    op.create_table(
        "user_sessions",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True, comment="SHA-256 hash of JWT"),
        sa.Column("ip_address", sa.String(45), nullable=False, comment="Client IP (supports IPv6)"),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("device_name", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_activity", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.String(50), nullable=True, comment="logout, password_change, admin_revoke"),
        sa.PrimaryKeyConstraint("id"),
        comment="Server-side session tracking for security monitoring",
    )

    op.create_index("idx_sessions_user", "user_sessions", ["user_id"])
    op.create_index("idx_sessions_token_hash", "user_sessions", ["token_hash"])


def downgrade() -> None:
    op.drop_table("user_sessions")
    op.drop_table("password_reset_tokens")
    op.drop_table("user_invitations")
