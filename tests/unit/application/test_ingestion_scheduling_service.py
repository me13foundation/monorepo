"""Tests for the ingestion scheduling service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, cast
from uuid import UUID, uuid4

import pytest

from src.application.services.ingestion_scheduling_service import (
    IngestionSchedulingService,
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

if TYPE_CHECKING:
    from src.domain.repositories.ingestion_job_repository import (
        IngestionJobRepository,
    )
    from src.domain.repositories.user_data_source_repository import (
        UserDataSourceRepository,
    )
else:  # pragma: no cover - type checking only
    IngestionJobRepository = object  # type: ignore[assignment]
    UserDataSourceRepository = object  # type: ignore[assignment]


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
