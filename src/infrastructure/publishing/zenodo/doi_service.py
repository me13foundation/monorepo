"""
DOI minting service for Zenodo deposits.
"""

from typing import Dict, Any, Optional, cast
import logging

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
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
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
        doi = self.client.extract_doi(cast(Dict[str, Any], published_deposit))

        if not doi:
            raise ValueError("DOI not found in published deposit response")

        logger.info(f"DOI minted successfully: {doi}")

        published_dict = cast(Dict[str, Any], published_deposit)
        return {
            "deposit_id": deposit_id,
            "doi": doi,
            "url": published_dict.get("links", {}).get("html", ""),
            "deposit": published_deposit,
        }

    async def get_doi(self, deposit_id: int) -> Optional[str]:
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
