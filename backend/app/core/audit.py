"""
GDPR Audit Logging Middleware for OpenHeart Cyprus.

Logs all access to sensitive resources as required by:
- GDPR (General Data Protection Regulation)
- Cyprus Law 125(I)/2018

Audit logs are retained for 15 years per Cyprus healthcare regulations.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


# Paths that require audit logging
AUDITED_PATHS = [
    "/api/patients",
    "/api/encounters",
    "/api/observations",
    "/api/notes",
    "/api/cdss",
    "/api/dicom",
    "/api/gesy",
    "/api/prescriptions",
    "/fhir/r4",
]

# Paths excluded from audit logging
EXCLUDED_PATHS = [
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/static",
    "/favicon.ico",
]


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware for GDPR-compliant audit logging.

    Captures all access to sensitive clinical data including:
    - Who accessed the data (user_id, email, role)
    - What was accessed (resource type, resource ID)
    - When (timestamp)
    - From where (IP address, user agent)
    - What action was performed (READ, CREATE, UPDATE, DELETE)
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and log audit trail."""
        # Generate unique request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Skip excluded paths
        if self._should_skip_path(request.url.path):
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        # Record start time
        start_time = datetime.now(timezone.utc)

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = int(
            (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        )

        # Log audit for sensitive paths
        if self._should_audit_path(request.url.path):
            await self._log_audit(request, response, duration_ms)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response

    def _should_skip_path(self, path: str) -> bool:
        """Check if path should be skipped entirely."""
        return any(path.startswith(excluded) for excluded in EXCLUDED_PATHS)

    def _should_audit_path(self, path: str) -> bool:
        """Check if path should be audited."""
        return any(path.startswith(audited) for audited in AUDITED_PATHS)

    async def _log_audit(
        self,
        request: Request,
        response: Response,
        duration_ms: int,
    ) -> None:
        """
        Log audit entry to database.

        In production, this writes to the security_audit table.
        For now, we log to the application logger.
        """
        # Extract user info from request state (set by auth middleware)
        user = getattr(request.state, "user", None)

        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": getattr(request.state, "request_id", None),
            # User information
            "user_id": user.sub if user else None,
            "user_email": user.email if user else None,
            "user_role": user.role if user else None,
            "clinic_id": user.clinic_id if user else None,
            # Request context
            "ip_address": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", "")[:500],
            "session_id": request.cookies.get("session_id"),
            # Action details
            "action": self._map_method_to_action(request.method),
            "resource_type": self._extract_resource_type(request.url.path),
            "resource_id": self._extract_resource_id(request.url.path),
            "request_path": str(request.url.path),
            "request_method": request.method,
            "query_params": dict(request.query_params) if request.query_params else None,
            # Response
            "response_status": response.status_code,
            "duration_ms": duration_ms,
        }

        # Log to application logger (will be replaced with DB insert)
        logger.info(
            f"AUDIT: {audit_entry['action']} {audit_entry['resource_type']} "
            f"by user {audit_entry['user_id']} from {audit_entry['ip_address']} "
            f"- {audit_entry['response_status']} in {duration_ms}ms"
        )

        # TODO: Insert into security_audit table asynchronously
        # await self._insert_audit_log(audit_entry)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, handling proxies."""
        # Check X-Forwarded-For header (set by reverse proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain (original client)
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        if request.client:
            return request.client.host

        return "unknown"

    @staticmethod
    def _map_method_to_action(method: str) -> str:
        """Map HTTP method to audit action."""
        mapping = {
            "GET": "READ",
            "HEAD": "READ",
            "POST": "CREATE",
            "PUT": "UPDATE",
            "PATCH": "UPDATE",
            "DELETE": "DELETE",
        }
        return mapping.get(method.upper(), "UNKNOWN")

    @staticmethod
    def _extract_resource_type(path: str) -> str:
        """Extract resource type from URL path."""
        # Remove leading slash and split
        parts = path.strip("/").split("/")

        # Handle API paths: /api/patients/123 -> patients
        if len(parts) >= 2 and parts[0] == "api":
            return parts[1]

        # Handle FHIR paths: /fhir/r4/Patient/123 -> Patient
        if len(parts) >= 3 and parts[0] == "fhir":
            return parts[2]

        return parts[0] if parts else "unknown"

    @staticmethod
    def _extract_resource_id(path: str) -> Optional[str]:
        """Extract resource ID from URL path."""
        parts = path.strip("/").split("/")

        # /api/patients/123 -> 123
        if len(parts) >= 3 and parts[0] == "api":
            # Check if the third part looks like an ID
            potential_id = parts[2]
            if potential_id.isdigit() or len(potential_id) == 36:  # UUID
                return potential_id

        # /fhir/r4/Patient/123 -> 123
        if len(parts) >= 4 and parts[0] == "fhir":
            return parts[3]

        return None


async def log_cdss_calculation(
    calculation_type: str,
    patient_id: Optional[int],
    input_params: dict,
    result: dict,
    user_id: int,
    clinic_id: int,
) -> None:
    """
    Log CDSS calculation to audit trail.

    All risk score calculations must be logged for clinical audit.

    Args:
        calculation_type: Type of calculation (GRACE, CHA2DS2-VASc, etc.)
        patient_id: Patient ID if linked to a patient
        input_params: Input parameters used
        result: Calculation result
        user_id: ID of clinician who ran calculation
        clinic_id: Clinic ID for tenant context
    """
    logger.info(
        f"CDSS_AUDIT: {calculation_type} calculation by user {user_id} "
        f"for patient {patient_id} - Score: {result.get('total_score', 'N/A')} "
        f"Risk: {result.get('risk_category', 'N/A')}"
    )

    # TODO: Insert into cdss_audit_log table
    # audit_entry = {
    #     "calculation_type": calculation_type,
    #     "patient_id": patient_id,
    #     "input_parameters": input_params,
    #     "calculated_score": result.get("total_score"),
    #     "risk_category": result.get("risk_category"),
    #     "recommendation": result.get("recommendation"),
    #     "clinician_id": user_id,
    #     "clinic_id": clinic_id,
    #     "timestamp": datetime.now(timezone.utc),
    # }


async def log_note_access(
    note_id: int,
    action: str,
    user_id: int,
    user_email: str,
    ip_address: str,
    version_viewed: Optional[int] = None,
    attachment_id: Optional[int] = None,
) -> None:
    """
    Log clinical note access for GDPR compliance.

    Args:
        note_id: ID of the note accessed
        action: Action performed (VIEW, EDIT, DOWNLOAD_ATTACHMENT)
        user_id: ID of user who accessed the note
        user_email: Email of user
        ip_address: Client IP address
        version_viewed: Version number if viewing specific version
        attachment_id: Attachment ID if downloading attachment
    """
    logger.info(
        f"NOTE_AUDIT: {action} note {note_id} "
        f"(version: {version_viewed}, attachment: {attachment_id}) "
        f"by user {user_id} ({user_email}) from {ip_address}"
    )

    # TODO: Insert into note_access_log table
