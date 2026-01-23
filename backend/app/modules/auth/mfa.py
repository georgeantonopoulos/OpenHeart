"""
MFA (Multi-Factor Authentication) Service for OpenHeart Cyprus.

Implements TOTP (Time-based One-Time Password) per RFC 6238.
Compatible with Google Authenticator, Authy, and other TOTP apps.
"""

import secrets
from base64 import b32encode
from typing import Optional

import pyotp
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_pii, encrypt_pii
from app.modules.auth.service import AuthEvent, log_auth_event
from app.modules.clinic.models import User


# MFA constants
TOTP_ISSUER = "OpenHeart Cyprus"
BACKUP_CODE_COUNT = 10
BACKUP_CODE_LENGTH = 8


class MFAService:
    """
    Service for managing Multi-Factor Authentication.

    Uses TOTP (RFC 6238) with 30-second windows.
    Backup codes provide recovery if device is lost.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def setup_mfa(
        self,
        user_id: int,
        ip_address: str = "",
        user_agent: str = "",
    ) -> dict:
        """
        Initialize MFA setup for a user.

        Generates a new TOTP secret and returns provisioning info.
        MFA is NOT enabled until verify_and_enable is called.

        Args:
            user_id: User ID
            ip_address: Client IP for audit
            user_agent: Client user agent for audit

        Returns:
            dict with:
                - secret: Base32-encoded secret (for manual entry)
                - provisioning_uri: URI for QR code
                - qr_code_data: Data URL for QR code image
        """
        # Get user
        result = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        # Generate new secret (160 bits = 32 base32 characters)
        secret_bytes = secrets.token_bytes(20)
        secret = b32encode(secret_bytes).decode("utf-8")

        # Store encrypted secret (not enabled yet)
        encrypted_secret = encrypt_pii(secret)
        await self.db.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(mfa_secret=encrypted_secret)
        )
        await self.db.commit()

        # Generate provisioning URI for QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name=TOTP_ISSUER,
        )

        # Log setup initiation
        await log_auth_event(
            event=AuthEvent.MFA_SETUP_INITIATED,
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user_id,
        )

        return {
            "secret": secret,  # For manual entry
            "provisioning_uri": provisioning_uri,  # For QR code
        }

    async def verify_and_enable(
        self,
        user_id: int,
        code: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> dict:
        """
        Verify TOTP code and enable MFA if correct.

        This completes the MFA setup process.

        Args:
            user_id: User ID
            code: 6-digit TOTP code from authenticator app
            ip_address: Client IP for audit
            user_agent: Client user agent for audit

        Returns:
            dict with backup_codes if successful

        Raises:
            ValueError: If code is invalid or MFA secret not set
        """
        # Get user
        result = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        if not user.mfa_secret:
            raise ValueError("MFA setup not initiated. Call setup_mfa first.")

        # Decrypt and verify
        secret = decrypt_pii(user.mfa_secret)
        totp = pyotp.TOTP(secret)

        if not totp.verify(code, valid_window=1):
            await log_auth_event(
                event=AuthEvent.MFA_SETUP_FAILED,
                email=user.email,
                ip_address=ip_address,
                user_agent=user_agent,
                user_id=user_id,
                details="Invalid verification code",
            )
            raise ValueError("Invalid verification code")

        # Generate backup codes
        backup_codes = [
            secrets.token_hex(BACKUP_CODE_LENGTH // 2).upper()
            for _ in range(BACKUP_CODE_COUNT)
        ]

        # Encrypt backup codes for storage
        encrypted_codes = [encrypt_pii(code) for code in backup_codes]

        # Enable MFA
        await self.db.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(
                mfa_enabled=True,
                mfa_backup_codes=encrypted_codes,
            )
        )
        await self.db.commit()

        # Log successful setup
        await log_auth_event(
            event=AuthEvent.MFA_ENABLED,
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user_id,
        )

        return {
            "enabled": True,
            "backup_codes": backup_codes,  # Show once, then never again
            "message": "MFA enabled successfully. Save your backup codes securely.",
        }

    async def verify_code(
        self,
        user_id: int,
        code: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> bool:
        """
        Verify a TOTP code during login.

        Also accepts backup codes for recovery.

        Args:
            user_id: User ID
            code: 6-digit TOTP code or backup code
            ip_address: Client IP for audit
            user_agent: Client user agent for audit

        Returns:
            True if code is valid
        """
        # Get user
        result = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user or not user.mfa_enabled or not user.mfa_secret:
            return False

        # Try TOTP first
        secret = decrypt_pii(user.mfa_secret)
        totp = pyotp.TOTP(secret)

        if totp.verify(code, valid_window=1):
            await log_auth_event(
                event=AuthEvent.MFA_VERIFIED,
                email=user.email,
                ip_address=ip_address,
                user_agent=user_agent,
                user_id=user_id,
            )
            return True

        # Try backup codes
        if user.mfa_backup_codes:
            normalized_code = code.upper().replace("-", "")
            for i, encrypted_backup in enumerate(user.mfa_backup_codes):
                decrypted = decrypt_pii(encrypted_backup)
                if secrets.compare_digest(decrypted, normalized_code):
                    # Remove used backup code
                    remaining_codes = user.mfa_backup_codes.copy()
                    remaining_codes.pop(i)

                    await self.db.execute(
                        update(User)
                        .where(User.user_id == user_id)
                        .values(mfa_backup_codes=remaining_codes)
                    )
                    await self.db.commit()

                    await log_auth_event(
                        event=AuthEvent.MFA_BACKUP_USED,
                        email=user.email,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        user_id=user_id,
                        details=f"{len(remaining_codes)} backup codes remaining",
                    )
                    return True

        # All verification failed
        await log_auth_event(
            event=AuthEvent.MFA_FAILED,
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user_id,
        )
        return False

    async def disable_mfa(
        self,
        user_id: int,
        password: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> bool:
        """
        Disable MFA for a user (requires password confirmation).

        Args:
            user_id: User ID
            password: Current password for verification
            ip_address: Client IP for audit
            user_agent: Client user agent for audit

        Returns:
            True if MFA was disabled

        Raises:
            ValueError: If password is incorrect
        """
        from app.core.security import verify_password

        # Get user
        result = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        # Verify password (supports both Argon2id and legacy bcrypt)
        if not verify_password(password, user.password_hash):
            await log_auth_event(
                event=AuthEvent.MFA_DISABLE_FAILED,
                email=user.email,
                ip_address=ip_address,
                user_agent=user_agent,
                user_id=user_id,
                details="Invalid password",
            )
            raise ValueError("Invalid password")

        # Disable MFA
        await self.db.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(
                mfa_enabled=False,
                mfa_secret=None,
                mfa_backup_codes=None,
            )
        )
        await self.db.commit()

        await log_auth_event(
            event=AuthEvent.MFA_DISABLED,
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user_id,
        )

        return True

    async def regenerate_backup_codes(
        self,
        user_id: int,
        code: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> list[str]:
        """
        Generate new backup codes (invalidates old ones).

        Requires current TOTP code for verification.

        Args:
            user_id: User ID
            code: Current TOTP code for verification
            ip_address: Client IP for audit
            user_agent: Client user agent for audit

        Returns:
            List of new backup codes

        Raises:
            ValueError: If verification fails
        """
        # Verify current TOTP code first
        result = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user or not user.mfa_enabled or not user.mfa_secret:
            raise ValueError("MFA not enabled")

        secret = decrypt_pii(user.mfa_secret)
        totp = pyotp.TOTP(secret)

        if not totp.verify(code, valid_window=1):
            raise ValueError("Invalid verification code")

        # Generate new backup codes
        backup_codes = [
            secrets.token_hex(BACKUP_CODE_LENGTH // 2).upper()
            for _ in range(BACKUP_CODE_COUNT)
        ]

        # Encrypt and save
        encrypted_codes = [encrypt_pii(code) for code in backup_codes]

        await self.db.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(mfa_backup_codes=encrypted_codes)
        )
        await self.db.commit()

        await log_auth_event(
            event=AuthEvent.MFA_BACKUP_REGENERATED,
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user_id,
        )

        return backup_codes

    async def get_mfa_status(self, user_id: int) -> dict:
        """
        Get MFA status for a user.

        Args:
            user_id: User ID

        Returns:
            dict with enabled status and backup code count
        """
        result = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        backup_count = len(user.mfa_backup_codes) if user.mfa_backup_codes else 0

        return {
            "enabled": user.mfa_enabled,
            "backup_codes_remaining": backup_count,
            "has_secret": user.mfa_secret is not None,
        }
