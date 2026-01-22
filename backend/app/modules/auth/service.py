"""
Authentication service layer for OpenHeart Cyprus.

Contains business logic for user authentication, session management,
and audit logging for GDPR compliance.
"""

import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.modules.clinic.models import Clinic, User, UserClinicRole

logger = logging.getLogger(__name__)


class AuthEvent(str, Enum):
    """Authentication event types for audit logging."""

    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    ACCOUNT_LOCKOUT = "ACCOUNT_LOCKOUT"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    LOGOUT = "LOGOUT"


# Lockout policy configuration
LOCKOUT_THRESHOLD = 5  # Failed attempts before lockout
LOCKOUT_DURATION_MINUTES = 15  # Lockout duration


async def log_auth_event(
    event: AuthEvent,
    email: str,
    ip_address: str,
    user_agent: str,
    user_id: Optional[int] = None,
    clinic_id: Optional[int] = None,
    details: Optional[str] = None,
) -> None:
    """
    Log authentication event for GDPR/Cyprus Law 125(I)/2018 compliance.

    Args:
        event: Type of authentication event
        email: Email address attempted
        ip_address: Client IP address
        user_agent: Client user agent string
        user_id: User ID if known
        clinic_id: Clinic ID if known
        details: Additional details about the event
    """
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event.value,
        "email": email,
        "user_id": user_id,
        "clinic_id": clinic_id,
        "ip_address": ip_address,
        "user_agent": user_agent[:500] if user_agent else None,
        "details": details,
    }

    # Log level based on event type
    if event == AuthEvent.LOGIN_SUCCESS:
        logger.info(f"AUTH_AUDIT: {event.value} for {email} from {ip_address}")
    elif event == AuthEvent.LOGIN_FAILURE:
        logger.warning(f"AUTH_AUDIT: {event.value} for {email} from {ip_address} - {details}")
    elif event == AuthEvent.ACCOUNT_LOCKOUT:
        logger.warning(f"AUTH_AUDIT: {event.value} for {email} from {ip_address}")
    else:
        logger.info(f"AUTH_AUDIT: {event.value} for {email} from {ip_address}")

    # TODO: Insert into security_audit table asynchronously
    # await db.execute(
    #     insert(SecurityAudit).values(**log_entry)
    # )


class AuthService:
    """
    Authentication service handling user login and session management.

    Implements GDPR-compliant authentication with:
    - Account lockout after failed attempts
    - Audit logging for all auth events
    - MFA bypass in development mode
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: str,
        user_agent: str,
    ) -> Optional[User]:
        """
        Authenticate user by email and password.

        Args:
            email: User's email address
            password: Plain text password to verify
            ip_address: Client IP for audit logging
            user_agent: Client user agent for audit logging

        Returns:
            User if authentication succeeds, None otherwise

        Side Effects:
            - Increments failed_login_attempts on failure
            - Locks account after LOCKOUT_THRESHOLD failures
            - Resets failed_login_attempts on success
            - Logs all auth events to audit trail
        """
        # Query user with clinic roles eagerly loaded
        query = (
            select(User)
            .where(User.email == email)
            .options(
                selectinload(User.clinic_roles).selectinload(UserClinicRole.clinic)
            )
        )
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            # Log failure but don't reveal user doesn't exist
            await log_auth_event(
                event=AuthEvent.LOGIN_FAILURE,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                details="User not found",
            )
            return None

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            await log_auth_event(
                event=AuthEvent.LOGIN_FAILURE,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                user_id=user.user_id,
                details=f"Account locked until {user.locked_until.isoformat()}",
            )
            return None

        # Check if account is active
        if not user.is_active:
            await log_auth_event(
                event=AuthEvent.LOGIN_FAILURE,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                user_id=user.user_id,
                details="Account inactive",
            )
            return None

        # Verify password
        if not verify_password(password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1

            # Check for lockout threshold
            if user.failed_login_attempts >= LOCKOUT_THRESHOLD:
                user.locked_until = datetime.now(timezone.utc) + timedelta(
                    minutes=LOCKOUT_DURATION_MINUTES
                )
                await self.db.commit()

                await log_auth_event(
                    event=AuthEvent.ACCOUNT_LOCKOUT,
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    user_id=user.user_id,
                    details=f"Locked for {LOCKOUT_DURATION_MINUTES} minutes after {LOCKOUT_THRESHOLD} failed attempts",
                )
                return None

            await self.db.commit()

            await log_auth_event(
                event=AuthEvent.LOGIN_FAILURE,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                user_id=user.user_id,
                details=f"Invalid password (attempt {user.failed_login_attempts}/{LOCKOUT_THRESHOLD})",
            )
            return None

        # SUCCESS - Reset failed attempts and update last login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.commit()

        # Re-query user with relationships after commit
        # (commit expires the eagerly loaded relationships)
        user = await self.get_user_by_id(user.user_id)
        if not user:
            return None

        # Get primary clinic for audit logging
        clinic_role = self.get_primary_clinic_role(user)

        await log_auth_event(
            event=AuthEvent.LOGIN_SUCCESS,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user.user_id,
            clinic_id=clinic_role.clinic_id if clinic_role else None,
        )

        return user

    def get_primary_clinic_role(self, user: User) -> Optional[UserClinicRole]:
        """
        Get user's primary clinic and role assignment.

        Args:
            user: User object with clinic_roles relationship loaded

        Returns:
            Primary UserClinicRole or first active role as fallback
        """
        if not user.clinic_roles:
            return None

        # First, try to find role marked as primary
        for role in user.clinic_roles:
            if role.is_primary_clinic and role.is_active:
                return role

        # Fallback: return first active role
        for role in user.clinic_roles:
            if role.is_active:
                return role

        return None

    def create_tokens(
        self,
        user: User,
        clinic_role: UserClinicRole,
    ) -> tuple[str, str]:
        """
        Create access and refresh tokens for authenticated user.

        Args:
            user: Authenticated user
            clinic_role: User's clinic role assignment

        Returns:
            Tuple of (access_token, refresh_token)

        Note:
            In development mode, mfa_verified is set to True to bypass
            MFA requirements. Production requires MFA setup in Phase 3.
        """
        # In development, bypass MFA requirement
        # In production, this will be False until MFA is verified
        mfa_verified = (
            settings.environment == "development" or not user.mfa_enabled
        )

        access_token = create_access_token(
            user_id=user.user_id,
            email=user.email,
            clinic_id=clinic_role.clinic_id,
            role=clinic_role.role,
            mfa_verified=mfa_verified,
        )

        refresh_token = create_refresh_token(user_id=user.user_id)

        return access_token, refresh_token

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID with clinic roles loaded.

        Args:
            user_id: User's database ID

        Returns:
            User if found, None otherwise
        """
        query = (
            select(User)
            .where(User.user_id == user_id)
            .options(
                selectinload(User.clinic_roles).selectinload(UserClinicRole.clinic)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
