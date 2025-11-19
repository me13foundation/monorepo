"""Tests for the ingestion scheduling service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast
from uuid import UUID, uuid4

import pytest

from src.application.services.ingestion_scheduling_service import (
    IngestionSchedulingService,
)
from src.application.services.pubmed_discovery_service import (
    PUBMED_STORAGE_METADATA_ARTICLE_ID_KEY,
    PUBMED_STORAGE_METADATA_JOB_ID_KEY,
    PUBMED_STORAGE_METADATA_OWNER_ID_KEY,
    PUBMED_STORAGE_METADATA_RETRYABLE_KEY,
    PUBMED_STORAGE_METADATA_USE_CASE_KEY,
    PubmedDownloadRequest,
)
from src.domain.entities.user_data_source import (
    IngestionSchedule,
    ScheduleFrequency,
    SourceConfiguration,
    SourceType,
    UserDataSource,
)
from src.domain.services.pubmed_ingestion import PubMedIngestionSummary
from src.infrastructure.scheduling import InMemoryScheduler
from src.type_definitions.storage import (
    StorageOperationRecord,
    StorageOperationStatus,
    StorageOperationType,
    StorageUseCase,
)

if TYPE_CHECKING:
    from src.application.services.pubmed_discovery_service import (
        PubMedDiscoveryService,
    )
    from src.domain.repositories.ingestion_job_repository import (
        IngestionJobRepository,
    )
    from src.domain.repositories.storage_repository import StorageOperationRepository
    from src.domain.repositories.user_data_source_repository import (
        UserDataSourceRepository,
    )
    from src.type_definitions.common import JSONObject
else:  # pragma: no cover - type checking only
    IngestionJobRepository = object  # type: ignore[assignment]
    UserDataSourceRepository = object  # type: ignore[assignment]
    StorageOperationRepository = object  # type: ignore[assignment]
    PubMedDiscoveryService = object  # type: ignore[assignment]
    JSONObject = dict[str, object]  # type: ignore[assignment]


class StubSourceRepository:
    def __init__(self, source: UserDataSource) -> None:
        self.source = source
        self.ingestion_recorded = False

    def find_by_id(self, source_id: UUID) -> UserDataSource | None:
        return self.source if source_id == self.source.id else None

    def update_ingestion_schedule(
        self,
        source_id: UUID,
        schedule: IngestionSchedule,
    ) -> UserDataSource:
        self.source = self.source.update_ingestion_schedule(schedule)
        return self.source

    def record_ingestion(self, source_id: UUID) -> UserDataSource:
        self.ingestion_recorded = True
        return self.source


class StubJobRepository:
    def __init__(self) -> None:
        self.saved: list[object] = []

    def save(self, job: object) -> object:
        self.saved.append(job)
        return job


class StubPubMedIngestionService:
    def __init__(self) -> None:
        self.calls: list[UserDataSource] = []

    async def ingest(self, source: UserDataSource) -> PubMedIngestionSummary:
        self.calls.append(source)
        return PubMedIngestionSummary(
            source_id=source.id,
            fetched_records=2,
            parsed_publications=2,
            created_publications=1,
            updated_publications=1,
        )


def _build_source(schedule: IngestionSchedule) -> UserDataSource:
    return UserDataSource(
        id=uuid4(),
        owner_id=uuid4(),
        research_space_id=None,
        name="PubMed Source",
        description="",
        source_type=SourceType.PUBMED,
        template_id=None,
        configuration=SourceConfiguration(
            url=None,
            file_path=None,
            format=None,
            auth_type=None,
            auth_credentials=None,
            requests_per_minute=None,
            field_mapping=None,
            metadata={"query": "MED13"},
        ),
        ingestion_schedule=schedule,
        tags=[],
        last_ingested_at=None,
    )


class StubStorageOperationRepository:
    def __init__(self, operations: list[StorageOperationRecord]) -> None:
        self.operations = operations
        self.updated: list[tuple[UUID, JSONObject]] = []

    def list_failed_store_operations(
        self,
        *,
        limit: int = 100,
    ) -> list[StorageOperationRecord]:
        return self.operations[:limit]

    def update_operation_metadata(
        self,
        operation_id: UUID,
        metadata: JSONObject,
    ) -> StorageOperationRecord:
        self.updated.append((operation_id, metadata))
        for index, operation in enumerate(self.operations):
            if operation.id == operation_id:
                updated = operation.model_copy(update={"metadata": metadata})
                self.operations[index] = updated
                return updated
        message = "Operation not found"
        raise ValueError(message)


class StubPubMedDiscoveryRetryService:
    def __init__(self) -> None:
        self.jobs: dict[UUID, tuple[UUID, dict[str, object]]] = {}
        self.download_calls: list[tuple[UUID, PubmedDownloadRequest]] = []

    def set_job(
        self,
        *,
        job_id: UUID,
        owner_id: UUID,
        metadata: JSONObject,
    ) -> None:
        self.jobs[job_id] = (owner_id, metadata)

    def get_search_job(
        self,
        owner_id: UUID,
        job_id: UUID,
    ) -> SimpleNamespace | None:
        stored = self.jobs.get(job_id)
        if stored is None:
            return None
        expected_owner, metadata = stored
        if expected_owner != owner_id:
            return None
        return SimpleNamespace(result_metadata=metadata)

    async def download_article_pdf(
        self,
        owner_id: UUID,
        request: PubmedDownloadRequest,
    ) -> None:
        self.download_calls.append((owner_id, request))


def _make_failed_operation(
    *,
    job_id: UUID,
    owner_id: UUID,
    article_id: str,
    retryable: bool = True,
) -> StorageOperationRecord:
    return StorageOperationRecord(
        id=uuid4(),
        configuration_id=uuid4(),
        user_id=owner_id,
        operation_type=StorageOperationType.STORE,
        key=f"discovery/pubmed/{job_id}/{article_id}.pdf",
        file_size_bytes=None,
        status=StorageOperationStatus.FAILED,
        error_message="upload failed",
        metadata={
            PUBMED_STORAGE_METADATA_USE_CASE_KEY: StorageUseCase.PDF.value,
            PUBMED_STORAGE_METADATA_JOB_ID_KEY: str(job_id),
            PUBMED_STORAGE_METADATA_OWNER_ID_KEY: str(owner_id),
            PUBMED_STORAGE_METADATA_ARTICLE_ID_KEY: article_id,
            PUBMED_STORAGE_METADATA_RETRYABLE_KEY: retryable,
        },
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_run_due_jobs_triggers_ingestion() -> None:
    schedule = IngestionSchedule(
        enabled=True,
        frequency=ScheduleFrequency.HOURLY,
        start_time=datetime.now(UTC) - timedelta(hours=1),
    )
    source = _build_source(schedule)
    source_repo = StubSourceRepository(source)
    job_repo = StubJobRepository()
    pubmed_service = StubPubMedIngestionService()
    scheduler = InMemoryScheduler()

    service = IngestionSchedulingService(
        scheduler=scheduler,
        source_repository=cast("UserDataSourceRepository", source_repo),
        job_repository=cast("IngestionJobRepository", job_repo),
        ingestion_services={SourceType.PUBMED: pubmed_service.ingest},
    )

    await service.schedule_source(source.id)
    await service.run_due_jobs(as_of=datetime.now(UTC) + timedelta(hours=1, seconds=1))

    assert len(pubmed_service.calls) == 1
    assert source_repo.ingestion_recorded
    # Jobs saved include initial, running, completion states
    assert len(job_repo.saved) >= 3


@pytest.mark.asyncio
async def test_run_due_jobs_retries_failed_pdf_downloads() -> None:
    owner_id = uuid4()
    job_id = uuid4()
    article_id = "12345"
    operation = _make_failed_operation(
        job_id=job_id,
        owner_id=owner_id,
        article_id=article_id,
    )
    storage_repo = StubStorageOperationRepository([operation])
    discovery_service = StubPubMedDiscoveryRetryService()
    discovery_service.set_job(
        job_id=job_id,
        owner_id=owner_id,
        metadata={"stored_assets": {}},
    )

    service = IngestionSchedulingService(
        scheduler=InMemoryScheduler(),
        source_repository=cast(
            "UserDataSourceRepository",
            StubSourceRepository(
                _build_source(
                    IngestionSchedule(
                        enabled=False,
                        frequency=ScheduleFrequency.MANUAL,
                    ),
                ),
            ),
        ),
        job_repository=cast("IngestionJobRepository", StubJobRepository()),
        ingestion_services={},
        storage_operation_repository=cast(
            "StorageOperationRepository",
            storage_repo,
        ),
        pubmed_discovery_service=cast(
            "PubMedDiscoveryService",
            discovery_service,
        ),
    )

    await service.run_due_jobs()

    assert len(discovery_service.download_calls) == 1
    updated_metadata = storage_repo.updated[0][1]
    assert updated_metadata[PUBMED_STORAGE_METADATA_RETRYABLE_KEY] is False


@pytest.mark.asyncio
async def test_retry_skips_when_article_already_stored() -> None:
    owner_id = uuid4()
    job_id = uuid4()
    article_id = "55555"
    operation = _make_failed_operation(
        job_id=job_id,
        owner_id=owner_id,
        article_id=article_id,
    )
    storage_repo = StubStorageOperationRepository([operation])
    discovery_service = StubPubMedDiscoveryRetryService()
    discovery_service.set_job(
        job_id=job_id,
        owner_id=owner_id,
        metadata={"stored_assets": {article_id: "discovery/pubmed/saved.pdf"}},
    )

    service = IngestionSchedulingService(
        scheduler=InMemoryScheduler(),
        source_repository=cast(
            "UserDataSourceRepository",
            StubSourceRepository(
                _build_source(
                    IngestionSchedule(
                        enabled=False,
                        frequency=ScheduleFrequency.MANUAL,
                    ),
                ),
            ),
        ),
        job_repository=cast("IngestionJobRepository", StubJobRepository()),
        ingestion_services={},
        storage_operation_repository=cast(
            "StorageOperationRepository",
            storage_repo,
        ),
        pubmed_discovery_service=cast(
            "PubMedDiscoveryService",
            discovery_service,
        ),
    )

    await service.run_due_jobs()

    assert not discovery_service.download_calls
    updated_metadata = storage_repo.updated[0][1]
    assert updated_metadata[PUBMED_STORAGE_METADATA_RETRYABLE_KEY] is False
