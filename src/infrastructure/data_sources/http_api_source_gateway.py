"""
Infrastructure implementation for API source operations.

Uses httpx to execute API requests while conforming to the
domain-level `APISourceGateway` protocol.
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

import httpx

from src.domain.services.api_source_service import (
    APIConnectionTest,
    APIRequestResult,
    APISourceGateway,
)
from src.type_definitions.json_utils import to_json_value

AuthHeaders = dict[str, str]

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.domain.entities.user_data_source import SourceConfiguration
    from src.type_definitions.common import JSONObject, SourceMetadata
else:  # pragma: no cover - runtime compatibility fallback
    SourceConfiguration = Any
    JSONObject = dict[str, Any]
    SourceMetadata = dict[str, Any]
    Callable = Any


class HttpxAPISourceGateway(APISourceGateway):
    """httpx-powered implementation of the API source gateway."""

    def __init__(self, timeout_seconds: int = 30, max_retries: int = 3):
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.auth_methods: dict[str, Callable[[dict[str, Any]], AuthHeaders | None]] = {
            "none": self._auth_none,
            "bearer": self._auth_bearer,
            "basic": self._auth_basic,
            "api_key": self._auth_api_key,
            "oauth2": self._auth_oauth2,
        }

    async def test_connection(
        self,
        configuration: SourceConfiguration,
    ) -> APIConnectionTest:
        if not configuration.url:
            return APIConnectionTest(success=False, error_message="No URL provided")

        start_time = datetime.now(UTC)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                headers = self._prepare_headers(configuration)
                auth_headers = self._prepare_auth(configuration)
                if auth_headers:
                    headers.update(auth_headers)

                params: dict[str, Any] = {}
                metadata = self._metadata(configuration)
                params["limit"] = self._coerce_limit(metadata.get("limit"), default=1)

                response = await client.request(
                    method="HEAD",
                    url=configuration.url,
                    headers=headers,
                    params=params,
                )

                response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000

                method_not_allowed = 405
                if response.status_code == method_not_allowed:
                    response = await client.get(
                        url=configuration.url,
                        headers=headers,
                        params=params,
                    )
                    response_time = (
                        datetime.now(UTC) - start_time
                    ).total_seconds() * 1000

                http_ok = 200
                http_multiple_choices = 300
                success = http_ok <= response.status_code < http_multiple_choices

                sample_data = None
                if success and response.headers.get("content-type", "").startswith(
                    "application/json",
                ):
                    with contextlib.suppress(Exception):
                        sample_data = response.json()

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

        except Exception as exc:  # noqa: BLE001
            response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
            return APIConnectionTest(
                success=False,
                response_time_ms=response_time,
                error_message=str(exc),
            )

    async def fetch_data(
        self,
        configuration: SourceConfiguration,
        request_parameters: JSONObject | None = None,
    ) -> APIRequestResult:
        if not configuration.url:
            return APIRequestResult(success=False, errors=["No URL provided"])

        start_time = datetime.now(UTC)
        params = dict(request_parameters or {})

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                headers = self._prepare_headers(configuration)
                auth_headers = self._prepare_auth(configuration)
                if auth_headers:
                    headers.update(auth_headers)

                metadata = self._metadata(configuration)
                url = configuration.url
                method = metadata.get("method", "GET").upper()
                params.update(dict(metadata.get("query_params", {})))

                await self._apply_rate_limiting(configuration)

                response = await self._make_request_with_retries(
                    client=client,
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                )

                if response is None:
                    return APIRequestResult(
                        success=False,
                        errors=["Failed to receive response after retries"],
                    )

                response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000

                data = None
                if response.headers.get("content-type", "").startswith(
                    "application/json",
                ):
                    data = response.json()

                errors: list[str] = []
                success = response.is_success and data is not None
                if not success:
                    errors.append(
                        f"HTTP {response.status_code}: {response.text[:200]}",
                    )

                metadata_payload = {
                    "request_url": url,
                    "params": params,
                    "method": method,
                    "headers": headers,
                }

                return APIRequestResult(
                    success=success,
                    data=data if success else None,
                    record_count=self._count_records(data),
                    response_time_ms=response_time,
                    status_code=response.status_code,
                    errors=errors,
                    metadata=cast("JSONObject", to_json_value(metadata_payload)),
                )

        except Exception as exc:  # noqa: BLE001
            response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
            return APIRequestResult(
                success=False,
                errors=[str(exc)],
                response_time_ms=response_time,
            )

    def _prepare_headers(self, configuration: SourceConfiguration) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if configuration.metadata and "headers" in configuration.metadata:
            metadata_headers = configuration.metadata["headers"]
            if isinstance(metadata_headers, dict):
                headers.update(
                    {str(key): str(value) for key, value in metadata_headers.items()},
                )

        if configuration.auth_type == "api_key" and configuration.auth_credentials:
            api_key = configuration.auth_credentials.get("key")
            header_name = configuration.auth_credentials.get("header", "X-API-Key")
            if api_key:
                headers[str(header_name)] = str(api_key)

        return headers

    def _prepare_auth(self, configuration: SourceConfiguration) -> AuthHeaders | None:
        auth_type = configuration.auth_type or "none"
        auth_method = self.auth_methods.get(auth_type)
        if auth_method and configuration.auth_credentials:
            credentials = cast("dict[str, Any]", configuration.auth_credentials)
            return auth_method(credentials)
        if auth_type == "none":
            return None
        return auth_method({}) if auth_method else None

    def _metadata(self, configuration: SourceConfiguration) -> SourceMetadata:
        return configuration.metadata

    def _coerce_limit(self, value: Any, default: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        else:
            return parsed if parsed > 0 else default

    async def _apply_rate_limiting(
        self,
        configuration: SourceConfiguration,
    ) -> None:
        rate_limit = configuration.requests_per_minute or 60
        delay_seconds = 60.0 / rate_limit
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)

    async def _make_request_with_retries(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any],
    ) -> httpx.Response | None:
        for attempt in range(self.max_retries):
            try:
                return await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                )
            except (httpx.TimeoutException, httpx.ConnectError):
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2**attempt)
        return None

    def _count_records(self, data: Any) -> int:
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict):
            for key in ["data", "results", "records", "items"]:
                if key in data and isinstance(data[key], list):
                    return len(data[key])
            return 1
        return 0

    def _auth_none(self, _config: dict[str, Any]) -> None:
        return None

    def _auth_bearer(self, config: dict[str, Any]) -> AuthHeaders | None:
        token = config.get("token", "")
        if token:
            return {"Authorization": f"Bearer {token}"}
        return None

    def _auth_basic(self, config: dict[str, Any]) -> AuthHeaders | None:
        username = config.get("username", "")
        password = config.get("password", "")
        if username and password:
            auth_string = base64.b64encode(f"{username}:{password}".encode()).decode()
            return {"Authorization": f"Basic {auth_string}"}
        return None

    def _auth_api_key(self, _config: dict[str, Any]) -> None:
        return None

    def _auth_oauth2(self, config: dict[str, Any]) -> AuthHeaders | None:
        token = config.get("access_token", "")
        if token:
            return {"Authorization": f"Bearer {token}"}
        return None
