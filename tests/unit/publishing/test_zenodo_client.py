"""
Unit tests for Zenodo client.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.infrastructure.publishing.zenodo.client import ZenodoClient


class TestZenodoClient:
    """Test Zenodo client functionality."""

    def test_create_client(self):
        """Test creating ZenodoClient instance."""
        client = ZenodoClient(access_token="test_token", sandbox=True)
        assert client.sandbox is True
        assert client.base_url == ZenodoClient.SANDBOX_URL
        assert "Bearer test_token" in client.headers["Authorization"]

    def test_create_client_production(self):
        """Test creating production ZenodoClient."""
        client = ZenodoClient(access_token="test_token", sandbox=False)
        assert client.sandbox is False
        assert client.base_url == ZenodoClient.PRODUCTION_URL

    @pytest.mark.asyncio
    async def test_create_deposit(self):
        """Test creating a deposit."""
        client = ZenodoClient(access_token="test_token", sandbox=True)
        metadata = {"metadata": {"title": "Test Deposit"}}

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 12345,
            "links": {"bucket": "https://zenodo.org/api/files/bucket/123"},
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)

            deposit = await client.create_deposit(metadata)

            assert deposit["id"] == 12345
            assert "links" in deposit

    @pytest.mark.asyncio
    async def test_publish_deposit(self):
        """Test publishing a deposit."""
        client = ZenodoClient(access_token="test_token", sandbox=True)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 12345,
            "doi": "10.1234/test.12345",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)

            result = await client.publish_deposit(12345)

            assert result["id"] == 12345
            assert result["doi"] == "10.1234/test.12345"

    def test_extract_doi(self):
        """Test extracting DOI from deposit."""
        client = ZenodoClient(access_token="test_token")

        # DOI in metadata
        deposit1 = {"metadata": {"doi": "10.1234/test.12345"}}
        assert client.extract_doi(deposit1) == "10.1234/test.12345"

        # DOI at top level
        deposit2 = {"doi": "10.1234/test.12345"}
        assert client.extract_doi(deposit2) == "10.1234/test.12345"

        # No DOI
        deposit3 = {}
        assert client.extract_doi(deposit3) is None
