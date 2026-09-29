"""
Email Notification Service
Sends email alerts when a new job match is found.
Uses SMTP (Gmail / any SMTP provider).
"""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_job_match_notification(user, job, score: float):
    """Send an email to notify a user of a new high-scoring job match."""
    subject = f"🎯 New Job Match: {job.title} at {job.company} ({int(score * 100)}% match)"
    body = f"""
Hi {user.full_name},

Good news! We found a new job that matches your profile:

🏢 Company:  {job.company}
💼 Role:     {job.title}
📍 Location: {job.location or 'Not specified'}
🔗 Link:     {job.source_url}
⭐ Match:    {int(score * 100)}%

Log in to your JobAIgent dashboard to review and apply:
{settings.FRONTEND_URL}/dashboard

Best,
The JobAIgent Team
"""
    try:
        _send_email(to_email=user.email, subject=subject, body=body)
        logger.info(f"Notification sent to {user.email} for job {job.id}")
    except Exception as e:
        logger.error(f"Failed to send notification to {user.email}: {e}")


def _send_email(to_email: str, subject: str, body: str):
    """Send a plain-text email via SMTP."""
    if not settings.SMTP_USER:
        logger.warning("SMTP not configured — skipping email send")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
