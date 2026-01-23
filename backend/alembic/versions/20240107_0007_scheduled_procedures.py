"""Scheduled procedures and worklist stations tables.

Revision ID: 0007
Revises: 0006
Create Date: 2024-01-07 00:00:00.000000

This migration creates:
- scheduled_procedures table for Modality Worklist (MWL) scheduling
- worklist_stations table for imaging equipment configuration
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create worklist_stations table
    op.create_table(
        "worklist_stations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("clinic_id", sa.Integer(), nullable=False),
        sa.Column(
            "ae_title",
            sa.String(16),
            nullable=False,
            unique=True,
            comment="DICOM Application Entity Title",
        ),
        sa.Column(
            "station_name",
            sa.String(64),
            nullable=False,
            comment="Friendly display name",
        ),
        sa.Column(
            "location",
            sa.String(64),
            nullable=True,
            comment="Physical location (room number, etc.)",
        ),
        sa.Column(
            "modality",
            sa.String(16),
            nullable=False,
        ),
        sa.Column(
            "manufacturer",
            sa.String(64),
            nullable=True,
            comment="Equipment manufacturer (GE, Philips, Siemens)",
        ),
        sa.Column(
            "model",
            sa.String(64),
            nullable=True,
            comment="Equipment model",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "last_query_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Last MWL query timestamp",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.clinic_id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_worklist_stations_clinic_id",
        "worklist_stations",
        ["clinic_id"],
    )

    # Create scheduled_procedures table
    op.create_table(
        "scheduled_procedures",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("clinic_id", sa.Integer(), nullable=False),
        sa.Column(
            "accession_number",
            sa.String(16),
            nullable=False,
            unique=True,
            comment="Unique exam identifier (DICOM 0008,0050)",
        ),
        sa.Column(
            "scheduled_station_ae_title",
            sa.String(16),
            nullable=False,
            comment="Target AE Title: ECHO1, ECHO2, CATH1, etc.",
        ),
        sa.Column(
            "scheduled_station_name",
            sa.String(64),
            nullable=True,
            comment="Friendly name: Echo Room 1, Cath Lab, etc.",
        ),
        sa.Column(
            "modality",
            sa.String(16),
            nullable=False,
            comment="DICOM Modality code",
        ),
        sa.Column(
            "procedure_code",
            sa.String(16),
            nullable=True,
            comment="Procedure code for billing/coding",
        ),
        sa.Column(
            "procedure_description",
            sa.Text(),
            nullable=True,
            comment="Scheduled Procedure Step Description (DICOM 0040,0007)",
        ),
        sa.Column(
            "scheduled_datetime",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Scheduled start date/time",
        ),
        sa.Column(
            "expected_duration_minutes",
            sa.Integer(),
            nullable=True,
            comment="Expected duration in minutes",
        ),
        sa.Column("performing_physician_id", sa.Integer(), nullable=True),
        sa.Column("referring_physician_id", sa.Integer(), nullable=True),
        sa.Column(
            "referring_physician_name",
            sa.String(128),
            nullable=True,
            comment="External referring physician name",
        ),
        sa.Column(
            "study_instance_uid",
            sa.String(64),
            nullable=True,
            comment="Assigned Study Instance UID",
        ),
        sa.Column(
            "scheduled_procedure_step_id",
            sa.String(16),
            nullable=True,
            comment="SPS ID (DICOM 0040,0009)",
        ),
        sa.Column(
            "status",
            sa.String(16),
            nullable=False,
            server_default="SCHEDULED",
        ),
        sa.Column("actual_start_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "reason_for_exam",
            sa.Text(),
            nullable=True,
            comment="Clinical indication",
        ),
        sa.Column(
            "priority",
            sa.String(8),
            nullable=False,
            server_default="ROUTINE",
            comment="STAT, ROUTINE, URGENT",
        ),
        sa.Column("encounter_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.String(256), nullable=True),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
            comment="Internal scheduling notes",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.patient_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.clinic_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["performing_physician_id"],
            ["users.user_id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["referring_physician_id"],
            ["users.user_id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["encounters.encounter_id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.user_id"],
            ondelete="SET NULL",
        ),
    )
    op.create_index(
        "ix_scheduled_procedures_patient_id",
        "scheduled_procedures",
        ["patient_id"],
    )
    op.create_index(
        "ix_scheduled_procedures_clinic_id",
        "scheduled_procedures",
        ["clinic_id"],
    )
    op.create_index(
        "ix_scheduled_procedures_scheduled_datetime",
        "scheduled_procedures",
        ["scheduled_datetime"],
    )
    op.create_index(
        "ix_scheduled_procedures_status",
        "scheduled_procedures",
        ["status"],
    )


def downgrade() -> None:
    op.drop_table("scheduled_procedures")
    op.drop_table("worklist_stations")
