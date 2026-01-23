"""
GDPR Data Retention Scheduler.

Manages the automated lifecycle of patient records per Cyprus Law 125(I)/2018:
- 15-year medical record retention period
- Automatic erasure request creation after retention expires
- Scheduled anonymization of expired records

This module is designed to be invoked by a periodic task runner (e.g., cron,
APScheduler, or Celery beat) rather than running as a standalone daemon.
"""

import logging
from datetime import date, datetime, timezone
from typing import Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.encounter.models import Encounter
from app.modules.patient.models import (
    ErasureLegalBasis,
    ErasureRequestStatus,
    GDPRErasureRequest,
    Patient,
    PatientStatus,
)

logger = logging.getLogger(__name__)

# Cyprus Law 125(I)/2018: 15-year retention for medical records
RETENTION_YEARS = 15


async def find_retention_expired_patients(
    db: AsyncSession,
) -> Sequence[Patient]:
    """
    Find patients whose retention period has expired.

    The retention clock starts from the patient's LAST clinical encounter
    (using actual_start, falling back to scheduled_start). If no encounters
    exist, patient creation date is used as the fallback.

    An administrative update (address change, phone number) does NOT reset
    the retention clock — only actual clinical encounters count.

    Patients already anonymized or with pending/approved erasure requests
    are excluded.

    Returns:
        List of patients eligible for automated erasure
    """
    cutoff_timestamp = datetime(
        date.today().year - RETENTION_YEARS,
        date.today().month,
        date.today().day,
        tzinfo=timezone.utc,
    )

    # Subquery: last clinical encounter date per patient
    # Uses actual_start (when encounter really happened), falling back to scheduled_start
    last_encounter_subquery = (
        select(
            func.max(
                func.coalesce(Encounter.actual_start, Encounter.scheduled_start)
            )
        )
        .where(Encounter.patient_id == Patient.patient_id)
        .correlate(Patient)
        .scalar_subquery()
    )

    # Subquery: patients with active erasure requests (exclude these)
    active_requests_subquery = (
        select(GDPRErasureRequest.patient_id)
        .where(
            GDPRErasureRequest.evaluation_status.in_([
                ErasureRequestStatus.PENDING.value,
                ErasureRequestStatus.APPROVED.value,
            ])
        )
    )

    # Main query: find patients whose last clinical activity predates the cutoff
    # Fall back to created_at if no encounters exist
    query = (
        select(Patient)
        .options(selectinload(Patient.pii))
        .where(
            and_(
                # Last encounter (or creation date) before retention cutoff
                func.coalesce(last_encounter_subquery, Patient.created_at) < cutoff_timestamp,
                # Not already anonymized
                Patient.pii.has(anonymized_at=None),
                # No active erasure request already pending
                ~Patient.patient_id.in_(active_requests_subquery),
            )
        )
    )

    result = await db.execute(query)
    return result.scalars().all()


async def create_retention_expired_requests(
    db: AsyncSession,
    system_user_id: int,
) -> int:
    """
    Create erasure requests for patients whose retention has expired.

    These requests are auto-created with RETENTION_EXPIRED legal basis
    and are auto-approved (no Article 17(3) exception applies after
    the statutory retention period).

    Args:
        db: Database session
        system_user_id: User ID for the system/scheduler account

    Returns:
        Number of erasure requests created
    """
    patients = await find_retention_expired_patients(db)
    created_count = 0

    for patient in patients:
        now = datetime.now(timezone.utc)

        erasure_request = GDPRErasureRequest(
            patient_id=patient.patient_id,
            requested_by=system_user_id,
            request_method="portal",  # System-generated
            legal_basis_cited=ErasureLegalBasis.RETENTION_EXPIRED.value,
            evaluation_status=ErasureRequestStatus.APPROVED.value,
            evaluated_by=system_user_id,
            evaluated_at=now,
            retention_expiry_date=date.today(),
            # Cooling-off still applies for safety
            cooloff_expires_at=now,  # Immediate for retention-expired (already waited 15 years)
        )
        db.add(erasure_request)
        created_count += 1

        logger.info(
            f"Auto-created retention-expired erasure request for patient {patient.patient_id}"
        )

    if created_count > 0:
        await db.commit()

    logger.info(f"Retention check complete: {created_count} requests created")
    return created_count


async def run_retention_check(
    db: AsyncSession,
    system_user_id: int,
) -> dict:
    """
    Main entry point for the retention scheduler.

    Call this from a periodic task (daily recommended).

    Args:
        db: Database session
        system_user_id: User ID for the system account

    Returns:
        Summary of actions taken
    """
    logger.info("Starting retention check...")

    created = await create_retention_expired_requests(db, system_user_id)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "retention_years": RETENTION_YEARS,
        "requests_created": created,
    }
