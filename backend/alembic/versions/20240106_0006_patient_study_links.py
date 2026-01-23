"""Patient-to-DICOM study linking table.

Revision ID: 0006
Revises: 0005
Create Date: 2024-01-06 00:00:00.000000

This migration creates:
- patient_study_links table for associating DICOM studies with patients
- Unique constraint on (study_instance_uid, patient_id) to prevent duplicates
- Indexes for patient and study lookups
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patient_study_links",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("study_instance_uid", sa.String(128), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False),
        sa.Column("encounter_id", sa.Integer(), sa.ForeignKey("encounters.encounter_id", ondelete="SET NULL"), nullable=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.clinic_id", ondelete="CASCADE"), nullable=False),
        sa.Column("linked_by_user_id", sa.Integer(), sa.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=False),
        sa.Column("link_reason", sa.String(255), nullable=True),
        sa.Column("study_date", sa.Date(), nullable=True),
        sa.Column("study_description", sa.String(255), nullable=True),
        sa.Column("modality", sa.String(16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("study_instance_uid", "patient_id", name="uq_study_patient"),
        comment="Links DICOM studies to OpenHeart patient records",
    )

    op.create_index("idx_study_links_study_uid", "patient_study_links", ["study_instance_uid"])
    op.create_index("idx_study_links_patient", "patient_study_links", ["patient_id"])
    op.create_index("idx_study_links_clinic", "patient_study_links", ["clinic_id"])


def downgrade() -> None:
    op.drop_table("patient_study_links")
