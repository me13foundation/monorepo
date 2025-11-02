"""
Email notification service for releases.
"""

from typing import List, Optional
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        use_tls: bool = True,
    ):
        """
        Initialize email service.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username (optional)
            smtp_password: SMTP password (optional)
            from_email: From email address
            use_tls: Whether to use TLS
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email or "noreply@med13foundation.org"
        self.use_tls = use_tls

    def send_notification(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> bool:
        """
        Send email notification.

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = ", ".join(to_emails)

            # Add plain text part
            text_part = MIMEText(body, "plain")
            msg.attach(text_part)

            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, "html")
                msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)

                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_emails}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_release_notification(
        self,
        to_emails: List[str],
        version: str,
        doi: str,
        release_notes: Optional[str] = None,
    ) -> bool:
        """
        Send release notification email.

        Args:
            to_emails: List of recipient email addresses
            version: Release version
            doi: DOI for the release
            release_notes: Optional release notes

        Returns:
            True if sent successfully, False otherwise
        """
        subject = f"New Release: MED13 Resource Library v{version}"

        body = f"""
MED13 Resource Library Release Notification

Version: {version}
DOI: {doi}

{release_notes or "A new release of the MED13 Resource Library is now available."}

Access the release: https://doi.org/{doi}

---
MED13 Foundation
        """.strip()

        html_body = f"""
        <html>
        <body>
        <h2>MED13 Resource Library Release Notification</h2>
        <p><strong>Version:</strong> {version}</p>
        <p><strong>DOI:</strong> <a href="https://doi.org/{doi}">{doi}</a></p>
        <p>{release_notes or "A new release of the MED13 Resource Library is now available."}</p>
        <p><a href="https://doi.org/{doi}">Access the release</a></p>
        <hr>
        <p><em>MED13 Foundation</em></p>
        </body>
        </html>
        """

        return self.send_notification(to_emails, subject, body, html_body)
