"""
Modality Worklist (MWL) Service for OpenHeart Cyprus.

Manages scheduled procedures and provides worklist data for
DICOM equipment to query. Generates accession numbers and
tracks procedure lifecycle.
"""

import logging
from datetime import datetime, date, timedelta, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import and_, or_, select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.integrations.dicom.mwl_models import (
    ImagingModality,
    ProcedureStatus,
    ScheduledProcedure,
    WorklistStation,
)
from app.modules.patient.models import Patient

logger = logging.getLogger(__name__)


def generate_accession_number(clinic_code: str, year: int, sequence: int) -> str:
    """
    Generate a unique accession number.

    Format: {CLINIC_CODE}{YEAR_2DIGIT}{SEQUENCE_5DIGIT}
    Example: LIM25-00001

    Args:
        clinic_code: 3-letter clinic code
        year: Year (4 digit)
        sequence: Sequential number

    Returns:
        Formatted accession number
    """
    return f"{clinic_code[:3].upper()}{year % 100:02d}-{sequence:05d}"


def generate_study_instance_uid() -> str:
    """
    Generate a unique DICOM Study Instance UID.

    Uses root OID prefix (fictional for OpenHeart) + timestamp + random.
    Format: 1.2.826.0.1.3680043.8.1234.{timestamp}.{random}
    """
    # Using a fictional OID root for OpenHeart Cyprus
    # In production, this should be registered with IANA
    root = "1.2.826.0.1.3680043.8.1234"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    random_part = uuid4().int % 10000000
    return f"{root}.{timestamp}.{random_part}"


