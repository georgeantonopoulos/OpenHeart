"""
Development seed script for OpenHeart Cyprus.

Creates test users and clinic for development environment.
Uses idempotent "get or create" pattern - safe to run multiple times.

NEVER run in production - checks environment before executing.
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.modules.clinic.models import Clinic, User, UserClinicRole

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
    for user_data in DEV_USERS:
        user = await get_or_create_user(db, user_data)
        await get_or_create_user_clinic_role(db, user, clinic, user_data["role"])

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
