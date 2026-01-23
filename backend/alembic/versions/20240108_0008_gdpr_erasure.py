"""GDPR Article 17 erasure request tables and patient model updates.

Revision ID: 0008
Revises: 0007
Create Date: 2024-01-08 00:00:00.000000

This migration creates:
- gdpr_erasure_requests table for tracking right-to-erasure lifecycle
- Adds deactivation_reason to patients table
- Adds anonymized_at to patient_pii table
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add deactivation_reason to patients
    op.add_column(
        "patients",
        sa.Column(
            "deactivation_reason",
            sa.String(255),
            nullable=True,
            comment="Reason for deactivation (transfer, duplicate, etc.)",
        ),
    )

    # Add anonymized_at to patient_pii
    op.add_column(
        "patient_pii",
        sa.Column(
            "anonymized_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When PII was anonymized (Tier 2 erasure)",
        ),
    )

    # Create GDPR erasure requests table
    op.create_table(
        "gdpr_erasure_requests",
        sa.Column("request_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "patient_id",
            sa.Integer(),
            sa.ForeignKey("patients.patient_id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Request metadata
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "requested_by",
            sa.Integer(),
            sa.ForeignKey("users.user_id", ondelete="SET NULL"),
            nullable=False,
        ),
        sa.Column(
            "request_method",
            sa.String(20),
            nullable=False,
            comment="How request was received: written, email, portal, in_person",
        ),
        sa.Column(
            "legal_basis_cited",
            sa.String(50),
            nullable=False,
            comment="Article 17(1) ground cited by data subject",
        ),
        # Evaluation
        sa.Column(
            "evaluation_status",
            sa.String(20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "evaluated_by",
            sa.Integer(),
            sa.ForeignKey("users.user_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "denial_reason",
            sa.Text(),
            nullable=True,
            comment="Article 17(3) exception justifying denial",
        ),
        # Retention tracking
        sa.Column(
            "retention_expiry_date",
            sa.Date(),
            nullable=True,
            comment="When 15-year Cyprus retention period ends",
        ),
        # 72-hour cooling-off
        sa.Column(
            "cooloff_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="evaluated_at + 72 hours; execution blocked until this passes",
        ),
        # Cancellation
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        # Execution
        sa.Column(
            "executed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When anonymization was performed",
        ),
        sa.Column(
            "execution_details",
            postgresql.JSONB(),
            nullable=True,
            comment="Summary of what was anonymized",
        ),
        sa.PrimaryKeyConstraint("request_id"),
        comment="GDPR Article 17 erasure request lifecycle",
    )

    # Indexes
    op.create_index(
        "idx_erasure_patient_status",
        "gdpr_erasure_requests",
        ["patient_id", "evaluation_status"],
    )
    op.create_index(
        "idx_erasure_pending",
        "gdpr_erasure_requests",
        ["evaluation_status"],
        postgresql_where=sa.text("evaluation_status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_table("gdpr_erasure_requests")
    op.drop_column("patient_pii", "anonymized_at")
    op.drop_column("patients", "deactivation_reason")
