"""
Unit tests for DOI service.
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.infrastructure.publishing.zenodo.client import ZenodoClient
from src.infrastructure.publishing.zenodo.doi_service import DOIService


class TestDOIService:
    """Test DOI service functionality."""

    def test_create_service(self):
        """Test creating DOIService instance."""
        client = ZenodoClient(access_token="test_token")
        service = DOIService(client)
        assert service.client == client

    @pytest.mark.asyncio
    async def test_mint_doi(self):
        """Test minting DOI."""
        client = ZenodoClient(access_token="test_token")
        service = DOIService(client)

        mock_published = {
            "id": 12345,
            "doi": "10.1234/test.12345",
            "links": {"html": "https://zenodo.org/record/12345"},
        }

        with patch.object(
            client, "publish_deposit", new_callable=AsyncMock
        ) as mock_publish:
            mock_publish.return_value = mock_published

            result = await service.mint_doi(12345)

            assert result["doi"] == "10.1234/test.12345"
            assert result["deposit_id"] == 12345

    def test_format_doi_url(self):
        """Test formatting DOI URL."""
        client = ZenodoClient(access_token="test_token")
        service = DOIService(client)

        # DOI without URL prefix
        url = service.format_doi_url("10.1234/test.12345")
        assert url == "https://doi.org/10.1234/test.12345"

        # DOI with URL prefix
        url = service.format_doi_url("https://doi.org/10.1234/test.12345")
        assert url == "https://doi.org/10.1234/test.12345"
