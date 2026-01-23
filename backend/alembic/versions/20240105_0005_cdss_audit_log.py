"""CDSS audit log table for clinical calculation tracking.

Revision ID: 0005
Revises: 0004
Create Date: 2024-01-05 00:00:00.000000

This migration creates:
- cdss_audit_log partitioned table (yearly partitions 2024-2040)
- Indexes for clinician, patient, calculation type lookups
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create partitioned parent table
    op.execute("""
        CREATE TABLE cdss_audit_log (
            log_id BIGSERIAL,
            calculation_type VARCHAR(50) NOT NULL,
            patient_id INTEGER REFERENCES patients(patient_id),
            clinician_id INTEGER NOT NULL REFERENCES users(user_id),
            clinic_id INTEGER NOT NULL REFERENCES clinics(clinic_id),
            input_parameters JSONB NOT NULL,
            calculated_score DOUBLE PRECISION,
            risk_category VARCHAR(50),
            recommendation TEXT,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (log_id, timestamp)
        ) PARTITION BY RANGE (timestamp)
    """)

    # Create yearly partitions (2024-2040 for 15-year retention)
    for year in range(2024, 2041):
        op.execute(f"""
            CREATE TABLE cdss_audit_log_{year} PARTITION OF cdss_audit_log
            FOR VALUES FROM ('{year}-01-01') TO ('{year + 1}-01-01')
        """)

    # Indexes for common queries
    op.execute("""
        CREATE INDEX idx_cdss_audit_clinician ON cdss_audit_log (clinician_id, timestamp)
    """)
    op.execute("""
        CREATE INDEX idx_cdss_audit_patient ON cdss_audit_log (patient_id, timestamp)
    """)
    op.execute("""
        CREATE INDEX idx_cdss_audit_type ON cdss_audit_log (calculation_type, timestamp)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS cdss_audit_log CASCADE")
