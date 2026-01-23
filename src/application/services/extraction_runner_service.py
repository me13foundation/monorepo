"""Application service for running publication extraction jobs."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from src.application.services.ports.extraction_processor_port import (
        ExtractionProcessorPort,
        ExtractionProcessorResult,
    )
    from src.domain.entities.extraction_queue_item import ExtractionQueueItem
    from src.domain.entities.publication import Publication
    from src.domain.repositories.extraction_queue_repository import (
        ExtractionQueueRepository,
    )
    from src.domain.repositories.publication_repository import PublicationRepository
    from src.type_definitions.common import JSONObject


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExtractionRunSummary:
    source_id: UUID | None
    ingestion_job_id: UUID | None
    requested: int
    processed: int
    completed: int
    skipped: int
    failed: int
    started_at: datetime
    completed_at: datetime

    def to_metadata(self) -> JSONObject:
        return {
            "source_id": str(self.source_id) if self.source_id else None,
            "ingestion_job_id": (
                str(self.ingestion_job_id) if self.ingestion_job_id else None
            ),
            "requested": self.requested,
            "processed": self.processed,
            "completed": self.completed,
            "skipped": self.skipped,
            "failed": self.failed,
            "started_at": self.started_at.isoformat(timespec="seconds"),
            "completed_at": self.completed_at.isoformat(timespec="seconds"),
        }


class ExtractionRunnerService:
    """Claims pending extraction queue items and processes them."""

    def __init__(
        self,
        *,
        queue_repository: ExtractionQueueRepository,
        publication_repository: PublicationRepository,
        processor: ExtractionProcessorPort,
        batch_size: int = 25,
    ) -> None:
        self._queue_repository = queue_repository
        self._publication_repository = publication_repository
        self._processor = processor
        self._batch_size = max(batch_size, 1)

    def run_for_ingestion_job(
        self,
        *,
        source_id: UUID,
        ingestion_job_id: UUID,
        expected_items: int,
        batch_size: int | None = None,
    ) -> ExtractionRunSummary:
        started_at = datetime.now(UTC)
        processed = 0
        completed = 0
        skipped = 0
        failed = 0
        batch_limit = batch_size or self._batch_size

        while True:
            batch = self._run_batch(
                limit=batch_limit,
                source_id=source_id,
                ingestion_job_id=ingestion_job_id,
            )
            processed += batch.processed
            completed += batch.completed
            skipped += batch.skipped
            failed += batch.failed

            if batch.processed == 0:
                break
            if processed >= expected_items:
                break

        completed_at = datetime.now(UTC)
        return ExtractionRunSummary(
            source_id=source_id,
            ingestion_job_id=ingestion_job_id,
            requested=expected_items,
            processed=processed,
            completed=completed,
            skipped=skipped,
            failed=failed,
            started_at=started_at,
            completed_at=completed_at,
        )

    def run_pending(
        self,
        *,
        limit: int | None = None,
        source_id: UUID | None = None,
        ingestion_job_id: UUID | None = None,
    ) -> ExtractionRunSummary:
        started_at = datetime.now(UTC)
        batch = self._run_batch(
            limit=limit or self._batch_size,
            source_id=source_id,
            ingestion_job_id=ingestion_job_id,
        )
        completed_at = datetime.now(UTC)
        return ExtractionRunSummary(
            source_id=source_id,
            ingestion_job_id=ingestion_job_id,
            requested=batch.processed,
            processed=batch.processed,
            completed=batch.completed,
            skipped=batch.skipped,
            failed=batch.failed,
            started_at=started_at,
            completed_at=completed_at,
        )

    def _run_batch(
        self,
        *,
        limit: int,
        source_id: UUID | None,
        ingestion_job_id: UUID | None,
    ) -> _BatchSummary:
        items = self._queue_repository.claim_pending(
            limit=limit,
            source_id=source_id,
            ingestion_job_id=ingestion_job_id,
        )
        if not items:
            return _BatchSummary()

        completed = 0
        skipped = 0
        failed = 0

        for item in items:
            publication = self._publication_repository.get_by_id(item.publication_id)
            try:
                result = self._processor.extract_publication(
                    queue_item=item,
                    publication=publication,
                )
            except Exception as exc:  # pragma: no cover - defensive
                failed += 1
                self._queue_repository.mark_failed(
                    item.id,
                    error_message=str(exc),
                )
                logger.exception(
                    "Extraction processor failed for item %s",
                    item.id,
                )
                continue

            failed_increment = self._handle_result(
                item=item,
                publication=publication,
                result=result,
            )
            if failed_increment:
                failed += 1
            elif result.status == "skipped":
                skipped += 1
            else:
                completed += 1

        return _BatchSummary(
            processed=len(items),
            completed=completed,
            skipped=skipped,
            failed=failed,
        )

    def _handle_result(
        self,
        *,
        item: ExtractionQueueItem,
        publication: Publication | None,
        result: ExtractionProcessorResult,
    ) -> bool:
        if result.status == "failed":
            error_message = result.error_message or "extraction_failed"
            self._queue_repository.mark_failed(
                item.id,
                error_message=error_message,
            )
            return True

        metadata = self._build_metadata(
            item=item,
            publication=publication,
            result=result,
        )
        self._queue_repository.mark_completed(
            item.id,
            metadata=metadata,
        )
        return False

    def _build_metadata(
        self,
        *,
        item: ExtractionQueueItem,
        publication: Publication | None,
        result: ExtractionProcessorResult,
    ) -> JSONObject:
        payload: JSONObject = dict(result.metadata)
        payload["extraction_outcome"] = result.status
        payload["extraction_version"] = item.extraction_version
        payload["extracted_at"] = datetime.now(UTC).isoformat(timespec="seconds")

        if publication is not None:
            if publication.id is not None:
                payload["publication_id"] = publication.id
            payload["publication_title"] = publication.title
            payload["pubmed_id"] = publication.identifier.pubmed_id
            payload["pmc_id"] = publication.identifier.pmc_id
            payload["doi"] = publication.identifier.doi

        return payload


@dataclass(frozen=True)
class _BatchSummary:
    processed: int = 0
    completed: int = 0
    skipped: int = 0
    failed: int = 0


__all__ = ["ExtractionRunSummary", "ExtractionRunnerService"]
