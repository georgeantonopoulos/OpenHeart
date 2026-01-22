"""
Server-Side Session Manager for OpenHeart Cyprus.

Tracks active user sessions for security monitoring and session revocation.
Each JWT is linked to a session record for immediate invalidation capability.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, delete, select, update
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.config import settings
from app.db.base import Base


class UserSession(Base):
    """
    Server-side session tracking for security and audit.

    Each JWT token is linked to a session for:
    - Viewing active sessions
    - Immediate revocation (logout everywhere)
    - Security monitoring (unusual activity)
    """

    __tablename__ = "user_sessions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Token identification (hash for security)
    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        comment="SHA-256 hash of JWT for lookup",
    )

    # Client information
    ip_address: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
        comment="Client IP (supports IPv6)",
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Browser/device user agent",
    )
    device_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Friendly device name",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Revocation
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_reason: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="logout, password_change, admin_revoke, etc.",
    )


def hash_token(token: str) -> str:
    """Create SHA-256 hash of JWT for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def parse_user_agent(user_agent: str) -> str:
    """Extract friendly device name from user agent string."""
    if not user_agent:
        return "Unknown Device"

    ua_lower = user_agent.lower()

    # Mobile devices
    if "iphone" in ua_lower:
        return "iPhone"
    if "ipad" in ua_lower:
        return "iPad"
    if "android" in ua_lower:
        if "mobile" in ua_lower:
            return "Android Phone"
        return "Android Tablet"

    # Desktop browsers
    if "chrome" in ua_lower and "edge" not in ua_lower:
        if "windows" in ua_lower:
            return "Chrome on Windows"
        if "mac" in ua_lower:
            return "Chrome on Mac"
        if "linux" in ua_lower:
            return "Chrome on Linux"
        return "Chrome"

    if "firefox" in ua_lower:
        if "windows" in ua_lower:
            return "Firefox on Windows"
        if "mac" in ua_lower:
            return "Firefox on Mac"
        return "Firefox"

    if "safari" in ua_lower and "chrome" not in ua_lower:
        return "Safari on Mac"

    if "edge" in ua_lower:
        return "Edge"

    return "Unknown Device"


class SessionManager:
    """
    Manages server-side session tracking.

    Provides session creation, validation, revocation, and listing.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        user_id: int,
        token: str,
        ip_address: str,
        user_agent: str = "",
        expires_in_minutes: int = 0,
    ) -> UserSession:
        """
        Create a new session record for a JWT.

        Args:
            user_id: User ID
            token: JWT access token
            ip_address: Client IP address
            user_agent: Client user agent string
            expires_in_minutes: Token expiry in minutes (default from settings)

        Returns:
            Created UserSession
        """
        if expires_in_minutes <= 0:
            expires_in_minutes = settings.jwt_expiry_minutes

        session = UserSession(
            user_id=user_id,
            token_hash=hash_token(token),
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            device_name=parse_user_agent(user_agent),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes),
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def validate_session(self, token: str) -> bool:
        """
        Check if a session is valid (not revoked or expired).

        Args:
            token: JWT access token

        Returns:
            True if session is valid
        """
        token_hash = hash_token(token)

        result = await self.db.execute(
            select(UserSession).where(
                UserSession.token_hash == token_hash,
                UserSession.revoked == False,
                UserSession.expires_at > datetime.now(timezone.utc),
            )
        )
        session = result.scalar_one_or_none()

        if session:
            # Update last activity
            await self.db.execute(
                update(UserSession)
                .where(UserSession.id == session.id)
                .values(last_activity=datetime.now(timezone.utc))
            )
            await self.db.commit()
            return True

        return False

    async def revoke_session(
        self,
        session_id: UUID,
        reason: str = "logout",
    ) -> bool:
        """
        Revoke a specific session.

        Args:
            session_id: Session UUID
            reason: Revocation reason

        Returns:
            True if session was revoked
        """
        result = await self.db.execute(
            update(UserSession)
            .where(UserSession.id == session_id, UserSession.revoked == False)
            .values(
                revoked=True,
                revoked_at=datetime.now(timezone.utc),
                revoked_reason=reason,
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def revoke_session_by_token(
        self,
        token: str,
        reason: str = "logout",
    ) -> bool:
        """
        Revoke a session by its token.

        Args:
            token: JWT access token
            reason: Revocation reason

        Returns:
            True if session was revoked
        """
        token_hash = hash_token(token)

        result = await self.db.execute(
            update(UserSession)
            .where(UserSession.token_hash == token_hash, UserSession.revoked == False)
            .values(
                revoked=True,
                revoked_at=datetime.now(timezone.utc),
                revoked_reason=reason,
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def revoke_all_user_sessions(
        self,
        user_id: int,
        reason: str = "password_change",
        exclude_token: Optional[str] = None,
    ) -> int:
        """
        Revoke all sessions for a user.

        Useful for password changes or forced logout.

        Args:
            user_id: User ID
            reason: Revocation reason
            exclude_token: Optional token to keep active (current session)

        Returns:
            Number of sessions revoked
        """
        query = (
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked == False)
            .values(
                revoked=True,
                revoked_at=datetime.now(timezone.utc),
                revoked_reason=reason,
            )
        )

        if exclude_token:
            exclude_hash = hash_token(exclude_token)
            query = query.where(UserSession.token_hash != exclude_hash)

        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount

    async def list_user_sessions(
        self,
        user_id: int,
        include_revoked: bool = False,
    ) -> list[dict]:
        """
        List all sessions for a user.

        Args:
            user_id: User ID
            include_revoked: Whether to include revoked sessions

        Returns:
            List of session dictionaries
        """
        query = (
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .order_by(UserSession.last_activity.desc())
        )

        if not include_revoked:
            query = query.where(
                UserSession.revoked == False,
                UserSession.expires_at > datetime.now(timezone.utc),
            )

        result = await self.db.execute(query)
        sessions = result.scalars().all()

        return [
            {
                "id": str(session.id),
                "device_name": session.device_name,
                "ip_address": session.ip_address,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "is_current": False,  # Set by caller if needed
            }
            for session in sessions
        ]

    async def cleanup_expired_sessions(self) -> int:
        """
        Remove expired and old revoked sessions.

        Should be called periodically (e.g., by a scheduled task).

        Returns:
            Number of sessions deleted
        """
        # Delete sessions expired more than 7 days ago
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)

        result = await self.db.execute(
            delete(UserSession).where(
                (UserSession.expires_at < cutoff)
                | (
                    (UserSession.revoked == True)
                    & (UserSession.revoked_at < cutoff)
                )
            )
        )
        await self.db.commit()
        return result.rowcount

    async def get_session_by_token(self, token: str) -> Optional[UserSession]:
        """
        Get session record by token.

        Args:
            token: JWT access token

        Returns:
            UserSession if found
        """
        token_hash = hash_token(token)

        result = await self.db.execute(
            select(UserSession).where(UserSession.token_hash == token_hash)
        )
        return result.scalar_one_or_none()
