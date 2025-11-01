"""
Base ingestor for MED13 Resource Library data acquisition.
Provides common functionality for API clients with rate limiting and error handling.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import json
import time
from pathlib import Path

import httpx

from src.models.value_objects import Provenance, DataSource


class IngestionStatus(Enum):
    """Status of an ingestion operation."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class IngestionError(Exception):
    """Base exception for ingestion operations."""

    def __init__(
        self, message: str, source: str, details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.source = source
        self.details = details or {}


@dataclass
class IngestionResult:
    """Result of an ingestion operation."""

    source: str
    status: IngestionStatus
    records_processed: int
    records_failed: int
    data: List[Dict[str, Any]]
    provenance: Provenance
    errors: List[IngestionError]
    duration_seconds: float
    timestamp: datetime


class RateLimiter:
    """Simple token bucket rate limiter."""

    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests_per_second = requests_per_minute / 60.0
        self.tokens = requests_per_minute
        self.last_update = time.time()
        self.max_tokens = requests_per_minute

    def acquire(self) -> bool:
        """Acquire a token. Returns True if successful."""
        now = time.time()
        elapsed = now - self.last_update

        # Add tokens based on elapsed time
        self.tokens = min(
            self.max_tokens, self.tokens + elapsed * self.requests_per_second
        )
        self.last_update = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

    async def wait_for_token(self) -> None:
        """Wait until a token is available."""
        while not self.acquire():
            await asyncio.sleep(1.0)


class BaseIngestor(ABC):
    """
    Abstract base class for data ingestion from biomedical sources.

    Provides common functionality for:
    - Rate limiting and retry logic
    - Error handling and circuit breaker patterns
    - Provenance tracking
    - Raw data storage
    - Progress tracking
    """

    def __init__(
        self,
        source_name: str,
        base_url: str,
        requests_per_minute: int = 60,
        timeout_seconds: int = 30,
        max_retries: int = 3,
        raw_data_dir: Optional[Path] = None,
    ):
        self.source_name = source_name
        self.base_url = base_url
        self.rate_limiter = RateLimiter(requests_per_minute)
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

        # Raw data storage
        self.raw_data_dir = raw_data_dir or Path("data/raw") / source_name
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)

        # Circuit breaker state
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_open = False

        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds),
            headers={"User-Agent": "MED13-Resource-Library/1.0 (research@med13.org)"},
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    @abstractmethod
    async def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Abstract method to fetch data from the source.

        Args:
            **kwargs: Source-specific parameters

        Returns:
            List of raw data records
        """
        pass

    async def ingest(self, **kwargs) -> IngestionResult:
        """
        Main ingestion method with error handling and provenance tracking.

        Args:
            **kwargs: Parameters passed to fetch_data

        Returns:
            IngestionResult with all operation details
        """
        start_time = datetime.utcnow()
        # Map source name to DataSource enum
        data_source_enum = DataSource(self.source_name)

        provenance = Provenance(
            source=data_source_enum,
            acquired_at=start_time,
            acquired_by="MED13-Resource-Library",
            processing_steps=[f"Ingested from {self.source_name}"],
            validation_status="pending",
            quality_score=1.0,
        )

        errors = []
        data = []

        try:
            # Check circuit breaker
            if self.circuit_open:
                raise IngestionError(
                    f"Circuit breaker open for {self.source_name}",
                    self.source_name,
                    {"circuit_breaker": True},
                )

            # Fetch data
            data = await self.fetch_data(**kwargs)

            # Store raw data
            await self._store_raw_data(data, start_time)

            # Update provenance
            provenance.processing_steps.append(f"Retrieved {len(data)} records")

            return IngestionResult(
                source=self.source_name,
                status=IngestionStatus.COMPLETED,
                records_processed=len(data),
                records_failed=0,
                data=data,
                provenance=provenance,
                errors=errors,
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                timestamp=start_time,
            )

        except Exception as e:
            # Record failure
            self._record_failure()
            error = IngestionError(
                str(e), self.source_name, {"exception_type": type(e).__name__}
            )
            errors.append(error)

            return IngestionResult(
                source=self.source_name,
                status=IngestionStatus.FAILED,
                records_processed=len(data),
                records_failed=len(data) if data else 1,
                data=data,
                provenance=provenance,
                errors=errors,
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                timestamp=start_time,
            )

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with rate limiting and retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint (relative to base_url)
            **kwargs: Additional request parameters

        Returns:
            HTTP response

        Raises:
            IngestionError: If request fails after retries
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        for attempt in range(self.max_retries):
            try:
                # Wait for rate limit token
                await self.rate_limiter.wait_for_token()

                response = await self.client.request(method, url, **kwargs)

                # Check for rate limiting
                if response.status_code == 429:
                    # Exponential backoff for rate limiting
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    # Server error - retry
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2**attempt)
                        continue
                raise IngestionError(
                    f"HTTP {e.response.status_code}: {e.response.text}",
                    self.source_name,
                )

            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue
                raise IngestionError(f"Request failed: {str(e)}", self.source_name)

        raise IngestionError(
            f"Failed after {self.max_retries} attempts", self.source_name
        )

    async def _store_raw_data(
        self, data: List[Dict[str, Any]], timestamp: datetime
    ) -> Path:
        """
        Store raw data to filesystem with timestamp.

        Args:
            data: Raw data to store
            timestamp: Timestamp for filename

        Returns:
            Path to stored file
        """
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"{self.source_name}_{timestamp_str}.json"
        filepath = self.raw_data_dir / filename

        with open(filepath, "w") as f:
            json.dump(
                {
                    "source": self.source_name,
                    "timestamp": timestamp.isoformat(),
                    "records": data,
                },
                f,
                indent=2,
                default=str,
            )

        return filepath

    def _record_failure(self) -> None:
        """Record a failure for circuit breaker logic."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        # Open circuit after 5 consecutive failures
        if self.failure_count >= 5:
            self.circuit_open = True

    def reset_circuit_breaker(self) -> None:
        """Reset circuit breaker state."""
        self.failure_count = 0
        self.circuit_open = False
        self.last_failure_time = None
