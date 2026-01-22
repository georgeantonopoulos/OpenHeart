"""
Authentication and Authorization for OpenHeart Cyprus.

Provides JWT token management, password hashing, and MFA (TOTP) support.
All clinical accounts require MFA per GDPR/Cyprus Law 125(I)/2018.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

import pyotp
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token security scheme
security = HTTPBearer()


# =============================================================================
# Token Models
# =============================================================================


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: int  # user_id
    email: str
    clinic_id: int
    role: str
    mfa_verified: bool = False
    token_type: str = "access"
    exp: datetime
    iat: datetime


class TokenResponse(BaseModel):
    """Token response for login endpoints."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


# =============================================================================
# Password Functions
# =============================================================================


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored password hash

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# =============================================================================
# JWT Token Functions
# =============================================================================


def create_access_token(
    user_id: int,
    email: str,
    clinic_id: int,
    role: str,
    mfa_verified: bool = False,
) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User's database ID
        email: User's email address
        clinic_id: User's clinic ID for RLS
        role: User's role (admin, cardiologist, nurse, etc.)
        mfa_verified: Whether MFA has been verified

    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_expiry_minutes)

    payload = {
        "sub": user_id,
        "email": email,
        "clinic_id": clinic_id,
        "role": role,
        "mfa_verified": mfa_verified,
        "token_type": "access",
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: int) -> str:
    """
    Create a JWT refresh token with longer expiry.

    Args:
        user_id: User's database ID

    Returns:
        Encoded JWT refresh token string
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.refresh_token_expiry_days)

    payload = {
        "sub": user_id,
        "token_type": "refresh",
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload(**payload)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# =============================================================================
# Authentication Dependencies
# =============================================================================


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> TokenPayload:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        Decoded token payload with user information

    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    return decode_token(credentials.credentials)


async def require_mfa(
    user: Annotated[TokenPayload, Depends(get_current_user)],
) -> TokenPayload:
    """
    Dependency that requires MFA verification.

    Use this for sensitive operations that require additional security.

    Args:
        user: Current user from token

    Returns:
        User payload if MFA is verified

    Raises:
        HTTPException: If MFA is not verified
    """
    if not user.mfa_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA verification required. Please complete two-factor authentication.",
        )
    return user


# =============================================================================
# TOTP (MFA) Functions
# =============================================================================


def generate_totp_secret() -> str:
    """
    Generate a new TOTP secret for MFA setup.

    Returns:
        Base32-encoded TOTP secret
    """
    return pyotp.random_base32()


def get_totp_provisioning_uri(secret: str, email: str) -> str:
    """
    Generate a TOTP provisioning URI for authenticator apps.

    Args:
        secret: TOTP secret
        email: User's email for identification

    Returns:
        otpauth:// URI for QR code generation
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=email,
        issuer_name=settings.totp_issuer,
    )


def verify_totp(secret: str, token: str) -> bool:
    """
    Verify a TOTP token.

    Args:
        secret: User's TOTP secret
        token: 6-digit TOTP code from authenticator app

    Returns:
        True if token is valid, False otherwise
    """
    totp = pyotp.TOTP(secret)
    # Allow 1 time step tolerance for clock drift
    return totp.verify(token, valid_window=1)


def get_totp_current(secret: str) -> str:
    """
    Get the current TOTP token (for testing only).

    Args:
        secret: TOTP secret

    Returns:
        Current 6-digit TOTP code
    """
    totp = pyotp.TOTP(secret)
    return totp.now()
