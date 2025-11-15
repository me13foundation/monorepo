"""Application service coordinating scheduled ingestion across sources."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from src.domain.entities.ingestion_job import (
    IngestionError,
    IngestionJob,
    IngestionTrigger,
    JobMetrics,
)
from src.domain.entities.user_data_source import (
    ScheduleFrequency,
    SourceType,
    UserDataSource,
)
from src.models.value_objects.provenance import (
    DataSource as ProvenanceSource,
)
from src.models.value_objects.provenance import (
    Provenance,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Mapping

    from src.application.services.ports.scheduler_port import (
        ScheduledJob,
        SchedulerPort,
    )
    from src.domain.repositories.ingestion_job_repository import (
        IngestionJobRepository,
    )
    from src.domain.repositories.user_data_source_repository import (
        UserDataSourceRepository,
    )
    from src.domain.services.pubmed_ingestion import PubMedIngestionSummary


class IngestionSchedulingService:
    """Coordinates scheduler registration and execution of ingestion jobs."""

    def __init__(
        self,
        scheduler: SchedulerPort,
        source_repository: UserDataSourceRepository,
        job_repository: IngestionJobRepository,
        ingestion_services: Mapping[
            SourceType,
            Callable[[UserDataSource], Awaitable[PubMedIngestionSummary]],
        ],
    ) -> None:
        self._scheduler = scheduler
        self._source_repository = source_repository
        self._job_repository = job_repository
        self._ingestion_services = dict(ingestion_services)

    async def schedule_source(self, source_id: UUID) -> ScheduledJob:
        """Register a source with the scheduler backend."""
        source = self._get_source(source_id)
        schedule = source.ingestion_schedule
        if not schedule.requires_scheduler:
            msg = "Source schedule must be enabled with non-manual frequency"
            raise ValueError(msg)

        scheduled = self._scheduler.register_job(source_id, schedule)
        updated_schedule = schedule.model_copy(
            update={
                "backend_job_id": scheduled.job_id,
                "next_run_at": scheduled.next_run_at,
            },
        )
        self._source_repository.update_ingestion_schedule(source_id, updated_schedule)
        return scheduled

    def unschedule_source(self, source_id: UUID) -> None:
        """Remove a scheduled job for the given source if present."""
        source = self._get_source(source_id)
        job_id = source.ingestion_schedule.backend_job_id
        if job_id:
            self._scheduler.remove_job(job_id)
            updated = source.ingestion_schedule.model_copy(
                update={"backend_job_id": None, "next_run_at": None},
            )
            self._source_repository.update_ingestion_schedule(source_id, updated)

    async def run_due_jobs(self, *, as_of: datetime | None = None) -> None:
        """Execute all jobs that are due as of the provided timestamp."""
        due_jobs = self._scheduler.get_due_jobs(as_of=as_of)
        for job in due_jobs:
            await self._execute_job(job)

    async def trigger_ingestion(
        self,
        source_id: UUID,
    ) -> PubMedIngestionSummary:
        """Manually trigger ingestion for a source outside of scheduler cadence."""
        source = self._get_source(source_id)
        return await self._run_ingestion_for_source(source)

    async def _execute_job(self, scheduled_job: ScheduledJob) -> None:
        source = self._get_source(scheduled_job.source_id)
        if source.ingestion_schedule.frequency == ScheduleFrequency.MANUAL:
            return
        await self._run_ingestion_for_source(source)

    async def _run_ingestion_for_source(
        self,
        source: UserDataSource,
    ) -> PubMedIngestionSummary:
        service = self._ingestion_services.get(source.source_type)
        if service is None:
            msg = f"No ingestion service registered for {source.source_type}"
            raise ValueError(msg)

        job = self._job_repository.save(self._create_ingestion_job(source))
        running = self._job_repository.save(job.start_execution())
        try:
            summary = await service(source)
            metrics = JobMetrics(
                records_processed=summary.created_publications
                + summary.updated_publications,
                records_failed=0,
                records_skipped=0,
                bytes_processed=0,
                api_calls_made=0,
                duration_seconds=None,
                records_per_second=None,
            )
            completed = running.complete_successfully(metrics)
        except Exception as exc:  # pragma: no cover - defensive
            error = IngestionError(
                error_type="scheduler_failure",
                error_message=str(exc),
                record_id=None,
            )
            failed = running.fail(error)
            self._job_repository.save(failed)
            raise
        else:
            self._job_repository.save(completed)
            updated_source = (
                self._source_repository.record_ingestion(source.id) or source
            )
            self._update_schedule_after_run(updated_source)
            return summary

    def _create_ingestion_job(self, source: UserDataSource) -> IngestionJob:
        return IngestionJob(
            id=uuid4(),
            source_id=source.id,
            trigger=IngestionTrigger.SCHEDULED,
            triggered_by=None,
            started_at=None,
            completed_at=None,
            provenance=Provenance(
                source=ProvenanceSource.COMPUTED,
                source_version=None,
                source_url=None,
                acquired_by="ingestion-scheduler",
                processing_steps=["scheduled_ingestion"],
                quality_score=None,
            ),
            metadata={},
            source_config_snapshot=source.configuration.model_dump(),
        )

    def _get_source(self, source_id: UUID) -> UserDataSource:
        source = self._source_repository.find_by_id(source_id)
        if source is None:
            msg = f"Data source {source_id} not found"
            raise ValueError(msg)
        return source

    def _update_schedule_after_run(self, source: UserDataSource) -> None:
        schedule = source.ingestion_schedule
        updates: dict[str, datetime | None] = {"last_run_at": datetime.now(UTC)}
        job_id = schedule.backend_job_id
        if job_id:
            job = self._scheduler.get_job(job_id)
            if job:
                updates["next_run_at"] = job.next_run_at
        updated_schedule = schedule.model_copy(update=updates)
        self._source_repository.update_ingestion_schedule(source.id, updated_schedule)
