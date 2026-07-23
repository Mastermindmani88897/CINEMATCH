"""Email service for verification and password reset."""

import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_verification_email(email: str, username: str, token: str):
    """Send email verification link."""
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    subject = "Verify your CineMatch AI account"
    body = f"""
Hi {username},

Welcome to CineMatch AI! Please verify your email address by clicking the link below:

{verify_url}

This link expires in 24 hours.

If you didn't create an account, please ignore this email.

— The CineMatch AI Team
"""
    await _send_email(email, subject, body)


async def send_password_reset_email(email: str, username: str, token: str):
    """Send password reset link."""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    subject = "Reset your CineMatch AI password"
    body = f"""
Hi {username},

You requested a password reset. Click the link below:

{reset_url}

This link expires in 1 hour. If you didn't request this, please ignore this email.

— The CineMatch AI Team
"""
    await _send_email(email, subject, body)


async def _send_email(to_email: str, subject: str, body: str):
    """Internal SMTP sender."""
    if not settings.SMTP_USERNAME:
        logger.warning(f"SMTP not configured. Would send to {to_email}: {subject}")
        return
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart()
        msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAILS_FROM_EMAIL, to_email, msg.as_string())

        logger.info(f"Email sent to {to_email}: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
