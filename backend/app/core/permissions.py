"""
Role-Based Access Control (RBAC) for OpenHeart Cyprus.

Defines permissions and roles for clinical staff access control.
"""

from enum import Enum
from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.security import TokenPayload, get_current_user


class Permission(str, Enum):
    """
    Application permissions.

    Granular permissions for RBAC enforcement.
    """

    # Patient permissions
    PATIENT_READ = "patient:read"
    PATIENT_WRITE = "patient:write"
    PATIENT_DELETE = "patient:delete"
    PATIENT_EXPORT = "patient:export"  # GDPR data export

    # Encounter permissions
    ENCOUNTER_READ = "encounter:read"
    ENCOUNTER_WRITE = "encounter:write"
    ENCOUNTER_DELETE = "encounter:delete"

    # Clinical Notes permissions
    NOTE_READ = "note:read"
    NOTE_WRITE = "note:write"
    NOTE_DELETE = "note:delete"
    NOTE_ATTACHMENT_UPLOAD = "note:attachment:upload"
    NOTE_ATTACHMENT_DOWNLOAD = "note:attachment:download"

    # Observation permissions
    OBSERVATION_READ = "observation:read"
    OBSERVATION_WRITE = "observation:write"

    # CDSS permissions
    CDSS_USE = "cdss:use"
    CDSS_OVERRIDE = "cdss:override"  # Override CDSS recommendations

    # DICOM/Imaging permissions
    DICOM_VIEW = "dicom:view"
    DICOM_UPLOAD = "dicom:upload"
    DICOM_DELETE = "dicom:delete"

    # Prescription permissions
    PRESCRIPTION_READ = "prescription:read"
    PRESCRIPTION_WRITE = "prescription:write"

    # Billing/Claims permissions
    BILLING_READ = "billing:read"
    BILLING_WRITE = "billing:write"

    # Gesy (GHS) Integration permissions
    GESY_BENEFICIARY_READ = "gesy:beneficiary:read"
    GESY_REFERRAL_READ = "gesy:referral:read"
    GESY_REFERRAL_WRITE = "gesy:referral:write"
    GESY_CLAIM_READ = "gesy:claim:read"
    GESY_CLAIM_WRITE = "gesy:claim:write"

    # Appointment permissions
    APPOINTMENT_READ = "appointment:read"
    APPOINTMENT_WRITE = "appointment:write"
    APPOINTMENT_DELETE = "appointment:delete"

    # Audit permissions
    AUDIT_READ = "audit:read"

    # Administration
    USER_MANAGE = "user:manage"
    CLINIC_MANAGE = "clinic:manage"
    ADMIN = "admin"  # Full access


