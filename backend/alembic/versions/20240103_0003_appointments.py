"""Appointments table with conflict detection support and RLS.

Revision ID: 0003
Revises: 0002
Create Date: 2024-01-03 00:00:00.000000

This migration creates:
- Appointments table with scheduling, status tracking, and encounter linking
- Indexes for conflict detection (provider + time range queries)
- RLS policy for clinic-level isolation
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "appointments",
        sa.Column("appointment_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.clinic_id"), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.patient_id"), nullable=False),
        sa.Column("provider_id", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("expected_duration_minutes", sa.Integer(), nullable=True),
        sa.Column(
            "appointment_type",
            sa.String(50),
            nullable=False,
            comment="consultation, follow_up, echo, stress_test, holter, procedure",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="scheduled",
            comment="scheduled, confirmed, checked_in, in_progress, completed, cancelled, no_show",
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("location", sa.String(100), nullable=True),
        sa.Column("gesy_referral_id", sa.String(50), nullable=True),
        sa.Column("encounter_id", sa.Integer(), sa.ForeignKey("encounters.encounter_id"), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_by", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("appointment_id"),
        comment="Patient appointments with conflict detection and encounter linking",
    )

    # Index for conflict detection: provider + time range
    op.create_index(
        "idx_appointments_provider_time",
        "appointments",
        ["provider_id", "start_time", "end_time"],
    )
    # Index for patient schedule lookup
    op.create_index(
        "idx_appointments_patient",
        "appointments",
        ["patient_id", "start_time"],
    )
    # Index for clinic schedule
    op.create_index(
        "idx_appointments_clinic_date",
        "appointments",
        ["clinic_id", "start_time"],
    )
    # Index for status filtering
    op.create_index(
        "idx_appointments_status",
        "appointments",
        ["status"],
    )

    # Row-Level Security for clinic isolation
    op.execute("ALTER TABLE appointments ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY appointments_clinic_isolation ON appointments
        USING (clinic_id = current_setting('app.current_clinic_id')::integer)
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS appointments_clinic_isolation ON appointments")
    op.execute("ALTER TABLE appointments DISABLE ROW LEVEL SECURITY")
    op.drop_table("appointments")
