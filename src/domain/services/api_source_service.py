"""
Domain service for API source operations.

Handles API connections, authentication, rate limiting, and data retrieval
for REST API data sources in the Data Sources module.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx

from pydantic import BaseModel

from src.domain.entities.user_data_source import SourceConfiguration


class APIRequestResult(BaseModel):
    """Result of an API request operation."""

    success: bool
    data: Optional[Any] = None
    record_count: int = 0
    response_time_ms: float = 0.0
    status_code: Optional[int] = None
    errors: List[str] = []
    metadata: Dict[str, Any] = {}


class APIConnectionTest(BaseModel):
    """Result of API connection testing."""

    success: bool
    response_time_ms: float = 0.0
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    response_headers: Dict[str, str] = {}
    sample_data: Optional[Any] = None


class APISourceService:
    """
    Domain service for handling API data sources.

    Provides connection testing, data retrieval, authentication handling,
    and rate limiting for REST API data sources.
    """

    def __init__(self, timeout_seconds: int = 30, max_retries: int = 3):
        """
        Initialize the API source service.

        Args:
            timeout_seconds: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

        # Supported authentication methods
        self.auth_methods = {
            "none": self._auth_none,
            "bearer": self._auth_bearer,
            "basic": self._auth_basic,
            "api_key": self._auth_api_key,
            "oauth2": self._auth_oauth2,
        }

    async def test_connection(
        self, configuration: SourceConfiguration
    ) -> APIConnectionTest:
        """
        Test connection to an API endpoint.

        Args:
            configuration: Source configuration with API details

        Returns:
            Connection test results
        """
        if not configuration.url:
            return APIConnectionTest(success=False, error_message="No URL provided")

        start_time = datetime.now(timezone.utc)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                # Prepare request
                headers = self._prepare_headers(configuration)
                auth_headers = self._prepare_auth(configuration)
                # Merge auth headers if present
                if auth_headers:
                    headers.update(auth_headers)

                # Make test request (HEAD if available, otherwise GET with limit)
                method = "HEAD"
                url = configuration.url
                params = {}

                # Add limit parameter to avoid large responses
                if "limit" in configuration.metadata:
                    params["limit"] = min(int(configuration.metadata["limit"]), 1)
                else:
                    params["limit"] = 1

                response = await client.request(
                    method=method, url=url, headers=headers, params=params
                )

                response_time = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000

                # If HEAD not allowed, try GET
                if response.status_code == 405:  # Method not allowed
                    response = await client.get(url=url, headers=headers, params=params)
                    response_time = (
                        datetime.now(timezone.utc) - start_time
                    ).total_seconds() * 1000

                success = 200 <= response.status_code < 300

                sample_data = None
                if success and response.headers.get("content-type", "").startswith(
                    "application/json"
                ):
                    try:
                        sample_data = response.json()
                    except Exception:
                        pass

                return APIConnectionTest(
                    success=success,
                    response_time_ms=response_time,
                    status_code=response.status_code,
                    error_message=(
                        None
                        if success
                        else f"HTTP {response.status_code}: {response.text[:200]}"
                    ),
                    response_headers=dict(response.headers),
                    sample_data=sample_data,
                )

        except Exception as e:
            response_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            return APIConnectionTest(
                success=False, response_time_ms=response_time, error_message=str(e)
            )

    async def fetch_data(
        self, configuration: SourceConfiguration, **kwargs: Any
    ) -> APIRequestResult:
        """
        Fetch data from an API endpoint.

        Args:
            configuration: Source configuration
            **kwargs: Additional parameters for the request

        Returns:
            API request results with fetched data
        """
        if not configuration.url:
            return APIRequestResult(success=False, errors=["No URL provided"])

        start_time = datetime.now(timezone.utc)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                # Prepare request components
                headers = self._prepare_headers(configuration)
                auth_headers = self._prepare_auth(configuration)
                # Merge auth headers if present
                if auth_headers:
                    headers.update(auth_headers)

                # Build request parameters
                url = configuration.url
                method = configuration.metadata.get("method", "GET").upper()
                params = dict(configuration.metadata.get("query_params", {}))
                params.update(kwargs)

                # Rate limiting
                await self._apply_rate_limiting(configuration)

                # Make request with retries
                response = await self._make_request_with_retries(
                    client, method, url, headers, params
                )

                response_time = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000

                if not response:
                    return APIRequestResult(
                        success=False,
                        response_time_ms=response_time,
                        errors=["Request failed after retries"],
                    )

                success = 200 <= response.status_code < 300

                data = None
                record_count = 0
                errors = []

                if success:
                    try:
                        data = response.json()
                        record_count = self._count_records(data)
                    except Exception as e:
                        errors.append(f"Failed to parse response: {str(e)}")
                        data = response.text[:1000]  # Include some raw response
                else:
                    errors.append(f"HTTP {response.status_code}: {response.text[:200]}")

                return APIRequestResult(
                    success=success,
                    data=data,
                    record_count=record_count,
                    response_time_ms=response_time,
                    status_code=response.status_code,
                    errors=errors,
                    metadata={
                        "response_headers": dict(response.headers),
                        "request_url": str(response.url),
                        "request_method": method,
                    },
                )

        except Exception as e:
            response_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            return APIRequestResult(
                success=False, response_time_ms=response_time, errors=[str(e)]
            )

    def _prepare_headers(self, configuration: SourceConfiguration) -> Dict[str, str]:
        """Prepare HTTP headers for the request."""
        headers = {
            "User-Agent": "MED13-Data-Source/1.0",
            "Accept": "application/json, text/plain, */*",
        }

        # Add custom headers from configuration
        custom_headers = configuration.metadata.get("headers", {})
        headers.update(custom_headers)

        return headers

    def _prepare_auth(self, configuration: SourceConfiguration) -> Optional[Any]:
        """Prepare authentication for the request."""
        auth_config = configuration.auth_credentials or {}
        auth_type = configuration.auth_type or "none"

        if auth_type in self.auth_methods:
            return self.auth_methods[auth_type](auth_config)
        else:
            return None

    def _auth_none(self, config: Dict[str, Any]) -> None:
        """No authentication."""
        return None

    def _auth_bearer(self, config: Dict[str, Any]) -> Optional[Any]:
        """Bearer token authentication."""
        token = config.get("token", "")
        if token:
            # Use a simple dict approach to avoid httpx typing issues
            return {"Authorization": f"Bearer {token}"}
        return None

    def _auth_basic(self, config: Dict[str, Any]) -> Optional[Any]:
        """Basic HTTP authentication."""
        username = config.get("username", "")
        password = config.get("password", "")
        if username and password:
            import base64

            auth_string = base64.b64encode(f"{username}:{password}".encode()).decode()
            return {"Authorization": f"Basic {auth_string}"}
        return None

    def _auth_api_key(self, config: Dict[str, Any]) -> None:
        """API key authentication (added to headers)."""
        # This is handled in _prepare_headers
        return None

    def _auth_oauth2(self, config: Dict[str, Any]) -> Optional[Any]:
        """OAuth2 authentication (simplified - would need token refresh logic)."""
        token = config.get("access_token", "")
        if token:
            return {"Authorization": f"Bearer {token}"}
        return None

    async def _apply_rate_limiting(self, configuration: SourceConfiguration) -> None:
        """Apply rate limiting before making requests."""
        rate_limit = configuration.requests_per_minute or 60
        delay_seconds = 60.0 / rate_limit

        # Simple rate limiting - in production, use a more sophisticated approach
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)

    async def _make_request_with_retries(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Dict[str, Any],
    ) -> Optional[httpx.Response]:
        """Make HTTP request with retry logic."""
        for attempt in range(self.max_retries):
            try:
                response = await client.request(
                    method=method, url=url, headers=headers, params=params
                )
                return response

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt == self.max_retries - 1:
                    raise e
                await asyncio.sleep(2**attempt)  # Exponential backoff

        return None

    def _count_records(self, data: Any) -> int:
        """Count the number of records in API response data."""
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            # Look for common array fields
            for key in ["data", "results", "records", "items"]:
                if key in data and isinstance(data[key], list):
                    return len(data[key])
            # Check if it's a single record
            return 1
        else:
            return 0

    def validate_configuration(self, configuration: SourceConfiguration) -> List[str]:
        """
        Validate API source configuration.

        Args:
            configuration: Configuration to validate

        Returns:
            List of validation error messages
        """
        errors = []

        # Check required fields
        if not configuration.url:
            errors.append("API URL is required")

        # Validate URL format
        if configuration.url:
            if not configuration.url.startswith(("http://", "https://")):
                errors.append("URL must start with http:// or https://")

        # Validate authentication
        if configuration.auth_type and configuration.auth_type not in self.auth_methods:
            errors.append(f"Unsupported authentication type: {configuration.auth_type}")

        # Validate auth credentials based on type
        if configuration.auth_type and configuration.auth_type != "none":
            required_fields = self._get_auth_required_fields(configuration.auth_type)
            missing_fields = []
            for field in required_fields:
                if (
                    not configuration.auth_credentials
                    or field not in configuration.auth_credentials
                ):
                    missing_fields.append(field)

            if missing_fields:
                errors.append(
                    f"Missing authentication fields for {configuration.auth_type}: {missing_fields}"
                )

        # Validate rate limiting
        if configuration.requests_per_minute:
            if (
                configuration.requests_per_minute < 1
                or configuration.requests_per_minute > 1000
            ):
                errors.append("Requests per minute must be between 1 and 1000")

        return errors

    def _get_auth_required_fields(self, auth_type: str) -> List[str]:
        """Get required fields for authentication type."""
        auth_fields = {
            "bearer": ["token"],
            "basic": ["username", "password"],
            "api_key": ["key"],
            "oauth2": ["access_token"],  # Simplified
        }
        return auth_fields.get(auth_type, [])
