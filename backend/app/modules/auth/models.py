"""
Authentication-related SQLAlchemy Models.

Includes invitations and password reset tokens.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InvitationStatus(str, Enum):
    """Status of a user invitation."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class UserInvitation(Base):
    """
    User invitation for onboarding new users.

    Invitations are created by admins and allow new users to
    self-register with a predefined role at a specific clinic.
    """

    __tablename__ = "user_invitations"

    invitation_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Invitation token (secure random string)
    token: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="Secure invitation token",
    )

    # Invitee details
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Email address to invite",
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Role assignment
    clinic_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("clinics.clinic_id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Role to assign upon acceptance",
    )

    # Optional fields for professionals
    title: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    specialty: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    license_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Invitation tracking
    status: Mapped[str] = mapped_column(
        String(20),
        default=InvitationStatus.PENDING.value,
        nullable=False,
    )
    invited_by_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        comment="Admin who created the invitation",
    )

    # Expiration
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Token expiration time",
    )

    # Acceptance tracking
    accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    accepted_user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        comment="User created from this invitation",
    )

    # Personal message from inviter
    message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional personal message to invitee",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    clinic = relationship("Clinic", foreign_keys=[clinic_id])
    invited_by = relationship("User", foreign_keys=[invited_by_user_id])
    accepted_user = relationship("User", foreign_keys=[accepted_user_id])

    __table_args__ = (
        Index("idx_invitations_email", "email"),
        Index("idx_invitations_status", "status"),
        Index("idx_invitations_clinic", "clinic_id"),
        {"comment": "User invitations for onboarding"},
    )


class PasswordResetToken(Base):
    """
    Password reset token for forgotten password flow.

    Tokens are single-use and expire after a short period.
    """

    __tablename__ = "password_reset_tokens"

    token_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Token
    token: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="Secure reset token",
    )

    # User
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    # Status
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Expiration
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Request tracking
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_reset_tokens_user", "user_id"),
        {"comment": "Password reset tokens"},
    )
