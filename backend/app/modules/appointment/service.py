"""Appointment Service Layer.

Business logic for appointment scheduling including:
- Conflict detection (overlapping provider appointments)
- Duration warnings
- Encounter handover (start encounter from appointment)
- Available slot finder
"""

from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import set_tenant_context
from app.modules.appointment.models import (
    Appointment,
    AppointmentStatus,
    EXPECTED_DURATIONS,
)
from app.modules.appointment.schemas import (
    AppointmentCreate,
    AppointmentUpdate,
    ConflictInfo,
    check_duration_warning,
)
from app.modules.encounter.models import Encounter, EncounterStatus


class AppointmentService:
    """Service class for appointment operations."""

    def __init__(self, session: AsyncSession, clinic_id: int, user_id: int):
        self.session = session
        self.clinic_id = clinic_id
        self.user_id = user_id

    async def _set_tenant(self) -> None:
        """Set RLS tenant context."""
        await set_tenant_context(self.session, self.clinic_id)

    async def create_appointment(
        self, data: AppointmentCreate
    ) -> Appointment:
        """Create a new appointment with conflict check."""
        await self._set_tenant()

        end_time = data.start_time + timedelta(minutes=data.duration_minutes)
        expected = EXPECTED_DURATIONS.get(data.appointment_type.value, 30)

        # Check for conflicts
        conflicts = await self.check_conflicts(
            data.provider_id, data.start_time, end_time
        )
        if conflicts:
            raise ValueError(
                f"Scheduling conflict: provider already has an appointment "
                f"from {conflicts[0].start_time} to {conflicts[0].end_time}"
            )

        appointment = Appointment(
            clinic_id=self.clinic_id,
            patient_id=data.patient_id,
            provider_id=data.provider_id,
            start_time=data.start_time,
            end_time=end_time,
            duration_minutes=data.duration_minutes,
            expected_duration_minutes=expected,
            appointment_type=data.appointment_type.value,
            status=AppointmentStatus.SCHEDULED.value,
            reason=data.reason,
            notes=data.notes,
            location=data.location,
            gesy_referral_id=data.gesy_referral_id,
            created_by=self.user_id,
        )

        self.session.add(appointment)
        await self.session.flush()
        await self.session.refresh(appointment)
        return appointment

    async def get_appointment(self, appointment_id: int) -> Optional[Appointment]:
        """Get appointment by ID."""
        await self._set_tenant()
        return await self.session.get(Appointment, appointment_id)

    async def list_appointments(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        provider_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> list[Appointment]:
        """List appointments with optional filters."""
        await self._set_tenant()

        stmt = select(Appointment).where(
            Appointment.clinic_id == self.clinic_id
        )

        if from_date:
            stmt = stmt.where(Appointment.start_time >= datetime.combine(from_date, datetime.min.time()))
        if to_date:
            stmt = stmt.where(Appointment.start_time < datetime.combine(to_date + timedelta(days=1), datetime.min.time()))
        if provider_id:
            stmt = stmt.where(Appointment.provider_id == provider_id)
        if patient_id:
            stmt = stmt.where(Appointment.patient_id == patient_id)
        if status:
            stmt = stmt.where(Appointment.status == status)

        stmt = stmt.order_by(Appointment.start_time)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_appointment(
        self, appointment_id: int, data: AppointmentUpdate
    ) -> Optional[Appointment]:
        """Update/reschedule an appointment."""
        await self._set_tenant()

        appointment = await self.session.get(Appointment, appointment_id)
        if not appointment or appointment.clinic_id != self.clinic_id:
            return None

        if appointment.status in (
            AppointmentStatus.COMPLETED.value,
            AppointmentStatus.CANCELLED.value,
        ):
            raise ValueError("Cannot update a completed or cancelled appointment")

        # If rescheduling, check conflicts
        new_start = data.start_time or appointment.start_time
        new_duration = data.duration_minutes or appointment.duration_minutes
        new_end = new_start + timedelta(minutes=new_duration)
        new_provider = data.provider_id or appointment.provider_id

        if data.start_time or data.duration_minutes or data.provider_id:
            conflicts = await self.check_conflicts(
                new_provider, new_start, new_end, exclude_id=appointment_id
            )
            if conflicts:
                raise ValueError(
                    f"Scheduling conflict: provider already has an appointment "
                    f"from {conflicts[0].start_time} to {conflicts[0].end_time}"
                )

        # Apply updates
        if data.start_time:
            appointment.start_time = new_start
            appointment.end_time = new_end
        if data.duration_minutes:
            appointment.duration_minutes = new_duration
            appointment.end_time = appointment.start_time + timedelta(minutes=new_duration)
        if data.appointment_type:
            appointment.appointment_type = data.appointment_type.value
            appointment.expected_duration_minutes = EXPECTED_DURATIONS.get(
                data.appointment_type.value, 30
            )
        if data.reason is not None:
            appointment.reason = data.reason
        if data.notes is not None:
            appointment.notes = data.notes
        if data.location is not None:
            appointment.location = data.location
        if data.provider_id:
            appointment.provider_id = data.provider_id

        appointment.updated_at = func.now()
        await self.session.flush()
        await self.session.refresh(appointment)
        return appointment

    async def cancel_appointment(
        self,
        appointment_id: int,
        reason: Optional[str] = None,
    ) -> Optional[Appointment]:
        """Cancel an appointment."""
        await self._set_tenant()

        appointment = await self.session.get(Appointment, appointment_id)
        if not appointment or appointment.clinic_id != self.clinic_id:
            return None

        if appointment.status in (
            AppointmentStatus.COMPLETED.value,
            AppointmentStatus.CANCELLED.value,
        ):
            raise ValueError("Cannot cancel a completed or already cancelled appointment")

        appointment.status = AppointmentStatus.CANCELLED.value
        appointment.cancelled_at = func.now()
        appointment.cancelled_by = self.user_id
        appointment.cancellation_reason = reason
        appointment.updated_at = func.now()

        await self.session.flush()
        await self.session.refresh(appointment)
        return appointment

    async def check_in(self, appointment_id: int) -> Optional[Appointment]:
        """Check in a patient for their appointment."""
        await self._set_tenant()

        appointment = await self.session.get(Appointment, appointment_id)
        if not appointment or appointment.clinic_id != self.clinic_id:
            return None

        if appointment.status not in (
            AppointmentStatus.SCHEDULED.value,
            AppointmentStatus.CONFIRMED.value,
        ):
            raise ValueError(
                f"Cannot check in: appointment status is '{appointment.status}'"
            )

        appointment.status = AppointmentStatus.CHECKED_IN.value
        appointment.updated_at = func.now()

        await self.session.flush()
        await self.session.refresh(appointment)
        return appointment

    async def start_encounter_from_appointment(
        self, appointment_id: int
    ) -> Encounter:
        """Create an encounter from an appointment and link them.

        This is the appointment-to-encounter handover:
        1. Creates a new encounter with appointment data pre-populated
        2. Links appointment to the new encounter
        3. Updates appointment status to IN_PROGRESS
        """
        await self._set_tenant()

        appointment = await self.session.get(Appointment, appointment_id)
        if not appointment or appointment.clinic_id != self.clinic_id:
            raise ValueError("Appointment not found")

        if appointment.encounter_id:
            raise ValueError("Encounter already started for this appointment")

        if appointment.status not in (
            AppointmentStatus.SCHEDULED.value,
            AppointmentStatus.CONFIRMED.value,
            AppointmentStatus.CHECKED_IN.value,
        ):
            raise ValueError(
                f"Cannot start encounter: appointment status is '{appointment.status}'"
            )

        # Create encounter from appointment data
        encounter = Encounter(
            patient_id=appointment.patient_id,
            clinic_id=self.clinic_id,
            attending_physician_id=appointment.provider_id,
            encounter_type="outpatient",
            status=EncounterStatus.IN_PROGRESS.value,
            scheduled_start=appointment.start_time,
            actual_start=func.now(),
            chief_complaint=appointment.reason,
            location=appointment.location,
            gesy_referral_id=appointment.gesy_referral_id,
        )
        self.session.add(encounter)
        await self.session.flush()

        # Link appointment to encounter
        appointment.encounter_id = encounter.encounter_id
        appointment.status = AppointmentStatus.IN_PROGRESS.value
        appointment.updated_at = func.now()

        await self.session.flush()
        await self.session.refresh(encounter)
        return encounter

    async def check_conflicts(
        self,
        provider_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_id: Optional[int] = None,
    ) -> list[ConflictInfo]:
        """Check for overlapping appointments for a provider."""
        stmt = select(Appointment).where(
            Appointment.provider_id == provider_id,
            Appointment.status.not_in([
                AppointmentStatus.CANCELLED.value,
                AppointmentStatus.NO_SHOW.value,
            ]),
            # Overlap: existing.start < new.end AND existing.end > new.start
            Appointment.start_time < end_time,
            Appointment.end_time > start_time,
        )

        if exclude_id:
            stmt = stmt.where(Appointment.appointment_id != exclude_id)

        result = await self.session.execute(stmt)
        appointments = result.scalars().all()

        return [
            ConflictInfo(
                conflicting_appointment_id=a.appointment_id,
                patient_id=a.patient_id,
                start_time=a.start_time,
                end_time=a.end_time,
                appointment_type=a.appointment_type,
            )
            for a in appointments
        ]

    async def get_available_slots(
        self,
        provider_id: int,
        target_date: date,
        duration_minutes: int = 30,
        start_hour: int = 8,
        end_hour: int = 17,
    ) -> list[dict]:
        """Find available time slots for a provider on a given date."""
        await self._set_tenant()

        from_dt = datetime.combine(target_date, datetime.min.time().replace(hour=start_hour))
        to_dt = datetime.combine(target_date, datetime.min.time().replace(hour=end_hour))

        # Get existing appointments for the day
        stmt = (
            select(Appointment)
            .where(
                Appointment.provider_id == provider_id,
                Appointment.start_time >= from_dt,
                Appointment.start_time < to_dt,
                Appointment.status.not_in([
                    AppointmentStatus.CANCELLED.value,
                    AppointmentStatus.NO_SHOW.value,
                ]),
            )
            .order_by(Appointment.start_time)
        )
        result = await self.session.execute(stmt)
        existing = list(result.scalars().all())

        # Find gaps
        slots = []
        current = from_dt

        for appt in existing:
            if current + timedelta(minutes=duration_minutes) <= appt.start_time:
                slots.append({
                    "start_time": current.isoformat(),
                    "end_time": (current + timedelta(minutes=duration_minutes)).isoformat(),
                    "duration_minutes": duration_minutes,
                })
            current = max(current, appt.end_time)

        # Check remaining time after last appointment
        if current + timedelta(minutes=duration_minutes) <= to_dt:
            slots.append({
                "start_time": current.isoformat(),
                "end_time": (current + timedelta(minutes=duration_minutes)).isoformat(),
                "duration_minutes": duration_minutes,
            })

        return slots