# Role to permissions mapping
ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    "admin": {Permission.ADMIN},  # Admin gets all permissions
    "cardiologist": {
        # Full clinical access
        Permission.PATIENT_READ,
        Permission.PATIENT_WRITE,
        Permission.PATIENT_EXPORT,
        Permission.ENCOUNTER_READ,
        Permission.ENCOUNTER_WRITE,
        Permission.NOTE_READ,
        Permission.NOTE_WRITE,
        Permission.NOTE_ATTACHMENT_UPLOAD,
        Permission.NOTE_ATTACHMENT_DOWNLOAD,
        Permission.OBSERVATION_READ,
        Permission.OBSERVATION_WRITE,
        Permission.CDSS_USE,
        Permission.CDSS_OVERRIDE,
        Permission.DICOM_VIEW,
        Permission.DICOM_UPLOAD,
        Permission.PRESCRIPTION_READ,
        Permission.PRESCRIPTION_WRITE,
        Permission.BILLING_READ,
        Permission.BILLING_WRITE,
        # Gesy
        Permission.GESY_BENEFICIARY_READ,
        Permission.GESY_REFERRAL_READ,
        Permission.GESY_REFERRAL_WRITE,
        Permission.GESY_CLAIM_READ,
        Permission.GESY_CLAIM_WRITE,
        # Appointments
        Permission.APPOINTMENT_READ,
        Permission.APPOINTMENT_WRITE,
        Permission.APPOINTMENT_DELETE,
    },
    "nurse": {
        # Limited clinical access
        Permission.PATIENT_READ,
        Permission.ENCOUNTER_READ,
        Permission.ENCOUNTER_WRITE,
        Permission.NOTE_READ,
        Permission.NOTE_WRITE,
        Permission.NOTE_ATTACHMENT_UPLOAD,
        Permission.NOTE_ATTACHMENT_DOWNLOAD,
        Permission.OBSERVATION_READ,
        Permission.OBSERVATION_WRITE,
        Permission.CDSS_USE,
        Permission.DICOM_VIEW,
        # Gesy (read-only)
        Permission.GESY_BENEFICIARY_READ,
        Permission.GESY_REFERRAL_READ,
        # Appointments
        Permission.APPOINTMENT_READ,
        Permission.APPOINTMENT_WRITE,
    },
    "receptionist": {
        # Administrative access only
        Permission.PATIENT_READ,
        Permission.PATIENT_WRITE,
        Permission.ENCOUNTER_READ,
        Permission.NOTE_READ,
        Permission.BILLING_READ,
        # Gesy (beneficiary verification only)
        Permission.GESY_BENEFICIARY_READ,
        # Appointments (primary scheduler)
        Permission.APPOINTMENT_READ,
        Permission.APPOINTMENT_WRITE,
        Permission.APPOINTMENT_DELETE,
    },
    "auditor": {
        # Read-only audit access
        Permission.AUDIT_READ,
        Permission.PATIENT_READ,
        Permission.ENCOUNTER_READ,
        Permission.NOTE_READ,
    },
    "billing_staff": {
        # Billing-focused access
        Permission.PATIENT_READ,
        Permission.ENCOUNTER_READ,
        Permission.BILLING_READ,
        Permission.BILLING_WRITE,
        # Gesy claims
        Permission.GESY_BENEFICIARY_READ,
        Permission.GESY_REFERRAL_READ,
        Permission.GESY_CLAIM_READ,
        Permission.GESY_CLAIM_WRITE,
    },
}


def has_permission(role: str, permission: Permission) -> bool:
    """
    Check if a role has a specific permission.

    Args:
        role: User's role
        permission: Required permission

    Returns:
        True if role has permission, False otherwise
    """
    # Admin role has all permissions
    if role == "admin" or Permission.ADMIN in ROLE_PERMISSIONS.get(role, set()):
        return True

    return permission in ROLE_PERMISSIONS.get(role, set())


def get_role_permissions(role: str) -> set[Permission]:
    """
    Get all permissions for a role.

    Args:
        role: User's role

    Returns:
        Set of permissions for the role
    """
    if role == "admin":
        return set(Permission)  # All permissions
    return ROLE_PERMISSIONS.get(role, set())


def require_permission(permission: Permission):
    """
    Dependency factory for permission checking.

    Usage:
        @router.get("/patients")
        async def list_patients(
            user: TokenPayload = Depends(require_permission(Permission.PATIENT_READ))
        ):
            ...

    Args:
        permission: Required permission

    Returns:
        Dependency function that validates permission
    """

    async def permission_checker(
        user: Annotated[TokenPayload, Depends(get_current_user)],
    ) -> TokenPayload:
        if not has_permission(user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value} required",
            )
        return user

    return permission_checker


def require_any_permission(*permissions: Permission):
    """
    Dependency factory requiring any of the specified permissions.

    Args:
        *permissions: Permissions where at least one is required

    Returns:
        Dependency function that validates any permission
    """

    async def permission_checker(
        user: Annotated[TokenPayload, Depends(get_current_user)],
    ) -> TokenPayload:
        for permission in permissions:
            if has_permission(user.role, permission):
                return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: one of {[p.value for p in permissions]} required",
        )

    return permission_checker


def require_all_permissions(*permissions: Permission):
    """
    Dependency factory requiring all specified permissions.

    Args:
        *permissions: All permissions required

    Returns:
        Dependency function that validates all permissions
    """

    async def permission_checker(
        user: Annotated[TokenPayload, Depends(get_current_user)],
    ) -> TokenPayload:
        missing = [p for p in permissions if not has_permission(user.role, p)]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {[p.value for p in missing]} required",
            )
        return user

    return permission_checker
