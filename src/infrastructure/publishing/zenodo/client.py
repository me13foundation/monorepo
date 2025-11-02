"""
Zenodo API client for publishing packages.

Provides integration with Zenodo API for depositing research data packages
and minting DOIs.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import httpx

logger = logging.getLogger(__name__)


class ZenodoClient:
    """Client for interacting with Zenodo API."""

    # API endpoints
    SANDBOX_URL = "https://sandbox.zenodo.org/api"
    PRODUCTION_URL = "https://zenodo.org/api"

    def __init__(
        self,
        access_token: str,
        sandbox: bool = True,
        timeout: int = 30,
    ):
        """
        Initialize Zenodo client.

        Args:
            access_token: Zenodo API access token
            sandbox: Whether to use sandbox environment (default: True)
            timeout: Request timeout in seconds
        """
        self.access_token = access_token
        self.base_url = self.SANDBOX_URL if sandbox else self.PRODUCTION_URL
        self.timeout = timeout
        self.sandbox = sandbox

        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def create_deposit(
        self,
        metadata: Dict[str, Any],
        files: Optional[List[Path]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new deposit on Zenodo.

        Args:
            metadata: Deposit metadata dictionary
            files: Optional list of file paths to upload

        Returns:
            Deposit information dictionary
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Create deposit
            create_url = f"{self.base_url}/deposit/depositions"
            response = await client.post(
                create_url, headers=self.headers, json=metadata
            )
            response.raise_for_status()
            deposit = cast(Dict[str, Any], response.json())

            bucket_url = deposit["links"]["bucket"]

            # Upload files if provided
            if files:
                await self._upload_files(client, bucket_url, files)

            return deposit

    async def _upload_files(
        self,
        client: httpx.AsyncClient,
        bucket_url: str,
        files: List[Path],
    ) -> None:
        """
        Upload files to Zenodo deposit bucket.

        Args:
            client: HTTP client instance
            bucket_url: Zenodo bucket URL
            files: List of file paths to upload
        """
        for file_path in files:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                continue

            upload_url = f"{bucket_url}/{file_path.name}"

            with open(file_path, "rb") as f:
                upload_headers = {"Authorization": f"Bearer {self.access_token}"}
                response = await client.put(
                    upload_url,
                    headers=upload_headers,
                    content=f.read(),
                )
                response.raise_for_status()

    async def publish_deposit(self, deposit_id: int) -> Dict[str, Any]:
        """
        Publish a deposit (mint DOI).

        Args:
            deposit_id: Deposit ID

        Returns:
            Published deposit information with DOI
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            publish_url = (
                f"{self.base_url}/deposit/depositions/{deposit_id}/actions/publish"
            )
            response = await client.post(publish_url, headers=self.headers)
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())

    async def get_deposit(self, deposit_id: int) -> Dict[str, Any]:
        """
        Get deposit information.

        Args:
            deposit_id: Deposit ID

        Returns:
            Deposit information dictionary
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"{self.base_url}/deposit/depositions/{deposit_id}"
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())

    async def update_deposit(
        self, deposit_id: int, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update deposit metadata.

        Args:
            deposit_id: Deposit ID
            metadata: Updated metadata dictionary

        Returns:
            Updated deposit information
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"{self.base_url}/deposit/depositions/{deposit_id}"
            response = await client.put(url, headers=self.headers, json=metadata)
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())

    def extract_doi(self, deposit: Dict[str, Any]) -> Optional[str]:
        """
        Extract DOI from deposit response.

        Args:
            deposit: Deposit information dictionary

        Returns:
            DOI string or None
        """
        doi_value = deposit.get("doi")
        if isinstance(doi_value, str):
            return doi_value

        metadata = deposit.get("metadata")
        if isinstance(metadata, dict):
            metadata_doi = metadata.get("doi")
            if isinstance(metadata_doi, str):
                return metadata_doi

        return None