class MWLService:
    """
    Modality Worklist management service.

    Handles scheduling, status updates, and worklist queries
    for DICOM imaging procedures.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def schedule_procedure(
        self,
        patient_id: int,
        clinic_id: int,
        modality: ImagingModality,
        scheduled_datetime: datetime,
        station_ae_title: str,
        procedure_description: Optional[str] = None,
        procedure_code: Optional[str] = None,
        performing_physician_id: Optional[int] = None,
        referring_physician_id: Optional[int] = None,
        referring_physician_name: Optional[str] = None,
        reason_for_exam: Optional[str] = None,
        priority: str = "ROUTINE",
        encounter_id: Optional[int] = None,
        expected_duration_minutes: Optional[int] = None,
        notes: Optional[str] = None,
        created_by_user_id: Optional[int] = None,
        clinic_code: str = "OHC",
    ) -> ScheduledProcedure:
        """
        Schedule a new imaging procedure.

        Creates a record that will appear in the Modality Worklist
        when the specified imaging equipment queries for work.

        Args:
            patient_id: OpenHeart patient ID
            clinic_id: Clinic ID for RLS
            modality: Type of imaging (US, XA, CT, etc.)
            scheduled_datetime: When the procedure is scheduled
            station_ae_title: Target equipment AE title
            procedure_description: Description of the procedure
            procedure_code: Billing/coding code
            performing_physician_id: Assigned physician
            referring_physician_id: Internal referring physician
            referring_physician_name: External referring physician
            reason_for_exam: Clinical indication
            priority: STAT, URGENT, or ROUTINE
            encounter_id: Linked encounter
            expected_duration_minutes: Expected duration
            notes: Internal notes
            created_by_user_id: User who scheduled
            clinic_code: 3-letter clinic code for accession number

        Returns:
            Created ScheduledProcedure

        Raises:
            ValueError: If patient not found or station not configured
        """
        # Verify patient exists
        patient_result = await self.db.execute(
            select(Patient).where(Patient.patient_id == patient_id)
        )
        patient = patient_result.scalar_one_or_none()
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")

        # Verify station is configured
        station_result = await self.db.execute(
            select(WorklistStation).where(
                WorklistStation.ae_title == station_ae_title,
                WorklistStation.is_active == True,
            )
        )
        station = station_result.scalar_one_or_none()
        if not station:
            # Allow scheduling even if station not configured (for flexibility)
            logger.warning(f"Station {station_ae_title} not configured")

        # Generate accession number
        year = scheduled_datetime.year
        count_result = await self.db.execute(
            select(func.count(ScheduledProcedure.id)).where(
                ScheduledProcedure.clinic_id == clinic_id,
                ScheduledProcedure.created_at >= datetime(year, 1, 1, tzinfo=timezone.utc),
            )
        )
        sequence = (count_result.scalar() or 0) + 1
        accession_number = generate_accession_number(clinic_code, year, sequence)

        # Generate Study Instance UID
        study_instance_uid = generate_study_instance_uid()

        # Create scheduled procedure
        procedure = ScheduledProcedure(
            patient_id=patient_id,
            clinic_id=clinic_id,
            accession_number=accession_number,
            scheduled_station_ae_title=station_ae_title,
            scheduled_station_name=station.station_name if station else None,
            modality=modality,
            procedure_code=procedure_code,
            procedure_description=procedure_description,
            scheduled_datetime=scheduled_datetime,
            expected_duration_minutes=expected_duration_minutes,
            performing_physician_id=performing_physician_id,
            referring_physician_id=referring_physician_id,
            referring_physician_name=referring_physician_name,
            study_instance_uid=study_instance_uid,
            scheduled_procedure_step_id=f"SPS{sequence:05d}",
            status=ProcedureStatus.SCHEDULED,
            reason_for_exam=reason_for_exam,
            priority=priority,
            encounter_id=encounter_id,
            notes=notes,
            created_by_user_id=created_by_user_id,
        )

        self.db.add(procedure)
        await self.db.commit()
        await self.db.refresh(procedure)

        logger.info(
            f"Scheduled {modality.value} procedure {accession_number} for patient {patient_id} "
            f"on {station_ae_title} at {scheduled_datetime}"
        )

        return procedure

    async def get_worklist(
        self,
        station_ae_title: Optional[str] = None,
        modality: Optional[ImagingModality] = None,
        scheduled_date: Optional[date] = None,
        clinic_id: Optional[int] = None,
        patient_id: Optional[str] = None,
        accession_number: Optional[str] = None,
        include_completed: bool = False,
    ) -> list[dict]:
        """
        Query the worklist for scheduled procedures.

        This method is called when imaging equipment performs
        a DICOM MWL C-FIND query. Returns procedures matching
        the filter criteria in DICOM-compatible format.

        Args:
            station_ae_title: Filter by target station
            modality: Filter by modality
            scheduled_date: Filter by date (default: today)
            clinic_id: Filter by clinic (for multi-clinic support)
            patient_id: Filter by patient's DICOM ID
            accession_number: Filter by accession number
            include_completed: Include completed procedures

        Returns:
            List of procedures in worklist format
        """
        # Build query
        query = (
            select(ScheduledProcedure)
            .options(selectinload(ScheduledProcedure.patient))
            .options(selectinload(ScheduledProcedure.performing_physician))
        )

        # Apply filters
        filters = []

        if station_ae_title:
            filters.append(
                ScheduledProcedure.scheduled_station_ae_title == station_ae_title
            )

        if modality:
            filters.append(ScheduledProcedure.modality == modality)

        if clinic_id:
            filters.append(ScheduledProcedure.clinic_id == clinic_id)

        if accession_number:
            filters.append(ScheduledProcedure.accession_number == accession_number)

        # Date filter (default to today)
        if scheduled_date:
            start_of_day = datetime.combine(scheduled_date, datetime.min.time()).replace(
                tzinfo=timezone.utc
            )
            end_of_day = start_of_day + timedelta(days=1)
            filters.append(ScheduledProcedure.scheduled_datetime >= start_of_day)
            filters.append(ScheduledProcedure.scheduled_datetime < end_of_day)

        # Status filter
        if include_completed:
            filters.append(
                ScheduledProcedure.status.in_([
                    ProcedureStatus.SCHEDULED,
                    ProcedureStatus.IN_PROGRESS,
                    ProcedureStatus.COMPLETED,
                ])
            )
        else:
            filters.append(
                ScheduledProcedure.status.in_([
                    ProcedureStatus.SCHEDULED,
                    ProcedureStatus.IN_PROGRESS,
                ])
            )

        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(ScheduledProcedure.scheduled_datetime)

        result = await self.db.execute(query)
        procedures = result.scalars().all()

        # Format for DICOM MWL response
        worklist_items = []
        for proc in procedures:
            patient = proc.patient
            if not patient:
                continue

            item = {
                # Patient Module
                "PatientID": patient.cyprus_id or str(patient.patient_id),
                "PatientName": f"{patient.last_name}^{patient.first_name}",
                "PatientBirthDate": (
                    patient.date_of_birth.strftime("%Y%m%d")
                    if patient.date_of_birth
                    else ""
                ),
                "PatientSex": patient.sex or "",
                # Requested Procedure Module
                "AccessionNumber": proc.accession_number,
                "RequestedProcedureID": proc.accession_number,
                "RequestedProcedureDescription": proc.procedure_description or "",
                "StudyInstanceUID": proc.study_instance_uid or "",
                "ReasonForTheRequestedProcedure": proc.reason_for_exam or "",
                "RequestedProcedurePriority": proc.priority,
                # Scheduled Procedure Step Module
                "ScheduledProcedureStepStartDate": (
                    proc.scheduled_datetime.strftime("%Y%m%d")
                ),
                "ScheduledProcedureStepStartTime": (
                    proc.scheduled_datetime.strftime("%H%M%S")
                ),
                "Modality": proc.modality.value,
                "ScheduledStationAETitle": proc.scheduled_station_ae_title,
                "ScheduledStationName": proc.scheduled_station_name or "",
                "ScheduledProcedureStepDescription": proc.procedure_description or "",
                "ScheduledProcedureStepID": proc.scheduled_procedure_step_id or "",
                "ScheduledProcedureStepStatus": proc.status.value,
                # Performing Physician
                "ScheduledPerformingPhysicianName": (
                    proc.performing_physician.full_name
                    if proc.performing_physician
                    else ""
                ),
                # Referring Physician
                "ReferringPhysicianName": (
                    proc.referring_physician_name or ""
                ),
                # OpenHeart internal IDs (for linking)
                "_openheart_procedure_id": str(proc.id),
                "_openheart_patient_id": proc.patient_id,
                "_openheart_encounter_id": proc.encounter_id,
            }
            worklist_items.append(item)

        # Update station last query timestamp
        if station_ae_title:
            await self.db.execute(
                update(WorklistStation)
                .where(WorklistStation.ae_title == station_ae_title)
                .values(last_query_at=datetime.now(timezone.utc))
            )
            await self.db.commit()

        return worklist_items

    async def update_procedure_status(
        self,
        procedure_id: str,
        status: ProcedureStatus,
        actual_start_datetime: Optional[datetime] = None,
        actual_end_datetime: Optional[datetime] = None,
        study_instance_uid: Optional[str] = None,
    ) -> Optional[ScheduledProcedure]:
        """
        Update procedure status (MPPS callback).

        Called when imaging equipment reports procedure progress
        via DICOM MPPS (Modality Performed Procedure Step).

        Args:
            procedure_id: Procedure UUID
            status: New status
            actual_start_datetime: When exam actually started
            actual_end_datetime: When exam completed
            study_instance_uid: Study UID from equipment

        Returns:
            Updated procedure or None if not found
        """
        result = await self.db.execute(
            select(ScheduledProcedure).where(ScheduledProcedure.id == procedure_id)
        )
        procedure = result.scalar_one_or_none()

        if not procedure:
            return None

        procedure.status = status

        if actual_start_datetime:
            procedure.actual_start_datetime = actual_start_datetime

        if actual_end_datetime:
            procedure.actual_end_datetime = actual_end_datetime

        if study_instance_uid:
            procedure.study_instance_uid = study_instance_uid

        await self.db.commit()
        await self.db.refresh(procedure)

        logger.info(
            f"Updated procedure {procedure.accession_number} status to {status.value}"
        )

        return procedure

    async def cancel_procedure(
        self,
        procedure_id: str,
        cancellation_reason: str,
        cancelled_by_user_id: Optional[int] = None,
    ) -> Optional[ScheduledProcedure]:
        """
        Cancel a scheduled procedure.

        Args:
            procedure_id: Procedure UUID
            cancellation_reason: Why it was cancelled
            cancelled_by_user_id: User who cancelled

        Returns:
            Cancelled procedure or None if not found
        """
        result = await self.db.execute(
            select(ScheduledProcedure).where(
                ScheduledProcedure.id == procedure_id,
                ScheduledProcedure.status == ProcedureStatus.SCHEDULED,
            )
        )
        procedure = result.scalar_one_or_none()

        if not procedure:
            return None

        procedure.status = ProcedureStatus.CANCELLED
        procedure.cancelled_at = datetime.now(timezone.utc)
        procedure.cancellation_reason = cancellation_reason

        await self.db.commit()
        await self.db.refresh(procedure)

        logger.info(f"Cancelled procedure {procedure.accession_number}: {cancellation_reason}")

        return procedure

    async def get_procedure(self, procedure_id: str) -> Optional[ScheduledProcedure]:
        """Get a procedure by ID."""
        result = await self.db.execute(
            select(ScheduledProcedure)
            .where(ScheduledProcedure.id == procedure_id)
            .options(selectinload(ScheduledProcedure.patient))
            .options(selectinload(ScheduledProcedure.performing_physician))
        )
        return result.scalar_one_or_none()

    async def get_patient_procedures(
        self,
        patient_id: int,
        include_cancelled: bool = False,
        limit: int = 20,
    ) -> list[ScheduledProcedure]:
        """Get all scheduled procedures for a patient."""
        query = (
            select(ScheduledProcedure)
            .where(ScheduledProcedure.patient_id == patient_id)
            .order_by(ScheduledProcedure.scheduled_datetime.desc())
            .limit(limit)
        )

        if not include_cancelled:
            query = query.where(ScheduledProcedure.status != ProcedureStatus.CANCELLED)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_stations(self, clinic_id: int) -> list[WorklistStation]:
        """Get all configured stations for a clinic."""
        result = await self.db.execute(
            select(WorklistStation)
            .where(
                WorklistStation.clinic_id == clinic_id,
                WorklistStation.is_active == True,
            )
            .order_by(WorklistStation.station_name)
        )
        return list(result.scalars().all())

    async def create_station(
        self,
        clinic_id: int,
        ae_title: str,
        station_name: str,
        modality: ImagingModality,
        location: Optional[str] = None,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
    ) -> WorklistStation:
        """Create or update a worklist station configuration."""
        # Check for existing
        result = await self.db.execute(
            select(WorklistStation).where(WorklistStation.ae_title == ae_title)
        )
        station = result.scalar_one_or_none()

        if station:
            # Update existing
            station.station_name = station_name
            station.modality = modality
            station.location = location
            station.manufacturer = manufacturer
            station.model = model
            station.is_active = True
        else:
            # Create new
            station = WorklistStation(
                clinic_id=clinic_id,
                ae_title=ae_title,
                station_name=station_name,
                modality=modality,
                location=location,
                manufacturer=manufacturer,
                model=model,
            )
            self.db.add(station)

        await self.db.commit()
        await self.db.refresh(station)
        return station
