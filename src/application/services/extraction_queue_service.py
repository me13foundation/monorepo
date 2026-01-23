"""Application service for managing publication extraction queue items."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from src.domain.entities.extraction_queue_item import (
    ExtractionQueueItem,
    ExtractionStatus,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from src.domain.repositories.extraction_queue_repository import (
        ExtractionQueueRepository,
    )

logger = logging.getLogger(__name__)


DEFAULT_EXTRACTION_VERSION = 1


@dataclass(frozen=True)
class ExtractionEnqueueSummary:
    source_id: UUID
    ingestion_job_id: UUID
    extraction_version: int
    requested: int
    queued: int
    skipped: int


class ExtractionQueueService:
    """Coordinates queueing of publications for extraction."""

    def __init__(
        self,
        queue_repository: ExtractionQueueRepository,
        *,
        extraction_version: int = DEFAULT_EXTRACTION_VERSION,
    ) -> None:
        self._queue_repository = queue_repository
        self._extraction_version = extraction_version

    def enqueue_for_ingestion(
        self,
        *,
        source_id: UUID,
        ingestion_job_id: UUID,
        publication_ids: Sequence[int],
        extraction_version: int | None = None,
    ) -> ExtractionEnqueueSummary:
        if not publication_ids:
            return ExtractionEnqueueSummary(
                source_id=source_id,
                ingestion_job_id=ingestion_job_id,
                extraction_version=extraction_version or self._extraction_version,
                requested=0,
                queued=0,
                skipped=0,
            )

        version = extraction_version or self._extraction_version
        now = datetime.now(UTC)
        items = [
            ExtractionQueueItem(
                id=uuid4(),
                publication_id=publication_id,
                pubmed_id=None,
                source_id=source_id,
                ingestion_job_id=ingestion_job_id,
                status=ExtractionStatus.PENDING,
                attempts=0,
                extraction_version=version,
                queued_at=now,
                updated_at=now,
            )
            for publication_id in publication_ids
        ]
        created = self._queue_repository.enqueue_many(items)
        queued = len(created)
        skipped = max(len(items) - queued, 0)
        if queued:
            logger.info(
                "Queued %s publications for extraction (source=%s, job=%s)",
                queued,
                source_id,
                ingestion_job_id,
            )
        return ExtractionEnqueueSummary(
            source_id=source_id,
            ingestion_job_id=ingestion_job_id,
            extraction_version=version,
            requested=len(items),
            queued=queued,
            skipped=skipped,
        )


__all__ = ["ExtractionEnqueueSummary", "ExtractionQueueService"]
