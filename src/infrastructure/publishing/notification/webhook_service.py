"""
Webhook notification service for releases.
"""

import httpx
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for sending webhook notifications."""

    def __init__(self, timeout: int = 10):
        """
        Initialize webhook service.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout

    async def send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Send webhook notification.

        Args:
            url: Webhook URL
            payload: Payload dictionary
            headers: Optional custom headers

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            request_headers = {"Content-Type": "application/json"}
            if headers:
                request_headers.update(headers)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=request_headers,
                )
                response.raise_for_status()

            logger.info(f"Webhook sent successfully to {url}")
            return True

        except Exception as e:
            logger.error(f"Failed to send webhook to {url}: {e}")
            return False

    async def send_release_webhook(
        self,
        webhook_urls: List[str],
        version: str,
        doi: str,
        release_notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """
        Send release notification webhooks.

        Args:
            webhook_urls: List of webhook URLs
            version: Release version
            doi: DOI for the release
            release_notes: Optional release notes
            metadata: Optional additional metadata

        Returns:
            Dictionary mapping webhook URLs to success status
        """
        payload = {
            "event": "release.published",
            "package": "MED13 Resource Library",
            "version": version,
            "doi": doi,
            "doi_url": f"https://doi.org/{doi}",
            "release_notes": release_notes,
            "metadata": metadata or {},
        }

        results = {}
        for url in webhook_urls:
            success = await self.send_webhook(url, payload)
            results[url] = success

        return results
