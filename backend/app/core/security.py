"""
Authentication and Authorization for OpenHeart Cyprus.

Provides JWT token management, password hashing, and MFA (TOTP) support.
All clinical accounts require MFA per GDPR/Cyprus Law 125(I)/2018.

Password hashing uses Argon2id (OWASP recommended) with automatic
rehashing of legacy bcrypt hashes on successful login.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional, Tuple
from uuid import uuid4

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.config import settings

# HTTP Bearer token security scheme
security = HTTPBearer()

# =============================================================================
# Password Hashing Configuration (Argon2id - OWASP recommended)
# =============================================================================

# Argon2id with OWASP recommended parameters
# Memory: 65536 KB (64 MB), Iterations: 3, Parallelism: 4
argon2_hasher = PasswordHasher(
    time_cost=3,        # iterations
    memory_cost=65536,  # 64 MB
    parallelism=4,      # parallel threads
    hash_len=32,        # output hash length
    salt_len=16,        # salt length
)

# Legacy bcrypt context for rehashing old passwords
legacy_bcrypt = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =============================================================================
# Token Models
# =============================================================================


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: int  # user_id
    email: Optional[str] = None
    clinic_id: Optional[int] = None
    role: Optional[str] = None
    jti: str = ""  # JWT ID for token blacklisting (empty = legacy token)
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
# Password Functions (Argon2id with bcrypt fallback)
# =============================================================================


def hash_password(password: str) -> str:
    """
    Hash a password using Argon2id (OWASP recommended).

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return argon2_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Supports both Argon2id (preferred) and legacy bcrypt hashes.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored password hash

    Returns:
        True if password matches, False otherwise
    """
    is_valid, _ = verify_password_with_rehash(plain_password, hashed_password)
    return is_valid


def verify_password_with_rehash(
    plain_password: str,
    hashed_password: str,
) -> Tuple[bool, str | None]:
    """
    Verify password and return new hash if rehashing is needed.

    Automatically detects and verifies:
    - Argon2id hashes (preferred)
    - Legacy bcrypt hashes (migrated from older system)

    If a legacy bcrypt hash is detected and verification succeeds,
    returns a new Argon2id hash for the caller to update.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored password hash

    Returns:
        Tuple of (is_valid, new_hash_if_rehash_needed)
        - (True, None) - Argon2id verified, no rehash needed
        - (True, new_hash) - bcrypt verified, should update to new_hash
        - (False, None) - Verification failed
    """
    # Check if this is an Argon2 hash (starts with $argon2)
    if hashed_password.startswith("$argon2"):
        try:
            argon2_hasher.verify(hashed_password, plain_password)

            # Check if hash needs update (parameters changed)
            if argon2_hasher.check_needs_rehash(hashed_password):
                return True, argon2_hasher.hash(plain_password)

            return True, None
        except VerifyMismatchError:
            return False, None
        except InvalidHashError:
            return False, None

    # Check if this is a bcrypt hash (starts with $2b$, $2a$, or $2y$)
    if hashed_password.startswith(("$2b$", "$2a$", "$2y$")):
        if legacy_bcrypt.verify(plain_password, hashed_password):
            # Password verified, return new Argon2id hash for upgrade
            new_hash = argon2_hasher.hash(plain_password)
            return True, new_hash
        return False, None

    # Unknown hash format
    return False, None


def is_argon2_hash(hashed_password: str) -> bool:
    """Check if password hash is using Argon2."""
    return hashed_password.startswith("$argon2")


def is_bcrypt_hash(hashed_password: str) -> bool:
    """Check if password hash is using bcrypt (legacy)."""
    return hashed_password.startswith(("$2b$", "$2a$", "$2y$"))


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
        "sub": str(user_id),  # RFC 7519 requires sub to be a string
        "email": email,
        "clinic_id": clinic_id,
        "role": role,
        "jti": str(uuid4()),
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
        "sub": str(user_id),  # RFC 7519 requires sub to be a string
        "jti": str(uuid4()),
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
    request: Request,
) -> TokenPayload:
    """
    Dependency to get the current authenticated user from JWT token.

    Validates the token signature/expiry, then checks Redis for:
    1. Token-level blacklisting (logout)
    2. User-level session invalidation (password reset)

    Args:
        credentials: HTTP Bearer token credentials
        request: FastAPI request (for Redis access)

    Returns:
        Decoded token payload with user information

    Raises:
        HTTPException: If token is missing, invalid, expired, or revoked
    """
    payload = decode_token(credentials.credentials)

    # Ensure this is an access token
    if payload.token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Expected access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    redis_client = getattr(request.app.state, "redis", None)
    if redis_client and payload.jti:
        from app.core.redis import get_user_invalidation_time, is_token_blacklisted

        # Check if this specific token was blacklisted (e.g., on logout)
        if await is_token_blacklisted(redis_client, payload.jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user sessions were globally invalidated after this token was issued
        invalidation_time = await get_user_invalidation_time(redis_client, payload.sub)
        if invalidation_time and payload.iat.replace(tzinfo=None) < invalidation_time.replace(tzinfo=None):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session invalidated. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return payload


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
