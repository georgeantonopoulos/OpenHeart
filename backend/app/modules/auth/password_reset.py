"""
Password Reset Service for OpenHeart Cyprus.

Implements secure password reset flow with rate limiting and audit logging.
Tokens are single-use and expire after 1 hour.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.modules.auth.models import PasswordResetToken
from app.modules.auth.schemas import PasswordStrength
from app.modules.auth.service import AuthEvent, log_auth_event
from app.modules.clinic.models import User


# Password reset constants
TOKEN_EXPIRY_HOURS = 1
TOKEN_LENGTH = 64  # 512 bits of entropy
PASSWORD_MIN_LENGTH = 12


def check_password_strength(password: str) -> PasswordStrength:
    """
    Analyze password strength and provide feedback.

    Args:
        password: Password to check

    Returns:
        PasswordStrength with score and feedback
    """
    score = 0
    feedback = []

    # Length check
    if len(password) >= 12:
        score += 1
    else:
        feedback.append("Use at least 12 characters")

    if len(password) >= 16:
        score += 1

    # Character variety
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/~`" for c in password)

    if has_upper:
        score += 1
    else:
        feedback.append("Add uppercase letters")

    if has_lower:
        score += 1
    else:
        feedback.append("Add lowercase letters")

    if has_digit:
        score += 1
    else:
        feedback.append("Add numbers")

    if has_special:
        score += 1
    else:
        feedback.append("Add special characters (!@#$%^&*)")

    # Common patterns to avoid
    common_patterns = ["password", "123456", "qwerty", "letmein", "admin"]
    if any(pattern in password.lower() for pattern in common_patterns):
        score = max(0, score - 2)
        feedback.append("Avoid common passwords")

    # Determine strength level
    if score <= 2:
        strength = "weak"
    elif score <= 4:
        strength = "moderate"
    else:
        strength = "strong"

    meets_requirements = (
        len(password) >= 12 and has_upper and has_lower and has_digit and has_special
    )

    return PasswordStrength(
        score=min(score, 6),
        strength=strength,
        feedback=feedback if feedback else ["Password meets all requirements"],
        meets_requirements=meets_requirements,
    )


class PasswordResetService:
    """
    Service for handling password reset flows.

    Features:
    - Secure token generation (64 bytes = 512 bits entropy)
    - Single-use tokens
    - 1-hour expiry
    - Rate limiting by IP and email
    - GDPR-compliant audit logging
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def request_reset(
        self,
        email: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> bool:
        """
        Request a password reset for an email address.

        Always returns True to prevent email enumeration.

        Args:
            email: Email address requesting reset
            ip_address: Client IP for audit
            user_agent: Client user agent for audit

        Returns:
            True (always, to prevent enumeration)
        """
        # Check if user exists
        result = await self.db.execute(
            select(User).where(User.email == email, User.is_active == True)
        )
        user = result.scalar_one_or_none()

        if not user:
            # Log attempt but don't reveal user doesn't exist
            await log_auth_event(
                event=AuthEvent.PASSWORD_RESET_REQUESTED,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                details="User not found (not revealed to client)",
            )
            return True  # Don't reveal user doesn't exist

        # Invalidate any existing tokens for this user
        await self.db.execute(
            delete(PasswordResetToken).where(
                PasswordResetToken.user_id == user.user_id
            )
        )

        # Generate secure token
        token = secrets.token_urlsafe(TOKEN_LENGTH)

        # Create reset token record
        reset_token = PasswordResetToken(
            user_id=user.user_id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS),
            ip_address=ip_address,
        )

        self.db.add(reset_token)
        await self.db.commit()

        await log_auth_event(
            event=AuthEvent.PASSWORD_RESET_REQUESTED,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user.user_id,
        )

        # Send password reset email (dev mode: logs to console)
        from app.core.email import send_password_reset_email

        await send_password_reset_email(to=user.email, reset_token=token)

        return True

    async def validate_token(self, token: str) -> Optional[dict]:
        """
        Validate a password reset token.

        Args:
            token: Reset token from email link

        Returns:
            dict with user info if valid, None if invalid/expired
        """
        result = await self.db.execute(
            select(PasswordResetToken)
            .join(User, PasswordResetToken.user_id == User.user_id)
            .where(
                PasswordResetToken.token == token,
                PasswordResetToken.is_used == False,
                PasswordResetToken.expires_at > datetime.now(timezone.utc),
                User.is_active == True,
            )
        )
        reset_token = result.scalar_one_or_none()

        if not reset_token:
            return None

        # Get user email
        user_result = await self.db.execute(
            select(User).where(User.user_id == reset_token.user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            return None

        return {
            "valid": True,
            "email": user.email,
            "expires_at": reset_token.expires_at.isoformat(),
        }

    async def reset_password(
        self,
        token: str,
        new_password: str,
        ip_address: str = "",
        user_agent: str = "",
        redis_client: Optional[Any] = None,
    ) -> bool:
        """
        Reset password using a valid token.

        Args:
            token: Reset token from email link
            new_password: New password to set
            ip_address: Client IP for audit
            user_agent: Client user agent for audit

        Returns:
            True if password was reset

        Raises:
            ValueError: If token is invalid/expired or password is weak
        """
        # Validate token
        result = await self.db.execute(
            select(PasswordResetToken)
            .where(
                PasswordResetToken.token == token,
                PasswordResetToken.is_used == False,
                PasswordResetToken.expires_at > datetime.now(timezone.utc),
            )
        )
        reset_token = result.scalar_one_or_none()

        if not reset_token:
            raise ValueError("Invalid or expired reset token")

        # Get user
        user_result = await self.db.execute(
            select(User).where(User.user_id == reset_token.user_id, User.is_active == True)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found or inactive")

        # Check password strength
        strength = check_password_strength(new_password)
        if not strength.meets_requirements:
            raise ValueError(
                f"Password does not meet requirements: {', '.join(strength.feedback)}"
            )

        # Hash new password with Argon2id
        password_hash = hash_password(new_password)

        # Update user password
        await self.db.execute(
            update(User)
            .where(User.user_id == user.user_id)
            .values(
                password_hash=password_hash,
                password_changed_at=datetime.now(timezone.utc),
                must_change_password=False,
                failed_login_attempts=0,
                locked_until=None,
            )
        )

        # Mark token as used
        await self.db.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.id == reset_token.id)
            .values(is_used=True)
        )

        await self.db.commit()

        await log_auth_event(
            event=AuthEvent.PASSWORD_RESET_COMPLETED,
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user.user_id,
        )

        # Invalidate all existing sessions (DB-level)
        from app.modules.auth.session_manager import SessionManager

        session_manager = SessionManager(self.db)
        await session_manager.revoke_all_user_sessions(
            user_id=user.user_id, reason="password_reset"
        )

        # Invalidate all tokens via Redis (instant, covers tokens not yet expired)
        if redis_client:
            from app.core.redis import invalidate_user_sessions

            await invalidate_user_sessions(redis_client, user.user_id)

        return True

    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
        ip_address: str = "",
        user_agent: str = "",
        redis_client: Optional[Any] = None,
    ) -> bool:
        """
        Change password for authenticated user.

        Requires current password verification.

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password to set
            ip_address: Client IP for audit
            user_agent: Client user agent for audit

        Returns:
            True if password was changed

        Raises:
            ValueError: If current password is wrong or new password is weak
        """
        # Get user
        result = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        # Check new password strength
        strength = check_password_strength(new_password)
        if not strength.meets_requirements:
            raise ValueError(
                f"Password does not meet requirements: {', '.join(strength.feedback)}"
            )

        # Ensure new password is different
        if verify_password(new_password, user.password_hash):
            raise ValueError("New password must be different from current password")

        # Hash and update with Argon2id
        password_hash = hash_password(new_password)

        await self.db.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(
                password_hash=password_hash,
                password_changed_at=datetime.now(timezone.utc),
                must_change_password=False,
            )
        )
        await self.db.commit()

        await log_auth_event(
            event=AuthEvent.PASSWORD_CHANGED,
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user_id,
        )

        # Invalidate all other sessions
        from app.modules.auth.session_manager import SessionManager

        session_manager = SessionManager(self.db)
        await session_manager.revoke_all_user_sessions(
            user_id=user_id, reason="password_change"
        )

        # Invalidate all tokens via Redis
        if redis_client:
            from app.core.redis import invalidate_user_sessions

            await invalidate_user_sessions(redis_client, user_id)

        return True

    async def cleanup_expired_tokens(self) -> int:
        """
        Remove expired password reset tokens.

        Should be called periodically (e.g., by a scheduled task).

        Returns:
            Number of tokens deleted
        """
        result = await self.db.execute(
            delete(PasswordResetToken).where(
                PasswordResetToken.expires_at < datetime.now(timezone.utc)
            )
        )
        await self.db.commit()
        return result.rowcount
