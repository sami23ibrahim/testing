"""Send error notification emails to configured superusers."""

from __future__ import annotations
import smtplib
import logging
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from app.config import settings

logger = logging.getLogger(__name__)


def _get_recipients() -> list[str]:
    """Return the list of emails to notify, from .env or PocketBase."""
    raw = settings.error_notify_emails.strip()
    if not raw:
        return []
    return [e.strip() for e in raw.split(",") if e.strip()]


def send_error_email(
    error: Exception,
    context: str = "",
    user_email: str = "",
) -> bool:
    """Send an error notification email. Returns True if sent successfully."""
    recipients = _get_recipients()
    if not recipients or not settings.smtp_host:
        logger.debug("Email notification skipped: no SMTP config or recipients")
        return False

    subject = f"[{settings.bot_name}] Error: {type(error).__name__}"
    tb = traceback.format_exception(type(error), error, error.__traceback__)

    body = f"""
<h2 style="color:#ef4444">Error in {settings.bot_name}</h2>
<table style="font-family:monospace; font-size:13px; border-collapse:collapse;">
  <tr><td style="padding:4px 12px 4px 0; color:#888;">Time</td><td>{datetime.now(timezone.utc).isoformat()}</td></tr>
  <tr><td style="padding:4px 12px 4px 0; color:#888;">Error</td><td><strong>{type(error).__name__}: {error}</strong></td></tr>
  <tr><td style="padding:4px 12px 4px 0; color:#888;">Context</td><td>{context or 'N/A'}</td></tr>
  <tr><td style="padding:4px 12px 4px 0; color:#888;">User</td><td>{user_email or 'N/A'}</td></tr>
  <tr><td style="padding:4px 12px 4px 0; color:#888;">Domain</td><td>{settings.domain}</td></tr>
</table>
<h3 style="margin-top:16px">Traceback</h3>
<pre style="background:#1a1b23; color:#e4e4e7; padding:12px; border-radius:8px; overflow-x:auto; font-size:12px;">{''.join(tb)}</pre>
""".strip()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(body, "html"))

    try:
        if settings.smtp_tls:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)

        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)

        server.sendmail(msg["From"], recipients, msg.as_string())
        server.quit()
        logger.info(f"Error notification sent to {recipients}")
        return True
    except Exception as mail_err:
        logger.error(f"Failed to send error email: {mail_err}")
        return False
