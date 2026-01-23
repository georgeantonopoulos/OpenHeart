"""
Email service for OpenHeart Cyprus.

Sends transactional emails (password reset, invitations).
In development mode (no SMTP credentials), emails are logged to console.
"""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


def _is_dev_mode() -> bool:
    """Check if email should be logged instead of sent."""
    return settings.environment == "development" or not settings.smtp_username


async def _send_smtp(
    to: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> bool:
    """Send email via SMTP (production mode)."""
    try:
        import aiosmtplib

        message = MIMEMultipart("alternative")
        message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        message["To"] = to
        message["Subject"] = subject

        if text_body:
            message.attach(MIMEText(text_body, "plain"))
        message.attach(MIMEText(html_body, "html"))

        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            use_tls=settings.smtp_use_tls,
        )
        logger.info(f"Email sent to {to}: {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False


async def _log_email(to: str, subject: str, body: str) -> bool:
    """Log email content to console (development mode)."""
    logger.info(
        f"\n{'=' * 60}\n"
        f"  EMAIL (dev mode - not sent)\n"
        f"  To: {to}\n"
        f"  Subject: {subject}\n"
        f"{'=' * 60}\n"
        f"{body}\n"
        f"{'=' * 60}"
    )
    return True


async def send_email(
    to: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> bool:
    """
    Send an email. Routes to SMTP or console log based on environment.

    Args:
        to: Recipient email address
        subject: Email subject line
        html_body: HTML email body
        text_body: Optional plain text fallback

    Returns:
        True if sent/logged successfully
    """
    if _is_dev_mode():
        return await _log_email(to, subject, html_body)
    return await _send_smtp(to, subject, html_body, text_body)


async def send_password_reset_email(
    to: str,
    reset_token: str,
    reset_url: Optional[str] = None,
) -> bool:
    """
    Send password reset email with a secure link.

    Args:
        to: Recipient email
        reset_token: The reset token
        reset_url: Full reset URL (auto-generated from settings if not provided)

    Returns:
        True if sent successfully
    """
    if not reset_url:
        reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"

    subject = "OpenHeart Cyprus - Password Reset Request"
    html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #1E293B;">Password Reset Request</h2>
    <p>You requested a password reset for your OpenHeart Cyprus account.</p>
    <p>Click the button below to reset your password. This link expires in <strong>1 hour</strong>.</p>
    <p style="text-align: center; margin: 30px 0;">
        <a href="{reset_url}"
           style="background-color: #1E293B; color: white; padding: 12px 24px;
                  text-decoration: none; border-radius: 6px; font-weight: bold;">
            Reset Password
        </a>
    </p>
    <p style="font-size: 12px; color: #666;">
        If you did not request this reset, please ignore this email.
        Your password will remain unchanged.
    </p>
    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;" />
    <p style="font-size: 11px; color: #999;">
        OpenHeart Cyprus - Cardiology EMR<br/>
        This is an automated message, please do not reply.
    </p>
</body>
</html>"""
    text_body = (
        f"Password Reset Request\n\n"
        f"You requested a password reset for your OpenHeart Cyprus account.\n\n"
        f"Reset your password: {reset_url}\n\n"
        f"This link expires in 1 hour.\n"
        f"If you did not request this reset, please ignore this email."
    )

    return await send_email(to, subject, html_body, text_body)


async def send_invitation_email(
    to: str,
    invite_token: str,
    inviter_name: str = "An administrator",
    role: str = "",
    clinic_name: str = "",
    invite_url: Optional[str] = None,
) -> bool:
    """
    Send user invitation email.

    Args:
        to: Invitee email address
        invite_token: Invitation token
        inviter_name: Name of the person who sent the invitation
        role: Assigned role for the invitee
        clinic_name: Clinic name
        invite_url: Full invitation URL (auto-generated if not provided)

    Returns:
        True if sent successfully
    """
    if not invite_url:
        invite_url = f"{settings.frontend_url}/invite/{invite_token}"

    subject = "OpenHeart Cyprus - You've Been Invited"
    html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #1E293B;">You've Been Invited to OpenHeart Cyprus</h2>
    <p><strong>{inviter_name}</strong> has invited you to join
       <strong>{clinic_name or 'their clinic'}</strong>
       as a <strong>{role or 'team member'}</strong>.</p>
    <p>Click the button below to create your account. This invitation expires in <strong>7 days</strong>.</p>
    <p style="text-align: center; margin: 30px 0;">
        <a href="{invite_url}"
           style="background-color: #1E293B; color: white; padding: 12px 24px;
                  text-decoration: none; border-radius: 6px; font-weight: bold;">
            Accept Invitation
        </a>
    </p>
    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;" />
    <p style="font-size: 11px; color: #999;">
        OpenHeart Cyprus - Cardiology EMR<br/>
        This is an automated message, please do not reply.
    </p>
</body>
</html>"""

    return await send_email(to, subject, html_body)
