"""
Unit tests for webhook service.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.infrastructure.publishing.notification.webhook_service import WebhookService


class TestWebhookService:
    """Test webhook service functionality."""

    def test_create_service(self):
        """Test creating WebhookService instance."""
        service = WebhookService(timeout=15)
        assert service.timeout == 15

    @pytest.mark.asyncio
    async def test_send_webhook(self):
        """Test sending webhook."""
        service = WebhookService()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)

            success = await service.send_webhook(
                url="https://example.com/webhook",
                payload={"test": "data"},
            )

            assert success is True
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_release_webhook(self):
        """Test sending release webhook."""
        service = WebhookService()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)

            results = await service.send_release_webhook(
                webhook_urls=["https://example.com/webhook"],
                version="1.0.0",
                doi="10.1234/test.12345",
            )

            assert results["https://example.com/webhook"] is True
