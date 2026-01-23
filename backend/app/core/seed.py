"""
Development seed script for OpenHeart Cyprus.

Creates test users and clinic for development environment.
Uses idempotent "get or create" pattern - safe to run multiple times.

NEVER run in production - checks environment before executing.
"""

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.encryption import encrypt_pii
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.modules.appointment.models import Appointment, AppointmentType, AppointmentStatus, EXPECTED_DURATIONS
from app.modules.clinic.models import Clinic, User, UserClinicRole
from app.modules.encounter.models import Encounter  # noqa: F401 - needed for FK resolution
from app.modules.patient.models import Patient, PatientPII

logger = logging.getLogger(__name__)


# Development clinic configuration
DEV_CLINIC = {
    "name": "OpenHeart Development Clinic",
    "code": "OHDEV",
    "address": "123 Development Street, Nicosia, Cyprus",
    "phone": "+357 22 000000",
    "email": "dev@openheart.local",
}

# Development test accounts
# Using @example.com domain per RFC 2606 (reserved for documentation/testing)
DEV_USERS = [
    {
        "email": "admin@openheart.example.com",
        "password": "DevAdmin123!",
        "first_name": "System",
        "last_name": "Administrator",
        "title": None,
        "specialty": None,
        "license_number": None,
        "role": "admin",
        "is_superuser": True,
    },
    {
        "email": "cardiologist@openheart.example.com",
        "password": "TestUser123!",
        "first_name": "Andreas",
        "last_name": "Kyprianou",
        "title": "Dr.",
        "specialty": "Interventional Cardiology",
        "license_number": "CYP-CARD-001",
        "role": "cardiologist",
        "is_superuser": False,
    },
    {
        "email": "nurse@openheart.example.com",
        "password": "TestUser123!",
        "first_name": "Maria",
        "last_name": "Papadopoulou",
        "title": None,
        "specialty": None,
        "license_number": "CYP-NURSE-001",
        "role": "nurse",
        "is_superuser": False,
    },
    {
        "email": "reception@openheart.example.com",
        "password": "TestUser123!",
        "first_name": "Elena",
        "last_name": "Christodoulou",
        "title": None,
        "specialty": None,
        "license_number": None,
        "role": "receptionist",
        "is_superuser": False,
    },
]


# Development patient records (Cypriot Greek names)
DEV_PATIENTS = [
    {
        "mrn": "1-2026-00001",
        "first_name": "Maria",
        "last_name": "Papadopoulou",
        "birth_date": date(1958, 3, 15),
        "gender": "female",
        "gesy_beneficiary_id": "GHS-2024-10001",
    },
    {
        "mrn": "1-2026-00002",
        "first_name": "Andreas",
        "last_name": "Christodoulou",
        "birth_date": date(1971, 7, 22),
        "gender": "male",
        "gesy_beneficiary_id": "GHS-2024-10002",
    },
    {
        "mrn": "1-2026-00003",
        "first_name": "Elena",
        "last_name": "Georgiou",
        "birth_date": date(1980, 11, 5),
        "gender": "female",
        "gesy_beneficiary_id": None,
    },
    {
        "mrn": "1-2026-00004",
        "first_name": "Kostas",
        "last_name": "Nikolaou",
        "birth_date": date(1953, 1, 30),
        "gender": "male",
        "gesy_beneficiary_id": "GHS-2024-10004",
    },
    {
        "mrn": "1-2026-00005",
        "first_name": "Sophia",
        "last_name": "Antoniou",
        "birth_date": date(1967, 9, 12),
        "gender": "female",
        "gesy_beneficiary_id": "GHS-2024-10005",
    },
]

# Appointments seeded for "today" relative to run time
DEV_APPOINTMENTS = [
    {
        "patient_index": 0,  # Maria Papadopoulou
        "hour": 9, "minute": 0,
        "appointment_type": AppointmentType.FOLLOW_UP,
        "reason": "Post-PCI follow-up",
        "gesy_referral_id": "GESY-REF-2026-001",
    },
    {
        "patient_index": 1,  # Andreas Christodoulou
        "hour": 9, "minute": 30,
        "appointment_type": AppointmentType.ECHO,
        "reason": "Annual echocardiogram",
        "gesy_referral_id": "GESY-REF-2026-002",
    },
    {
        "patient_index": 2,  # Elena Georgiou
        "hour": 10, "minute": 15,
        "appointment_type": AppointmentType.CONSULTATION,
        "reason": "New patient - chest pain evaluation",
        "gesy_referral_id": None,
    },
    {
        "patient_index": 3,  # Kostas Nikolaou
        "hour": 11, "minute": 0,
        "appointment_type": AppointmentType.ECG,
        "reason": "ICD check - 6 month",
        "gesy_referral_id": "GESY-REF-2026-004",
    },
    {
        "patient_index": 4,  # Sophia Antoniou
        "hour": 11, "minute": 45,
        "appointment_type": AppointmentType.STRESS_TEST,
        "reason": "Exercise stress test - pre-operative",
        "gesy_referral_id": "GESY-REF-2026-005",
    },
]


