"""
Unit tests for email service.
"""

from unittest.mock import MagicMock, patch

from src.infrastructure.publishing.notification.email_service import EmailService


class TestEmailService:
    """Test email service functionality."""

    def test_create_service(self):
        """Test creating EmailService instance."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user",
            smtp_password="pass",
        )
        assert service.smtp_host == "smtp.example.com"
        assert service.smtp_port == 587

    @patch("smtplib.SMTP")
    def test_send_notification(self, mock_smtp):
        """Test sending email notification."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_user="user",
            smtp_password="pass",
        )

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        success = service.send_notification(
            to_emails=["test@example.com"],
            subject="Test",
            body="Test body",
        )

        assert success is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user", "pass")
        mock_server.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_release_notification(self, mock_smtp):
        """Test sending release notification."""
        service = EmailService(smtp_host="smtp.example.com")

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        success = service.send_release_notification(
            to_emails=["test@example.com"],
            version="1.0.0",
            doi="10.1234/test.12345",
            release_notes="Test release",
        )

        assert success is True
        mock_server.send_message.assert_called_once()
