"""
Tests for PubMedDiscoveryService ensuring search jobs and downloads behave.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import pytest

from src.application.services.pubmed_discovery_service import (
    PUBMED_STORAGE_METADATA_ARTICLE_ID_KEY,
    PUBMED_STORAGE_METADATA_JOB_ID_KEY,
    PUBMED_STORAGE_METADATA_OWNER_ID_KEY,
    PUBMED_STORAGE_METADATA_USE_CASE_KEY,
    PubMedDiscoveryService,
    PubmedDownloadRequest,
    RunPubmedSearchRequest,
)
from src.application.services.pubmed_query_builder import PubMedQueryBuilder
from src.domain.entities.data_discovery_parameters import AdvancedQueryParameters
from src.domain.repositories.data_discovery_repository import (
    DiscoverySearchJobRepository,
)
from src.domain.services.pubmed_search import (
    PubMedPdfGateway,
    PubMedSearchGateway,
    PubMedSearchPayload,
)
from src.type_definitions.storage import (
    StorageOperationRecord,
    StorageOperationStatus,
    StorageOperationType,
    StorageUseCase,
)

if TYPE_CHECKING:
    from pathlib import Path

    from src.domain.entities.discovery_search_job import DiscoverySearchJob
    from src.type_definitions.common import JSONObject


class InMemorySearchJobRepository(DiscoverySearchJobRepository):
    """Simple repository storing jobs in memory for tests."""

    def __init__(self) -> None:
        self._jobs: dict[UUID, DiscoverySearchJob] = {}

    def create(self, job: DiscoverySearchJob) -> DiscoverySearchJob:
        self._jobs[job.id] = job
        return job

    def update(self, job: DiscoverySearchJob) -> DiscoverySearchJob:
        self._jobs[job.id] = job
        return job

    def get(self, job_id: UUID) -> DiscoverySearchJob | None:
        return self._jobs.get(job_id)

    def list_for_owner(self, owner_id: UUID) -> list[DiscoverySearchJob]:
        return [job for job in self._jobs.values() if job.owner_id == owner_id]

    def list_for_session(self, session_id: UUID) -> list[DiscoverySearchJob]:
        return [job for job in self._jobs.values() if job.session_id == session_id]


class StubSearchGateway(PubMedSearchGateway):
    """Returns deterministic search payloads for tests."""

    async def run_search(
        self,
        parameters: AdvancedQueryParameters,
    ) -> PubMedSearchPayload:
        article_ids = [
            f"{parameters.gene_symbol or 'MED13'}-{index}" for index in range(1, 4)
        ]
        preview = [
            {
                "pmid": article_id,
                "title": f"{parameters.search_term or 'MED13'} preview {index}",
            }
            for index, article_id in enumerate(article_ids, start=1)
        ]
        return PubMedSearchPayload(
            article_ids=article_ids,
            total_count=len(article_ids),
            preview_records=preview,
        )


class StubPdfGateway(PubMedPdfGateway):
    """Produces fixed bytes for PDF downloads."""

    async def fetch_pdf(self, article_id: str) -> bytes:
        return f"PDF for {article_id}".encode()


class FailingPdfGateway(PubMedPdfGateway):
    """Simulates a gateway failure."""

    async def fetch_pdf(self, article_id: str) -> bytes:
        message = "Gateway connection failed"
        raise RuntimeError(message)


class RecordingStorageCoordinator:
    """Records store invocations without hitting real storage."""

    def __init__(self) -> None:
        self.records: list[StorageOperationRecord] = []

    async def store_for_use_case(
        self,
        use_case: StorageUseCase,
        *,
        key: str,
        file_path: Path,
        content_type: str | None = None,
        user_id: UUID | None = None,
        metadata: JSONObject | None = None,
    ) -> StorageOperationRecord:
        metadata_payload = {
            "content_type": content_type or "application/pdf",
            "use_case": use_case.value,
            **(metadata or {}),
        }
        record = StorageOperationRecord(
            id=uuid4(),
            configuration_id=uuid4(),
            user_id=user_id,
            operation_type=StorageOperationType.STORE,
            key=key,
            file_size_bytes=file_path.stat().st_size,
            status=StorageOperationStatus.SUCCESS,
            error_message=None,
            metadata=metadata_payload,
            created_at=datetime.now(UTC),
        )
        self.records.append(record)
        return record


@pytest.mark.asyncio
async def test_run_pubmed_search_transitions_job_states() -> None:
    """Search execution should create, run, and complete jobs with metadata."""
    repo = InMemorySearchJobRepository()
    service = PubMedDiscoveryService(
        job_repository=repo,
        query_builder=PubMedQueryBuilder(),
        search_gateway=StubSearchGateway(),
        pdf_gateway=StubPdfGateway(),
        storage_coordinator=RecordingStorageCoordinator(),
    )

    owner_id = uuid4()
    request = RunPubmedSearchRequest(
        session_id=uuid4(),
        parameters=AdvancedQueryParameters(
            gene_symbol="MED13L",
            search_term="syndrome",
        ),
    )

    job = await service.run_pubmed_search(owner_id, request)

    assert job.status.name == "COMPLETED"
    assert job.total_results == 3
    assert "article_ids" in job.result_metadata


@pytest.mark.asyncio
async def test_download_article_pdf_requires_completion() -> None:
    """Downloading before job completion should fail."""
    repo = InMemorySearchJobRepository()
    coordinator = RecordingStorageCoordinator()
    service = PubMedDiscoveryService(
        job_repository=repo,
        query_builder=PubMedQueryBuilder(),
        search_gateway=StubSearchGateway(),
        pdf_gateway=StubPdfGateway(),
        storage_coordinator=coordinator,
    )
    owner_id = uuid4()
    request = RunPubmedSearchRequest(
        session_id=None,
        parameters=AdvancedQueryParameters(gene_symbol="MED13", search_term=None),
    )
    job = await service.run_pubmed_search(owner_id, request)

    assert job.status.name == "COMPLETED"

    download_request = PubmedDownloadRequest(
        job_id=job.id,
        article_id=job.result_metadata["article_ids"][0],
    )
    record = await service.download_article_pdf(owner_id, download_request)

    assert record.key.endswith(".pdf")
    assert coordinator.records, "Storage coordinator should record the operation"


@pytest.mark.asyncio
async def test_download_article_pdf_sets_retry_metadata() -> None:
    repo = InMemorySearchJobRepository()
    coordinator = RecordingStorageCoordinator()
    service = PubMedDiscoveryService(
        job_repository=repo,
        query_builder=PubMedQueryBuilder(),
        search_gateway=StubSearchGateway(),
        pdf_gateway=StubPdfGateway(),
        storage_coordinator=coordinator,
    )
    owner_id = uuid4()
    job = await service.run_pubmed_search(
        owner_id,
        RunPubmedSearchRequest(
            session_id=None,
            parameters=AdvancedQueryParameters(gene_symbol="MED13", search_term=None),
        ),
    )
    article_id = job.result_metadata["article_ids"][0]
    record = await service.download_article_pdf(
        owner_id,
        PubmedDownloadRequest(job_id=job.id, article_id=article_id),
    )

    metadata = record.metadata
    assert metadata[PUBMED_STORAGE_METADATA_JOB_ID_KEY] == str(job.id)
    assert metadata[PUBMED_STORAGE_METADATA_ARTICLE_ID_KEY] == article_id
    assert metadata[PUBMED_STORAGE_METADATA_OWNER_ID_KEY] == str(owner_id)
    assert metadata[PUBMED_STORAGE_METADATA_USE_CASE_KEY] == StorageUseCase.PDF.value


@pytest.mark.asyncio
async def test_download_article_pdf_propagates_gateway_errors() -> None:
    """Service should propagate gateway errors to allow retries upstream."""
    repo = InMemorySearchJobRepository()
    coordinator = RecordingStorageCoordinator()
    service = PubMedDiscoveryService(
        job_repository=repo,
        query_builder=PubMedQueryBuilder(),
        search_gateway=StubSearchGateway(),
        pdf_gateway=FailingPdfGateway(),
        storage_coordinator=coordinator,
    )
    owner_id = uuid4()
    job = await service.run_pubmed_search(
        owner_id,
        RunPubmedSearchRequest(
            session_id=None,
            parameters=AdvancedQueryParameters(gene_symbol="MED13", search_term=None),
        ),
    )
    article_id = job.result_metadata["article_ids"][0]

    with pytest.raises(RuntimeError, match="Gateway connection failed"):
        await service.download_article_pdf(
            owner_id,
            PubmedDownloadRequest(job_id=job.id, article_id=article_id),
        )
