"""Pydantic schemas for the appointments module."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.modules.appointment.models import AppointmentStatus, AppointmentType, EXPECTED_DURATIONS


class AppointmentCreate(BaseModel):
    """Schema for creating a new appointment."""

    patient_id: int
    provider_id: int
    start_time: datetime
    duration_minutes: int
    appointment_type: AppointmentType
    reason: Optional[str] = None
    notes: Optional[str] = None
    location: Optional[str] = None
    gesy_referral_id: Optional[str] = None

    @field_validator("duration_minutes")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v < 5 or v > 480:
            raise ValueError("Duration must be between 5 and 480 minutes")
        return v


class AppointmentUpdate(BaseModel):
    """Schema for updating/rescheduling an appointment."""

    start_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    appointment_type: Optional[AppointmentType] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    location: Optional[str] = None
    provider_id: Optional[int] = None


class AppointmentResponse(BaseModel):
    """Schema for appointment API responses."""

    appointment_id: int
    clinic_id: int
    patient_id: int
    provider_id: int
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    expected_duration_minutes: Optional[int] = None
    appointment_type: str
    status: str
    reason: Optional[str] = None
    notes: Optional[str] = None
    location: Optional[str] = None
    gesy_referral_id: Optional[str] = None
    encounter_id: Optional[int] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    duration_warning: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConflictInfo(BaseModel):
    """Information about a scheduling conflict."""

    conflicting_appointment_id: int
    patient_id: int
    start_time: datetime
    end_time: datetime
    appointment_type: str


class AvailableSlot(BaseModel):
    """A time slot available for booking."""

    start_time: datetime
    end_time: datetime
    duration_minutes: int


def check_duration_warning(appointment_type: str, scheduled_minutes: int) -> Optional[str]:
    """Return warning if scheduled duration seems too short."""
    expected = EXPECTED_DURATIONS.get(appointment_type, 30)
    if scheduled_minutes < int(expected * 0.75):
        return (
            f"{appointment_type.replace('_', ' ').title()} appointments typically "
            f"require {expected} minutes, but only {scheduled_minutes} scheduled"
        )
    return None
