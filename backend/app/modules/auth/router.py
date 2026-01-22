"""
Authentication API endpoints for OpenHeart Cyprus.

Provides login, token refresh, logout, and invitation endpoints.
All endpoints follow GDPR audit logging requirements.
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.permissions import Permission, require_permission
from app.core.security import TokenPayload, create_access_token, decode_token
from app.db.session import get_db
from app.modules.auth.invitation import InvitationService
from app.modules.auth.schemas import (
    InvitationAcceptRequest,
    InvitationAcceptResponse,
    InvitationCreateRequest,
    InvitationListResponse,
    InvitationResponse,
    InvitationValidateResponse,
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


# =============================================================================
# Invitation Endpoints (Admin)
# =============================================================================


async def get_invitation_service(db: AsyncSession = Depends(get_db)) -> InvitationService:
    """Dependency to get InvitationService instance."""
    return InvitationService(db)


@router.post(
    "/admin/users/invite",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user invitation",
    description="""
    Create an invitation for a new user to join a clinic.

    **Permissions Required:** USER_MANAGEMENT or ADMIN role

    The invitation email will contain a secure token link that expires in 7 days.
    The invitee must create their account using the link and set their password.
    """,
)
async def create_invitation(
    data: InvitationCreateRequest,
    user: TokenPayload = Depends(require_permission(Permission.USER_MANAGE)),
    service: InvitationService = Depends(get_invitation_service),
) -> InvitationResponse:
    """Create a new user invitation."""
    try:
        return await service.create_invitation(data, invited_by_user_id=user.sub)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/admin/invitations",
    response_model=InvitationListResponse,
    summary="List invitations",
    description="""
    List user invitations with optional filters.

    **Permissions Required:** USER_MANAGEMENT or ADMIN role

    Can filter by clinic_id and status (pending, accepted, expired, revoked).
    """,
)
async def list_invitations(
    clinic_id: Annotated[
        Optional[int],
        Query(description="Filter by clinic ID"),
    ] = None,
    invitation_status: Annotated[
        Optional[str],
        Query(description="Filter by status: pending, accepted, expired, revoked"),
    ] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    user: TokenPayload = Depends(require_permission(Permission.USER_MANAGE)),
    service: InvitationService = Depends(get_invitation_service),
) -> InvitationListResponse:
    """List invitations with pagination."""
    invitations, total = await service.list_invitations(
        clinic_id=clinic_id,
        status=invitation_status,
        page=page,
        per_page=per_page,
    )

    return InvitationListResponse(
        invitations=invitations,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.delete(
    "/admin/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke invitation",
    description="""
    Revoke a pending invitation.

    **Permissions Required:** USER_MANAGEMENT or ADMIN role

    Only pending invitations can be revoked. Already accepted or expired
    invitations cannot be revoked.
    """,
)
async def revoke_invitation(
    invitation_id: int,
    user: TokenPayload = Depends(require_permission(Permission.USER_MANAGE)),
    service: InvitationService = Depends(get_invitation_service),
) -> None:
    """Revoke a pending invitation."""
    success = await service.revoke_invitation(invitation_id, revoked_by_user_id=user.sub)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or already processed",
        )

    return None


# =============================================================================
# Invitation Endpoints (Public - for invitees)
# =============================================================================


@router.get(
    "/invitations/{token}",
    response_model=InvitationValidateResponse,
    summary="Validate invitation token",
    description="""
    Validate an invitation token.

    **Public endpoint - no authentication required**

    Use this to check if an invitation is valid before showing the
    registration form. Returns invitation details if valid.
    """,
)
async def validate_invitation(
    token: str,
    service: InvitationService = Depends(get_invitation_service),
) -> InvitationValidateResponse:
    """Validate an invitation token (public)."""
    result = await service.validate_invitation_token(token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired invitation",
        )

    return result


@router.post(
    "/invitations/{token}/accept",
    response_model=InvitationAcceptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Accept invitation",
    description="""
    Accept an invitation and create user account.

    **Public endpoint - no authentication required**

    Creates a new user account with the email, name, and role specified
    in the invitation. The user must provide a strong password and
    accept GDPR consent and terms of service.

    **Password Requirements:**
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """,
)
async def accept_invitation(
    token: str,
    request: Request,
    data: InvitationAcceptRequest,
    service: InvitationService = Depends(get_invitation_service),
) -> InvitationAcceptResponse:
    """Accept an invitation and create account (public)."""
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    try:
        return await service.accept_invitation(
            token=token,
            data=data,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# MFA Endpoints (Authenticated)
# =============================================================================

from app.core.security import get_current_user


async def get_mfa_service(db: AsyncSession = Depends(get_db)) -> "MFAService":
    """Dependency to get MFAService instance."""
    from app.modules.auth.mfa import MFAService

    return MFAService(db)


@router.post(
    "/me/mfa/setup",
    response_model=dict,
    summary="Initialize MFA setup",
    description="""
    Start MFA setup by generating a new TOTP secret.

    Returns the secret (for manual entry) and provisioning URI (for QR code).
    MFA is NOT enabled until /me/mfa/verify is called with a valid code.
    """,
)
async def setup_mfa(
    request: Request,
    user: TokenPayload = Depends(get_current_user),
    service: "MFAService" = Depends(get_mfa_service),
) -> dict:
    """Initialize MFA setup."""
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    return await service.setup_mfa(
        user_id=user.sub,
        ip_address=ip_address,
        user_agent=user_agent,
    )


@router.post(
    "/me/mfa/verify",
    response_model=dict,
    summary="Verify and enable MFA",
    description="""
    Verify the TOTP code and enable MFA for the account.

    Must be called after /me/mfa/setup with a valid 6-digit code
    from your authenticator app. Returns backup codes on success.

    **Save your backup codes securely!** They will only be shown once.
    """,
)
async def verify_mfa(
    request: Request,
    code: str = Query(..., min_length=6, max_length=6, description="6-digit TOTP code"),
    user: TokenPayload = Depends(get_current_user),
    service: "MFAService" = Depends(get_mfa_service),
) -> dict:
    """Verify TOTP code and enable MFA."""
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    try:
        return await service.verify_and_enable(
            user_id=user.sub,
            code=code,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/auth/mfa/challenge",
    response_model=dict,
    summary="Verify MFA during login",
    description="""
    Verify MFA code during the login process.

    Called after initial login returns mfa_required=true.
    Accepts either a 6-digit TOTP code or an 8-character backup code.
    """,
)
async def verify_mfa_challenge(
    request: Request,
    code: str = Query(..., description="TOTP code or backup code"),
    user: TokenPayload = Depends(get_current_user),
    service: "MFAService" = Depends(get_mfa_service),
) -> dict:
    """Verify MFA during login flow."""
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    success = await service.verify_code(
        user_id=user.sub,
        code=code,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA code",
        )

    # TODO: Return new token with mfa_verified=True
    # This requires creating a new access token
    return {"success": True, "message": "MFA verified successfully"}


@router.delete(
    "/me/mfa",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Disable MFA",
    description="""
    Disable MFA for the account.

    Requires password confirmation for security.
    """,
)
async def disable_mfa(
    request: Request,
    password: str = Query(..., description="Current password for verification"),
    user: TokenPayload = Depends(get_current_user),
    service: "MFAService" = Depends(get_mfa_service),
) -> None:
    """Disable MFA for the account."""
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    try:
        await service.disable_mfa(
            user_id=user.sub,
            password=password,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/me/mfa/status",
    response_model=dict,
    summary="Get MFA status",
    description="Get current MFA status including backup code count.",
)
async def get_mfa_status(
    user: TokenPayload = Depends(get_current_user),
    service: "MFAService" = Depends(get_mfa_service),
) -> dict:
    """Get MFA status for current user."""
    return await service.get_mfa_status(user.sub)


@router.post(
    "/me/mfa/backup-codes",
    response_model=dict,
    summary="Regenerate backup codes",
    description="""
    Generate new backup codes (invalidates old ones).

    Requires current TOTP code for verification.
    **Save your new backup codes securely!**
    """,
)
async def regenerate_backup_codes(
    request: Request,
    code: str = Query(..., min_length=6, max_length=6, description="Current TOTP code"),
    user: TokenPayload = Depends(get_current_user),
    service: "MFAService" = Depends(get_mfa_service),
) -> dict:
    """Regenerate backup codes."""
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    try:
        codes = await service.regenerate_backup_codes(
            user_id=user.sub,
            code=code,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return {"backup_codes": codes}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# Password Reset Endpoints
# =============================================================================


async def get_password_service(db: AsyncSession = Depends(get_db)) -> "PasswordResetService":
    """Dependency to get PasswordResetService instance."""
    from app.modules.auth.password_reset import PasswordResetService

    return PasswordResetService(db)


@router.post(
    "/auth/password/reset-request",
    response_model=dict,
    summary="Request password reset",
    description="""
    Request a password reset email.

    **Public endpoint - no authentication required**

    Always returns success to prevent email enumeration.
    If the email exists, a reset link will be sent.
    """,
)
async def request_password_reset(
    request: Request,
    email: str = Query(..., description="Email address"),
    service: "PasswordResetService" = Depends(get_password_service),
) -> dict:
    """Request password reset email."""
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    await service.request_reset(
        email=email,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return {
        "success": True,
        "message": "If an account exists with this email, a reset link will be sent.",
    }


@router.get(
    "/auth/password/reset/{token}",
    response_model=dict,
    summary="Validate reset token",
    description="""
    Validate a password reset token.

    **Public endpoint - no authentication required**

    Use this to check if a reset token is valid before showing
    the password reset form.
    """,
)
async def validate_reset_token(
    token: str,
    service: "PasswordResetService" = Depends(get_password_service),
) -> dict:
    """Validate password reset token."""
    result = await service.validate_token(token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired reset token",
        )

    return result


@router.post(
    "/auth/password/reset",
    response_model=dict,
    summary="Reset password",
    description="""
    Reset password using a valid token.

    **Public endpoint - no authentication required**

    **Password Requirements:**
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """,
)
async def reset_password(
    request: Request,
    token: str = Query(..., description="Reset token from email"),
    new_password: str = Query(..., min_length=12, description="New password"),
    service: "PasswordResetService" = Depends(get_password_service),
) -> dict:
    """Reset password with token."""
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    try:
        await service.reset_password(
            token=token,
            new_password=new_password,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return {"success": True, "message": "Password has been reset successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put(
    "/me/password",
    response_model=dict,
    summary="Change password",
    description="""
    Change password for the current user.

    Requires verification of current password.

    **Password Requirements:**
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """,
)
async def change_password(
    request: Request,
    current_password: str = Query(..., description="Current password"),
    new_password: str = Query(..., min_length=12, description="New password"),
    user: TokenPayload = Depends(get_current_user),
    service: "PasswordResetService" = Depends(get_password_service),
) -> dict:
    """Change password for authenticated user."""
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    try:
        await service.change_password(
            user_id=user.sub,
            current_password=current_password,
            new_password=new_password,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return {"success": True, "message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# Session Management Endpoints
# =============================================================================


async def get_session_manager(db: AsyncSession = Depends(get_db)) -> "SessionManager":
    """Dependency to get SessionManager instance."""
    from app.modules.auth.session_manager import SessionManager

    return SessionManager(db)


@router.get(
    "/me/sessions",
    response_model=list[dict],
    summary="List active sessions",
    description="""
    List all active sessions for the current user.

    Returns device info, IP address, and last activity for each session.
    """,
)
async def list_sessions(
    request: Request,
    user: TokenPayload = Depends(get_current_user),
    session_manager: "SessionManager" = Depends(get_session_manager),
) -> list[dict]:
    """List active sessions for current user."""
    # Get current token to mark current session
    auth_header = request.headers.get("authorization", "")
    current_token = auth_header[7:] if auth_header.startswith("Bearer ") else None

    sessions = await session_manager.list_user_sessions(user.sub)

    # Mark current session
    if current_token:
        from app.modules.auth.session_manager import hash_token

        current_hash = hash_token(current_token)
        current_session = await session_manager.get_session_by_token(current_token)
        if current_session:
            for s in sessions:
                if s["id"] == str(current_session.id):
                    s["is_current"] = True
                    break

    return sessions


@router.delete(
    "/me/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke specific session",
    description="""
    Revoke a specific session by ID.

    Use this to sign out from a specific device.
    """,
)
async def revoke_session(
    session_id: str,
    user: TokenPayload = Depends(get_current_user),
    session_manager: "SessionManager" = Depends(get_session_manager),
) -> None:
    """Revoke a specific session."""
    from uuid import UUID

    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format",
        )

    success = await session_manager.revoke_session(session_uuid, reason="user_revoke")

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or already revoked",
        )


@router.delete(
    "/me/sessions",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke all other sessions",
    description="""
    Revoke all sessions except the current one.

    Use this to sign out from all other devices.
    """,
)
async def revoke_all_sessions(
    request: Request,
    user: TokenPayload = Depends(get_current_user),
    session_manager: "SessionManager" = Depends(get_session_manager),
) -> None:
    """Revoke all sessions except current."""
    # Get current token to exclude
    auth_header = request.headers.get("authorization", "")
    current_token = auth_header[7:] if auth_header.startswith("Bearer ") else None

    await session_manager.revoke_all_user_sessions(
        user_id=user.sub,
        reason="user_revoke_all",
        exclude_token=current_token,
    )