async def get_or_create_clinic(db: AsyncSession) -> Clinic:
    """
    Get existing clinic by code or create new one.

    Returns:
        Clinic object (existing or newly created)
    """
    # Check if clinic exists
    result = await db.execute(
        select(Clinic).where(Clinic.code == DEV_CLINIC["code"])
    )
    clinic = result.scalar_one_or_none()

    if clinic:
        logger.info(f"Clinic already exists: {clinic.name} (ID: {clinic.clinic_id})")
        return clinic

    # Create new clinic
    clinic = Clinic(
        name=DEV_CLINIC["name"],
        code=DEV_CLINIC["code"],
        address=DEV_CLINIC["address"],
        phone=DEV_CLINIC["phone"],
        email=DEV_CLINIC["email"],
        is_active=True,
    )
    db.add(clinic)
    await db.flush()

    logger.info(f"Created clinic: {clinic.name} (ID: {clinic.clinic_id})")
    return clinic


async def get_or_create_user(
    db: AsyncSession,
    user_data: dict,
) -> User:
    """
    Get existing user by email or create new one.

    Args:
        db: Database session
        user_data: User configuration dictionary

    Returns:
        User object (existing or newly created)
    """
    # Check if user exists
    result = await db.execute(
        select(User).where(User.email == user_data["email"])
    )
    user = result.scalar_one_or_none()

    if user:
        logger.info(f"User already exists: {user.email} (ID: {user.user_id})")
        return user

    # Create new user
    user = User(
        email=user_data["email"],
        password_hash=hash_password(user_data["password"]),
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        title=user_data.get("title"),
        specialty=user_data.get("specialty"),
        license_number=user_data.get("license_number"),
        is_active=True,
        is_superuser=user_data.get("is_superuser", False),
        email_verified=True,
        mfa_enabled=False,  # Disabled in development
        password_changed_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()

    logger.info(f"Created user: {user.email} (ID: {user.user_id})")
    return user


async def get_or_create_user_clinic_role(
    db: AsyncSession,
    user: User,
    clinic: Clinic,
    role: str,
) -> UserClinicRole:
    """
    Get existing user-clinic role assignment or create new one.

    Args:
        db: Database session
        user: User object
        clinic: Clinic object
        role: Role string (admin, cardiologist, etc.)

    Returns:
        UserClinicRole object (existing or newly created)
    """
    # Check if assignment exists
    result = await db.execute(
        select(UserClinicRole).where(
            UserClinicRole.user_id == user.user_id,
            UserClinicRole.clinic_id == clinic.clinic_id,
        )
    )
    user_role = result.scalar_one_or_none()

    if user_role:
        logger.info(f"Role assignment exists: {user.email} -> {clinic.name} ({role})")
        return user_role

    # Create new assignment
    user_role = UserClinicRole(
        user_id=user.user_id,
        clinic_id=clinic.clinic_id,
        role=role,
        is_primary_clinic=True,
        is_active=True,
    )
    db.add(user_role)
    await db.flush()

    logger.info(f"Created role: {user.email} -> {clinic.name} ({role})")
    return user_role


async def get_or_create_patient(
    db: AsyncSession,
    patient_data: dict,
    clinic_id: int,
) -> Patient:
    """Get existing patient by MRN or create with encrypted PII."""
    result = await db.execute(
        select(Patient).where(
            Patient.clinic_id == clinic_id,
            Patient.mrn == patient_data["mrn"],
        )
    )
    patient = result.scalar_one_or_none()

    if patient:
        logger.info(f"Patient already exists: {patient_data['mrn']} (ID: {patient.patient_id})")
        return patient

    patient = Patient(
        clinic_id=clinic_id,
        mrn=patient_data["mrn"],
        birth_date=patient_data["birth_date"],
        gender=patient_data["gender"],
        status="active",
        gesy_beneficiary_id=patient_data.get("gesy_beneficiary_id"),
    )
    db.add(patient)
    await db.flush()

    pii = PatientPII(
        patient_id=patient.patient_id,
        first_name_encrypted=encrypt_pii(patient_data["first_name"]),
        last_name_encrypted=encrypt_pii(patient_data["last_name"]),
    )
    db.add(pii)
    await db.flush()

    logger.info(f"Created patient: {patient_data['first_name']} {patient_data['last_name']} (MRN: {patient_data['mrn']})")
    return patient


async def seed_appointments(
    db: AsyncSession,
    patients: list[Patient],
    clinic_id: int,
    provider_id: int,
) -> None:
    """Seed today's appointments for development (idempotent by checking existing count)."""
    today = datetime.now(timezone.utc).date()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    today_end = today_start + timedelta(days=1)

    result = await db.execute(
        select(Appointment).where(
            Appointment.clinic_id == clinic_id,
            Appointment.start_time >= today_start,
            Appointment.start_time < today_end,
        )
    )
    existing = result.scalars().all()
    if existing:
        logger.info(f"Appointments already exist for today ({len(existing)} found), skipping seed")
        return

    for appt_data in DEV_APPOINTMENTS:
        patient = patients[appt_data["patient_index"]]
        start_time = datetime.combine(today, datetime.min.time()).replace(
            hour=appt_data["hour"],
            minute=appt_data["minute"],
            tzinfo=timezone.utc,
        )
        duration = EXPECTED_DURATIONS.get(appt_data["appointment_type"].value, 30)
        end_time = start_time + timedelta(minutes=duration)

        appointment = Appointment(
            clinic_id=clinic_id,
            patient_id=patient.patient_id,
            provider_id=provider_id,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration,
            expected_duration_minutes=duration,
            appointment_type=appt_data["appointment_type"].value,
            status=AppointmentStatus.SCHEDULED.value,
            reason=appt_data.get("reason"),
            gesy_referral_id=appt_data.get("gesy_referral_id"),
            created_by=provider_id,
        )
        db.add(appointment)

    await db.flush()
    logger.info(f"Created {len(DEV_APPOINTMENTS)} appointments for today")


async def seed_development_data(db: AsyncSession) -> None:
    """
    Seed development database with test users and clinic.

    Uses idempotent "get or create" pattern for all entities.
    Safe to run multiple times without errors or duplicates.
    """
    logger.info("=" * 60)
    logger.info("Starting development seed...")
    logger.info("=" * 60)

    # Create or get clinic
    clinic = await get_or_create_clinic(db)

    # Create or get users and assign roles
    users = {}
    for user_data in DEV_USERS:
        user = await get_or_create_user(db, user_data)
        await get_or_create_user_clinic_role(db, user, clinic, user_data["role"])
        users[user_data["role"]] = user

    # Create or get patients
    patients = []
    for patient_data in DEV_PATIENTS:
        patient = await get_or_create_patient(db, patient_data, clinic.clinic_id)
        patients.append(patient)

    # Seed today's appointments (cardiologist as provider)
    cardiologist = users.get("cardiologist")
    if cardiologist and patients:
        await seed_appointments(db, patients, clinic.clinic_id, cardiologist.user_id)

    # Commit all changes
    await db.commit()

    logger.info("=" * 60)
    logger.info("Development seed completed successfully!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Test Accounts:")
    logger.info("-" * 40)
    for user_data in DEV_USERS:
        logger.info(f"  {user_data['email']} / {user_data['password']} ({user_data['role']})")
    logger.info("")


async def run_seed() -> None:
    """
    Run seed script with environment check.

    Raises:
        RuntimeError: If not in development environment
    """
    if settings.environment != "development":
        raise RuntimeError(
            f"Seed script can only run in development environment! "
            f"Current: {settings.environment}"
        )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    async with AsyncSessionLocal() as db:
        await seed_development_data(db)


def main() -> None:
    """CLI entry point for seed script."""
    try:
        asyncio.run(run_seed())
    except RuntimeError as e:
        logger.error(str(e))
        exit(1)
    except Exception as e:
        logger.error(f"Seed failed: {e}")
        raise


if __name__ == "__main__":
    main()
