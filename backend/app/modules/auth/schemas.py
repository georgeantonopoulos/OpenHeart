"""
Authentication request/response schemas.

Pydantic models for login, token refresh, invitations, and user info endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    """Login request with email and password."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (minimum 8 characters)")


class UserInfo(BaseModel):
    """Basic user information returned after login."""

    user_id: int
    email: str
    full_name: str
    role: str
    clinic_id: int
    clinic_name: str

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Successful login response with tokens and user info."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiry in seconds")
    user: UserInfo


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str = Field(..., description="Valid refresh token")


class RefreshResponse(BaseModel):
    """Token refresh response with new access token."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiry in seconds")


class AuthError(BaseModel):
    """Authentication error response."""

    detail: str
    error_code: str | None = None


# =============================================================================
# Invitation Schemas
# =============================================================================


class InvitationCreateRequest(BaseModel):
    """Request to create a new user invitation."""

    email: EmailStr = Field(..., description="Email address to invite")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., description="Role to assign (e.g., cardiologist, nurse)")
    clinic_id: int = Field(..., description="Clinic to assign user to")

    # Optional professional fields
    title: Optional[str] = Field(None, max_length=50, description="Dr., Prof., etc.")
    specialty: Optional[str] = Field(None, max_length=100)
    license_number: Optional[str] = Field(None, max_length=50)

    # Optional personal message
    message: Optional[str] = Field(
        None,
        max_length=500,
        description="Personal message to include in invitation email",
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is one of the allowed values."""
        allowed_roles = {"admin", "cardiologist", "nurse", "receptionist", "lab_tech", "auditor"}
        if v.lower() not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v.lower()


class InvitationResponse(BaseModel):
    """Response containing invitation details."""

    invitation_id: int
    email: str
    first_name: str
    last_name: str
    role: str
    clinic_id: int
    clinic_name: str
    status: str
    invited_by_name: Optional[str] = None
    expires_at: datetime
    created_at: datetime
    accepted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InvitationListResponse(BaseModel):
    """Paginated list of invitations."""

    invitations: list[InvitationResponse]
    total: int
    page: int
    per_page: int


class InvitationValidateResponse(BaseModel):
    """Response when validating an invitation token (public)."""

    valid: bool
    email: str
    first_name: str
    last_name: str
    role: str
    clinic_name: str
    title: Optional[str] = None
    specialty: Optional[str] = None
    message: Optional[str] = None
    expires_at: datetime


class InvitationAcceptRequest(BaseModel):
    """Request to accept an invitation and create user account."""

    password: str = Field(
        ...,
        min_length=12,
        description="Password (minimum 12 characters, must include uppercase, lowercase, number, and special character)",
    )
    confirm_password: str = Field(..., description="Password confirmation")
    gdpr_consent: bool = Field(
        ...,
        description="User consents to GDPR data processing",
    )
    terms_accepted: bool = Field(
        ...,
        description="User accepts terms of service",
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements."""
        import re

        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Validate passwords match."""
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

    @field_validator("gdpr_consent", "terms_accepted")
    @classmethod
    def must_be_true(cls, v: bool) -> bool:
        """Validate consent fields are True."""
        if not v:
            raise ValueError("This field must be accepted")
        return v


class InvitationAcceptResponse(BaseModel):
    """Response after successfully accepting an invitation."""

    user_id: int
    email: str
    full_name: str
    role: str
    clinic_id: int
    clinic_name: str
    message: str = "Account created successfully. Please log in."


# =============================================================================
# Password Reset Schemas
# =============================================================================


class PasswordResetRequestSchema(BaseModel):
    """Request to initiate password reset."""

    email: EmailStr = Field(..., description="Email address for password reset")


class PasswordResetConfirmSchema(BaseModel):
    """Request to complete password reset with token."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=12)
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements."""
        import re

        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Validate passwords match."""
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class PasswordChangeSchema(BaseModel):
    """Request to change password while logged in."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=12)
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements."""
        import re

        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Validate passwords match."""
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class PasswordStrength(BaseModel):
    """Password strength analysis result."""

    score: int = Field(..., ge=0, le=6, description="Strength score (0-6)")
    strength: str = Field(..., description="Strength level: weak, moderate, strong")
    feedback: list[str] = Field(
        default_factory=list, description="Suggestions for improvement"
    )
    meets_requirements: bool = Field(
        ..., description="Whether password meets all requirements"
    )


# =============================================================================
# MFA Schemas
# =============================================================================


class MFASetupResponse(BaseModel):
    """Response with MFA setup information."""

    secret: str = Field(..., description="Base32-encoded TOTP secret for manual entry")
    provisioning_uri: str = Field(..., description="URI for QR code generation")


class MFAVerifyRequest(BaseModel):
    """Request to verify TOTP code."""

    code: str = Field(
        ...,
        min_length=6,
        max_length=8,
        description="6-digit TOTP code or 8-character backup code",
    )


class MFAEnableResponse(BaseModel):
    """Response after enabling MFA."""

    enabled: bool = True
    backup_codes: list[str] = Field(
        ..., description="One-time backup codes (save securely!)"
    )
    message: str = "MFA enabled successfully. Save your backup codes securely."


class MFAStatusResponse(BaseModel):
    """MFA status for current user."""

    enabled: bool
    backup_codes_remaining: int
    has_secret: bool


class MFADisableRequest(BaseModel):
    """Request to disable MFA."""

    password: str = Field(..., description="Current password for verification")
