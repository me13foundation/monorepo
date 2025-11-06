"""
DOI minting service for Zenodo deposits.
"""

import logging
from typing import Any, cast

from .client import ZenodoClient

logger = logging.getLogger(__name__)


class DOIService:
    """Service for minting DOIs through Zenodo."""

    def __init__(self, client: ZenodoClient):
        """
        Initialize DOI service.

        Args:
            client: ZenodoClient instance
        """
        self.client = client

    async def mint_doi(
        self,
        deposit_id: int,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Mint DOI for a deposit by publishing it.

        Args:
            deposit_id: Deposit ID
            metadata: Optional metadata to update before publishing

        Returns:
            Published deposit with DOI information
        """
        # Update metadata if provided
        if metadata:
            await self.client.update_deposit(deposit_id, metadata)

        # Publish deposit (this mints the DOI)
        published_deposit = await self.client.publish_deposit(deposit_id)

        # Extract DOI (cast to dict for compatibility)
        doi = self.client.extract_doi(cast("dict[str, Any]", published_deposit))

        if not doi:
            message = "DOI not found in published deposit response"
            raise ValueError(message)

        logger.info("DOI minted successfully: %s", doi)

        published_dict = cast("dict[str, Any]", published_deposit)
        return {
            "deposit_id": deposit_id,
            "doi": doi,
            "url": published_dict.get("links", {}).get("html", ""),
            "deposit": published_deposit,
        }

    async def get_doi(self, deposit_id: int) -> str | None:
        """
        Get DOI for an existing deposit.

        Args:
            deposit_id: Deposit ID

        Returns:
            DOI string or None
        """
        deposit = await self.client.get_deposit(deposit_id)
        return self.client.extract_doi(deposit)

    def format_doi_url(self, doi: str) -> str:
        """
        Format DOI as URL.

        Args:
            doi: DOI string

        Returns:
            DOI URL
        """
        if doi.startswith("http"):
            return doi
        return f"https://doi.org/{doi}"
