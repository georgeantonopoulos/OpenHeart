"""
Authentication API endpoints for OpenHeart Cyprus.

Provides login, token refresh, and logout endpoints.
All endpoints follow GDPR audit logging requirements.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import create_access_token, decode_token
from app.db.session import get_db
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    UserInfo,
)
from app.modules.auth.service import AuthEvent, AuthService, log_auth_event

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request, handling proxies."""
    # Check X-Forwarded-For header (set by reverse proxy)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP header
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip

    # Fall back to direct connection
    if request.client:
        return request.client.host

    return "unknown"


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency to get AuthService instance."""
    return AuthService(db)


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        401: {"description": "Invalid credentials"},
        403: {"description": "Account locked or no clinic assignment"},
    },
)
async def login(
    request: Request,
    data: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """
    Authenticate user with email and password.

    Returns JWT access and refresh tokens on successful authentication.

    **Security Notes:**
    - Account locks after 5 failed attempts for 15 minutes
    - All login attempts are logged for GDPR compliance
    - In development mode, MFA requirement is bypassed

    **Errors:**
    - 401: Invalid email or password (generic to prevent enumeration)
    - 403: Account locked or user has no active clinic assignment
    """
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    # Authenticate user
    user = await service.authenticate_user(
        email=data.email,
        password=data.password,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get primary clinic role
    clinic_role = service.get_primary_clinic_role(user)

    if not clinic_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no active clinic assignment. Please contact your administrator.",
        )

    # Create tokens
    access_token, refresh_token = service.create_tokens(user, clinic_role)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_expiry_minutes * 60,
        user=UserInfo(
            user_id=user.user_id,
            email=user.email,
            full_name=user.full_name,
            role=clinic_role.role,
            clinic_id=clinic_role.clinic_id,
            clinic_name=clinic_role.clinic.name,
        ),
    )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    responses={
        401: {"description": "Invalid or expired refresh token"},
        403: {"description": "User inactive or no clinic assignment"},
    },
)
async def refresh_token(
    request: Request,
    data: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
) -> RefreshResponse:
    """
    Refresh access token using a valid refresh token.

    Use this endpoint when your access token expires (15 minutes by default).
    Refresh tokens are valid for 7 days.

    **Errors:**
    - 401: Refresh token is invalid, expired, or wrong type
    - 403: User account is inactive or has no clinic assignment
    """
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    try:
        payload = decode_token(data.refresh_token)

        # Verify this is a refresh token
        if payload.token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Expected refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except HTTPException:
        # Re-raise HTTPException from decode_token
        raise
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get fresh user data
    user = await service.get_user_by_id(payload.sub)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Get primary clinic role
    clinic_role = service.get_primary_clinic_role(user)

    if not clinic_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no active clinic assignment",
        )

    # In development, bypass MFA requirement
    mfa_verified = settings.environment == "development" or not user.mfa_enabled

    # Create new access token
    new_access_token = create_access_token(
        user_id=user.user_id,
        email=user.email,
        clinic_id=clinic_role.clinic_id,
        role=clinic_role.role,
        mfa_verified=mfa_verified,
    )

    # Log token refresh
    await log_auth_event(
        event=AuthEvent.TOKEN_REFRESH,
        email=user.email,
        ip_address=ip_address,
        user_agent=user_agent,
        user_id=user.user_id,
        clinic_id=clinic_role.clinic_id,
    )

    return RefreshResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.jwt_expiry_minutes * 60,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(request: Request) -> None:
    """
    Logout user and invalidate session.

    **Current Implementation (Phase 1):**
    This is a no-op since we use stateless JWTs.
    The client should delete stored tokens locally.

    **Future Implementation (Phase 2):**
    Will add token blacklisting via Redis to support
    immediate session invalidation.
    """
    # Log logout attempt (best effort - may not have valid token)
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    # Try to extract email from Authorization header for logging
    auth_header = request.headers.get("authorization", "")
    email = "unknown"

    if auth_header.startswith("Bearer "):
        try:
            token = auth_header[7:]
            payload = decode_token(token)
            email = payload.email

            await log_auth_event(
                event=AuthEvent.LOGOUT,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                user_id=payload.sub,
                clinic_id=payload.clinic_id,
            )
        except Exception:
            # Token might be expired or invalid, still log logout attempt
            await log_auth_event(
                event=AuthEvent.LOGOUT,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                details="Token invalid or expired",
            )

    # TODO (Phase 2): Add token to Redis blacklist
    # await redis.setex(f"blacklist:{token}", settings.jwt_expiry_minutes * 60, "1")

    return None
