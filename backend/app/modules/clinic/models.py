"""
Clinic and User SQLAlchemy Models.

Implements multi-tenant isolation with RLS support,
user authentication, and role-based access control.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from typing import List


class Role(str, Enum):
    """User roles in the system."""

    ADMIN = "admin"
    CARDIOLOGIST = "cardiologist"
    NURSE = "nurse"
    RECEPTIONIST = "receptionist"
    AUDITOR = "auditor"
    LAB_TECH = "lab_tech"


class Clinic(Base):
    """
    Clinic entity for multi-tenant isolation.

    All patient data is scoped to a clinic via RLS policies.
    """

    __tablename__ = "clinics"

    clinic_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        comment="Short unique code for the clinic",
    )

    # Contact information
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Gesy registration
    gesy_provider_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        unique=True,
        comment="Gesy healthcare provider ID",
    )

    # Operating hours (JSON)
    operating_hours: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Weekly operating hours",
    )

    # Settings
    settings: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Clinic-specific configuration",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    users: Mapped["List[UserClinicRole]"] = relationship(
        "UserClinicRole",
        back_populates="clinic",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_clinics_gesy", "gesy_provider_id"),
        {"comment": "Healthcare clinics for multi-tenant isolation"},
    )


class User(Base):
    """
    User account for authentication.

    Users can belong to multiple clinics with different roles.
    """

    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Authentication
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Dr., Prof., etc.",
    )
    specialty: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Medical specialty",
    )
    license_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Medical license number",
    )

    # MFA
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="TOTP secret (encrypted)",
    )
    mfa_backup_codes: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Encrypted backup codes",
    )
    webauthn_credentials: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="WebAuthn credential IDs",
    )

    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Password management
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Login tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    clinic_roles: Mapped["List[UserClinicRole]"] = relationship(
        "UserClinicRole",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        {"comment": "User accounts with MFA support"},
    )

    @property
    def full_name(self) -> str:
        """Get user's full name with title if available."""
        parts = []
        if self.title:
            parts.append(self.title)
        parts.append(self.first_name)
        parts.append(self.last_name)
        return " ".join(parts)


class UserClinicRole(Base):
    """
    Many-to-many relationship between users and clinics with role.

    A user can have different roles at different clinics.
    """

    __tablename__ = "user_clinic_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    clinic_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("clinics.clinic_id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Role at this specific clinic",
    )

    # Additional permissions (JSON array of permission strings)
    additional_permissions: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Extra permissions beyond role defaults",
    )

    # Status
    is_primary_clinic: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="User's primary/default clinic",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="clinic_roles")
    clinic: Mapped["Clinic"] = relationship("Clinic", back_populates="users")

    __table_args__ = (
        UniqueConstraint("user_id", "clinic_id", name="uq_user_clinic"),
        Index("idx_user_clinic_roles_user", "user_id"),
        Index("idx_user_clinic_roles_clinic", "clinic_id"),
        {"comment": "User-clinic role assignments"},
    )
