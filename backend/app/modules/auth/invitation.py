"""
Invitation service for OpenHeart Cyprus.

Handles user invitation creation, validation, and acceptance.
All operations are logged for GDPR compliance.
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.modules.auth.models import InvitationStatus, UserInvitation
from app.modules.auth.schemas import (
    InvitationAcceptRequest,
    InvitationAcceptResponse,
    InvitationCreateRequest,
    InvitationResponse,
    InvitationValidateResponse,
)
from app.modules.clinic.models import Clinic, User, UserClinicRole

logger = logging.getLogger(__name__)

# Invitation expiration time
INVITATION_EXPIRY_DAYS = 7


def generate_invitation_token() -> str:
    """Generate a cryptographically secure invitation token."""
    return secrets.token_urlsafe(48)  # 64 characters


class InvitationService:
    """
    Service for managing user invitations.

    Provides methods to create, validate, accept, and revoke invitations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_invitation(
        self,
        data: InvitationCreateRequest,
        invited_by_user_id: int,
    ) -> InvitationResponse:
        """
        Create a new user invitation.

        Args:
            data: Invitation details
            invited_by_user_id: ID of the admin creating the invitation

        Returns:
            InvitationResponse with created invitation details

        Raises:
            ValueError: If email already exists or clinic not found
        """
        # Check if email already exists as a user
        existing_user = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        if existing_user.scalar_one_or_none():
            raise ValueError("A user with this email already exists")

        # Check for existing pending invitation
        existing_invitation = await self.db.execute(
            select(UserInvitation).where(
                UserInvitation.email == data.email,
                UserInvitation.status == InvitationStatus.PENDING.value,
            )
        )
        if existing_invitation.scalar_one_or_none():
            raise ValueError("A pending invitation already exists for this email")

        # Validate clinic exists
        clinic = await self.db.execute(
            select(Clinic).where(Clinic.clinic_id == data.clinic_id)
        )
        clinic_obj = clinic.scalar_one_or_none()
        if not clinic_obj:
            raise ValueError("Clinic not found")

        # Get inviter info
        inviter = await self.db.execute(
            select(User).where(User.user_id == invited_by_user_id)
        )
        inviter_obj = inviter.scalar_one_or_none()

        # Create invitation
        token = generate_invitation_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=INVITATION_EXPIRY_DAYS)

        invitation = UserInvitation(
            token=token,
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            clinic_id=data.clinic_id,
            role=data.role,
            title=data.title,
            specialty=data.specialty,
            license_number=data.license_number,
            invited_by_user_id=invited_by_user_id,
            expires_at=expires_at,
            message=data.message,
            status=InvitationStatus.PENDING.value,
        )

        self.db.add(invitation)
        await self.db.commit()
        await self.db.refresh(invitation)

        logger.info(
            f"Invitation created for {data.email} to join {clinic_obj.name} "
            f"as {data.role} by user {invited_by_user_id}"
        )

        return InvitationResponse(
            invitation_id=invitation.invitation_id,
            email=invitation.email,
            first_name=invitation.first_name,
            last_name=invitation.last_name,
            role=invitation.role,
            clinic_id=invitation.clinic_id,
            clinic_name=clinic_obj.name,
            status=invitation.status,
            invited_by_name=inviter_obj.full_name if inviter_obj else None,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
        )

    async def list_invitations(
        self,
        clinic_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[InvitationResponse], int]:
        """
        List invitations with optional filters.

        Args:
            clinic_id: Filter by clinic
            status: Filter by status
            page: Page number (1-indexed)
            per_page: Items per page

        Returns:
            Tuple of (invitations list, total count)
        """
        # Build base query
        query = select(UserInvitation).options(
            selectinload(UserInvitation.clinic),
            selectinload(UserInvitation.invited_by),
        )

        # Apply filters
        if clinic_id:
            query = query.where(UserInvitation.clinic_id == clinic_id)
        if status:
            query = query.where(UserInvitation.status == status)

        # Count total
        count_query = select(func.count(UserInvitation.invitation_id))
        if clinic_id:
            count_query = count_query.where(UserInvitation.clinic_id == clinic_id)
        if status:
            count_query = count_query.where(UserInvitation.status == status)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = (
            query.order_by(UserInvitation.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )

        result = await self.db.execute(query)
        invitations = result.scalars().all()

        # Build response list
        response_list = []
        for inv in invitations:
            response_list.append(
                InvitationResponse(
                    invitation_id=inv.invitation_id,
                    email=inv.email,
                    first_name=inv.first_name,
                    last_name=inv.last_name,
                    role=inv.role,
                    clinic_id=inv.clinic_id,
                    clinic_name=inv.clinic.name if inv.clinic else "Unknown",
                    status=inv.status,
                    invited_by_name=inv.invited_by.full_name if inv.invited_by else None,
                    expires_at=inv.expires_at,
                    created_at=inv.created_at,
                    accepted_at=inv.accepted_at,
                )
            )

        return response_list, total

    async def get_invitation_by_id(self, invitation_id: int) -> Optional[UserInvitation]:
        """Get invitation by ID."""
        result = await self.db.execute(
            select(UserInvitation)
            .where(UserInvitation.invitation_id == invitation_id)
            .options(
                selectinload(UserInvitation.clinic),
                selectinload(UserInvitation.invited_by),
            )
        )
        return result.scalar_one_or_none()

    async def revoke_invitation(self, invitation_id: int, revoked_by_user_id: int) -> bool:
        """
        Revoke a pending invitation.

        Args:
            invitation_id: ID of invitation to revoke
            revoked_by_user_id: ID of user revoking

        Returns:
            True if revoked, False if not found or already processed
        """
        invitation = await self.get_invitation_by_id(invitation_id)

        if not invitation:
            return False

        if invitation.status != InvitationStatus.PENDING.value:
            return False

        invitation.status = InvitationStatus.REVOKED.value
        await self.db.commit()

        logger.info(
            f"Invitation {invitation_id} for {invitation.email} "
            f"revoked by user {revoked_by_user_id}"
        )

        return True

    async def validate_invitation_token(self, token: str) -> Optional[InvitationValidateResponse]:
        """
        Validate an invitation token (public endpoint).

        Args:
            token: Invitation token

        Returns:
            Validation response if valid, None otherwise
        """
        result = await self.db.execute(
            select(UserInvitation)
            .where(UserInvitation.token == token)
            .options(selectinload(UserInvitation.clinic))
        )
        invitation = result.scalar_one_or_none()

        if not invitation:
            return None

        # Check status
        if invitation.status != InvitationStatus.PENDING.value:
            return None

        # Check expiration
        if invitation.expires_at < datetime.now(timezone.utc):
            # Mark as expired
            invitation.status = InvitationStatus.EXPIRED.value
            await self.db.commit()
            return None

        return InvitationValidateResponse(
            valid=True,
            email=invitation.email,
            first_name=invitation.first_name,
            last_name=invitation.last_name,
            role=invitation.role,
            clinic_name=invitation.clinic.name if invitation.clinic else "Unknown",
            title=invitation.title,
            specialty=invitation.specialty,
            message=invitation.message,
            expires_at=invitation.expires_at,
        )

    async def accept_invitation(
        self,
        token: str,
        data: InvitationAcceptRequest,
        ip_address: str,
        user_agent: str,
    ) -> InvitationAcceptResponse:
        """
        Accept an invitation and create user account.

        Args:
            token: Invitation token
            data: Account creation data (password, consents)
            ip_address: Client IP for audit
            user_agent: Client user agent for audit

        Returns:
            Account creation response

        Raises:
            ValueError: If invitation invalid/expired or user creation fails
        """
        # Get and validate invitation
        result = await self.db.execute(
            select(UserInvitation)
            .where(UserInvitation.token == token)
            .options(selectinload(UserInvitation.clinic))
        )
        invitation = result.scalar_one_or_none()

        if not invitation:
            raise ValueError("Invalid invitation token")

        if invitation.status != InvitationStatus.PENDING.value:
            raise ValueError(f"Invitation is no longer valid (status: {invitation.status})")

        if invitation.expires_at < datetime.now(timezone.utc):
            invitation.status = InvitationStatus.EXPIRED.value
            await self.db.commit()
            raise ValueError("Invitation has expired")

        # Check email not already taken (race condition check)
        existing_user = await self.db.execute(
            select(User).where(User.email == invitation.email)
        )
        if existing_user.scalar_one_or_none():
            raise ValueError("A user with this email already exists")

        # Create user
        password_hash = hash_password(data.password)

        user = User(
            email=invitation.email,
            password_hash=password_hash,
            first_name=invitation.first_name,
            last_name=invitation.last_name,
            title=invitation.title,
            specialty=invitation.specialty,
            license_number=invitation.license_number,
            is_active=True,
            email_verified=True,  # Invitation validates email
            password_changed_at=datetime.now(timezone.utc),
        )

        self.db.add(user)
        await self.db.flush()  # Get user_id

        # Create clinic role assignment
        clinic_role = UserClinicRole(
            user_id=user.user_id,
            clinic_id=invitation.clinic_id,
            role=invitation.role,
            is_primary_clinic=True,
            is_active=True,
        )

        self.db.add(clinic_role)

        # Update invitation
        invitation.status = InvitationStatus.ACCEPTED.value
        invitation.accepted_at = datetime.now(timezone.utc)
        invitation.accepted_user_id = user.user_id

        await self.db.commit()

        logger.info(
            f"Invitation accepted: User {user.user_id} ({invitation.email}) "
            f"joined {invitation.clinic.name} as {invitation.role} from {ip_address}"
        )

        return InvitationAcceptResponse(
            user_id=user.user_id,
            email=user.email,
            full_name=user.full_name,
            role=invitation.role,
            clinic_id=invitation.clinic_id,
            clinic_name=invitation.clinic.name if invitation.clinic else "Unknown",
        )

    async def cleanup_expired_invitations(self) -> int:
        """
        Mark expired pending invitations as expired.

        Returns:
            Number of invitations marked as expired
        """
        result = await self.db.execute(
            select(UserInvitation).where(
                UserInvitation.status == InvitationStatus.PENDING.value,
                UserInvitation.expires_at < datetime.now(timezone.utc),
            )
        )
        expired = result.scalars().all()

        count = 0
        for inv in expired:
            inv.status = InvitationStatus.EXPIRED.value
            count += 1

        if count > 0:
            await self.db.commit()
            logger.info(f"Cleaned up {count} expired invitations")

        return count
