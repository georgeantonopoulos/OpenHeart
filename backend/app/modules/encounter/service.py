"""
Encounter Service Layer.

Business logic for clinical encounters and vitals,
including RLS enforcement and audit logging.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_pii
from app.db.session import set_tenant_context
from app.modules.encounter.models import Encounter, EncounterStatus, Vitals
from app.modules.encounter.schemas import (
    EncounterComplete,
    EncounterCreate,
    EncounterResponse,
    EncounterStart,
    EncounterUpdate,
    VitalsCreate,
    VitalsResponse,
)
from app.modules.patient.models import Patient, PatientPII


class EncounterService:
    """Service class for encounter operations."""

    def __init__(self, session: AsyncSession, clinic_id: int, user_id: int):
        self.session = session
        self.clinic_id = clinic_id
        self.user_id = user_id

    async def _set_tenant(self) -> None:
        """Set RLS tenant context."""
        await set_tenant_context(self.session, self.clinic_id)

    async def create_encounter(self, data: EncounterCreate) -> Encounter:
        """Create a new encounter."""
        await self._set_tenant()

        # Verify patient exists and belongs to clinic
        patient = await self.session.get(Patient, data.patient_id)
        if not patient or patient.clinic_id != self.clinic_id:
            raise ValueError("Patient not found")

        encounter = Encounter(
            patient_id=data.patient_id,
            clinic_id=self.clinic_id,
            attending_physician_id=self.user_id,
            encounter_type=data.encounter_type.value,
            status=EncounterStatus.PLANNED.value,
            scheduled_start=data.scheduled_start,
            chief_complaint=data.chief_complaint,
            visit_reason_code=data.visit_reason_code,
            location=data.location,
            referral_source=data.referral_source,
            is_follow_up=data.is_follow_up,
            follow_up_to_encounter_id=data.follow_up_to_encounter_id,
            gesy_referral_id=data.gesy_referral_id,
        )

        self.session.add(encounter)
        await self.session.commit()
        await self.session.refresh(encounter)

        return encounter

    async def get_encounter(self, encounter_id: int) -> Optional[Encounter]:
        """Get encounter by ID."""
        await self._set_tenant()

        result = await self.session.execute(
            select(Encounter).where(
                Encounter.encounter_id == encounter_id,
                Encounter.clinic_id == self.clinic_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_encounters(
        self,
        patient_id: Optional[int] = None,
        status: Optional[str] = None,
        encounter_type: Optional[str] = None,
        attending_physician_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        billing_status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Encounter], int]:
        """Get encounters with filtering and pagination."""
        await self._set_tenant()

        query = select(Encounter).where(Encounter.clinic_id == self.clinic_id)

        # Apply filters
        if patient_id:
            query = query.where(Encounter.patient_id == patient_id)
        if status:
            query = query.where(Encounter.status == status)
        if encounter_type:
            query = query.where(Encounter.encounter_type == encounter_type)
        if attending_physician_id:
            query = query.where(Encounter.attending_physician_id == attending_physician_id)
        if date_from:
            query = query.where(Encounter.scheduled_start >= date_from)
        if date_to:
            query = query.where(Encounter.scheduled_start <= date_to)
        if billing_status:
            query = query.where(Encounter.billing_status == billing_status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and order
        query = query.order_by(Encounter.scheduled_start.desc().nulls_last())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.session.execute(query)
        encounters = list(result.scalars().all())

        return encounters, total

    async def get_today_encounters(self) -> list[Encounter]:
        """Get today's encounters for the current user."""
        await self._set_tenant()

        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)

        query = (
            select(Encounter)
            .where(
                Encounter.clinic_id == self.clinic_id,
                Encounter.attending_physician_id == self.user_id,
                Encounter.scheduled_start >= today_start,
                Encounter.scheduled_start <= today_end,
            )
            .order_by(Encounter.scheduled_start)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_encounter(
        self, encounter_id: int, data: EncounterUpdate
    ) -> Optional[Encounter]:
        """Update an encounter."""
        await self._set_tenant()

        encounter = await self.get_encounter(encounter_id)
        if not encounter:
            return None

        # Update fields
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "status" and value:
                setattr(encounter, field, value.value if hasattr(value, "value") else value)
            elif field == "encounter_type" and value:
                setattr(encounter, field, value.value if hasattr(value, "value") else value)
            elif field == "billing_status" and value:
                setattr(encounter, field, value.value if hasattr(value, "value") else value)
            elif field == "discharge_summary" and value:
                setattr(encounter, field, value.model_dump() if hasattr(value, "model_dump") else value)
            elif field == "diagnoses" and value:
                setattr(encounter, field, [d.model_dump() if hasattr(d, "model_dump") else d for d in value])
            elif value is not None:
                setattr(encounter, field, value)

        await self.session.commit()
        await self.session.refresh(encounter)

        return encounter

    async def start_encounter(
        self, encounter_id: int, data: EncounterStart
    ) -> Optional[Encounter]:
        """Start an encounter (set to in_progress)."""
        await self._set_tenant()

        encounter = await self.get_encounter(encounter_id)
        if not encounter:
            return None

        encounter.status = EncounterStatus.IN_PROGRESS.value
        encounter.actual_start = datetime.now()

        if data.chief_complaint:
            encounter.chief_complaint = data.chief_complaint
        if data.location:
            encounter.location = data.location

        await self.session.commit()
        await self.session.refresh(encounter)

        return encounter

    async def complete_encounter(
        self, encounter_id: int, data: EncounterComplete
    ) -> Optional[Encounter]:
        """Complete an encounter."""
        await self._set_tenant()

        encounter = await self.get_encounter(encounter_id)
        if not encounter:
            return None

        encounter.status = EncounterStatus.COMPLETED.value
        encounter.actual_end = datetime.now()

        if data.discharge_summary:
            encounter.discharge_summary = data.discharge_summary.model_dump()
        if data.diagnoses:
            encounter.diagnoses = [d.model_dump() for d in data.diagnoses]

        await self.session.commit()
        await self.session.refresh(encounter)

        return encounter

    async def cancel_encounter(
        self, encounter_id: int, reason: Optional[str] = None
    ) -> Optional[Encounter]:
        """Cancel an encounter."""
        await self._set_tenant()

        encounter = await self.get_encounter(encounter_id)
        if not encounter:
            return None

        encounter.status = EncounterStatus.CANCELLED.value
        if reason:
            encounter.chief_complaint = f"[CANCELLED] {reason}"

        await self.session.commit()
        await self.session.refresh(encounter)

        return encounter

    async def mark_no_show(self, encounter_id: int) -> Optional[Encounter]:
        """Mark encounter as no-show."""
        await self._set_tenant()

        encounter = await self.get_encounter(encounter_id)
        if not encounter:
            return None

        encounter.status = EncounterStatus.NO_SHOW.value

        await self.session.commit()
        await self.session.refresh(encounter)

        return encounter

    # ========================================================================
    # Vitals Operations
    # ========================================================================

    async def record_vitals(
        self, encounter_id: int, data: VitalsCreate
    ) -> Optional[Vitals]:
        """Record vitals for an encounter."""
        await self._set_tenant()

        encounter = await self.get_encounter(encounter_id)
        if not encounter:
            return None

        # Calculate BMI if height and weight provided
        bmi = None
        if data.height and data.weight:
            height_m = data.height / 100
            bmi = round(data.weight / (height_m * height_m), 1)

        vitals = Vitals(
            encounter_id=encounter_id,
            patient_id=encounter.patient_id,
            heart_rate=data.heart_rate,
            systolic_bp=data.systolic_bp,
            diastolic_bp=data.diastolic_bp,
            respiratory_rate=data.respiratory_rate,
            oxygen_saturation=data.oxygen_saturation,
            temperature=data.temperature,
            weight=data.weight,
            height=data.height,
            bmi=bmi,
            position=data.position,
            recorded_by=self.user_id,
        )

        self.session.add(vitals)
        await self.session.commit()
        await self.session.refresh(vitals)

        return vitals

    async def get_encounter_vitals(self, encounter_id: int) -> list[Vitals]:
        """Get all vitals for an encounter."""
        await self._set_tenant()

        # Verify encounter belongs to clinic
        encounter = await self.get_encounter(encounter_id)
        if not encounter:
            return []

        result = await self.session.execute(
            select(Vitals)
            .where(Vitals.encounter_id == encounter_id)
            .order_by(Vitals.recorded_at.desc())
        )
        return list(result.scalars().all())

    async def get_patient_vitals_trend(
        self, patient_id: int, vital_type: str, limit: int = 20
    ) -> list[Vitals]:
        """Get vitals trend for a patient."""
        await self._set_tenant()

        # Verify patient belongs to clinic
        patient = await self.session.get(Patient, patient_id)
        if not patient or patient.clinic_id != self.clinic_id:
            return []

        result = await self.session.execute(
            select(Vitals)
            .where(Vitals.patient_id == patient_id)
            .order_by(Vitals.recorded_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_vitals(self, patient_id: int) -> Optional[Vitals]:
        """Get most recent vitals for a patient."""
        await self._set_tenant()

        result = await self.session.execute(
            select(Vitals)
            .where(Vitals.patient_id == patient_id)
            .order_by(Vitals.recorded_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ========================================================================
    # Response Builders
    # ========================================================================

    async def build_encounter_response(
        self, encounter: Encounter, include_patient: bool = True
    ) -> EncounterResponse:
        """Build encounter response with optional patient info."""
        response = EncounterResponse(
            encounter_id=encounter.encounter_id,
            patient_id=encounter.patient_id,
            clinic_id=encounter.clinic_id,
            encounter_type=encounter.encounter_type,
            status=encounter.status,
            scheduled_start=encounter.scheduled_start,
            actual_start=encounter.actual_start,
            actual_end=encounter.actual_end,
            duration_minutes=encounter.duration_minutes,
            chief_complaint=encounter.chief_complaint,
            visit_reason_code=encounter.visit_reason_code,
            location=encounter.location,
            attending_physician_id=encounter.attending_physician_id,
            referral_source=encounter.referral_source,
            is_follow_up=encounter.is_follow_up,
            follow_up_to_encounter_id=encounter.follow_up_to_encounter_id,
            gesy_referral_id=encounter.gesy_referral_id,
            discharge_summary=encounter.discharge_summary,
            diagnoses=encounter.diagnoses,
            billing_status=encounter.billing_status,
            gesy_claim_id=encounter.gesy_claim_id,
            created_at=encounter.created_at,
            updated_at=encounter.updated_at,
        )

        # Add patient info
        if include_patient:
            patient = await self.session.get(Patient, encounter.patient_id)
            if patient:
                response.patient_mrn = patient.mrn

                # Get PII for name
                pii_result = await self.session.execute(
                    select(PatientPII).where(PatientPII.patient_id == patient.patient_id)
                )
                pii = pii_result.scalar_one_or_none()
                if pii:
                    first_name = decrypt_pii(pii.first_name_encrypted)
                    last_name = decrypt_pii(pii.last_name_encrypted)
                    response.patient_name = f"{first_name} {last_name}"

        return response

    async def build_vitals_response(self, vitals: Vitals) -> VitalsResponse:
        """Build vitals response."""
        return VitalsResponse(
            vital_id=vitals.vital_id,
            encounter_id=vitals.encounter_id,
            patient_id=vitals.patient_id,
            heart_rate=vitals.heart_rate,
            systolic_bp=vitals.systolic_bp,
            diastolic_bp=vitals.diastolic_bp,
            respiratory_rate=vitals.respiratory_rate,
            oxygen_saturation=vitals.oxygen_saturation,
            temperature=vitals.temperature,
            weight=vitals.weight,
            height=vitals.height,
            bmi=vitals.bmi,
            recorded_at=vitals.recorded_at,
            recorded_by=vitals.recorded_by,
            position=vitals.position,
        )
