"""
Authentication request/response schemas.

Pydantic models for login, token refresh, and user info endpoints.
"""

from pydantic import BaseModel, EmailStr, Field


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
