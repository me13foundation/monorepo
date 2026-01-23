"""Unit tests for the extraction runner service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from src.application.services.extraction_runner_service import ExtractionRunnerService
from src.application.services.ports.extraction_processor_port import (
    ExtractionProcessorResult,
)
from src.domain.entities.extraction_queue_item import (
    ExtractionQueueItem,
    ExtractionStatus,
)
from src.domain.entities.publication import Publication
from src.domain.entities.publication_extraction import (
    ExtractionOutcome,
    ExtractionTextSource,
    PublicationExtraction,
)
from src.domain.value_objects.identifiers import PublicationIdentifier

if TYPE_CHECKING:
    from src.type_definitions.common import (
        ExtractionFact,
        JSONObject,
        PublicationExtractionUpdate,
    )


class StubQueueRepository:
    def __init__(self, items: list[ExtractionQueueItem]) -> None:
        self._items = items
        self.completed_metadata: list[JSONObject] = []
        self.failed: list[str] = []

    def claim_pending(
        self,
        *,
        limit: int,
        source_id: UUID | None = None,
        ingestion_job_id: UUID | None = None,
    ) -> list[ExtractionQueueItem]:
        return self._items[:limit]

    def mark_completed(
        self,
        item_id: UUID,
        *,
        metadata: JSONObject | None = None,
    ) -> ExtractionQueueItem:
        if metadata:
            self.completed_metadata.append(metadata)
        return self._items[0]

    def mark_failed(self, item_id: UUID, *, error_message: str) -> ExtractionQueueItem:
        self.failed.append(error_message)
        return self._items[0]


class StubPublicationRepository:
    def __init__(self, publication: Publication) -> None:
        self._publication = publication

    def get_by_id(self, publication_id: int) -> Publication | None:
        if self._publication.id == publication_id:
            return self._publication
        return None


class StubExtractionRepository:
    def __init__(self, existing: PublicationExtraction | None = None) -> None:
        self._existing = existing
        self.created: list[PublicationExtraction] = []
        self.updated: list[PublicationExtractionUpdate] = []

    def find_by_queue_item_id(
        self,
        queue_item_id: UUID,
    ) -> PublicationExtraction | None:
        return self._existing

    def create(self, entity: PublicationExtraction) -> PublicationExtraction:
        self.created.append(entity)
        return entity

    def update(
        self,
        entity_id: UUID,
        updates: PublicationExtractionUpdate,
    ) -> PublicationExtraction:
        self.updated.append(updates)
        if self._existing is None:
            return self.created[-1]
        return self._existing


@dataclass(frozen=True)
class StubProcessor:
    result: ExtractionProcessorResult

    def extract_publication(
        self,
        *,
        queue_item: ExtractionQueueItem,
        publication: Publication | None,
    ) -> ExtractionProcessorResult:
        return self.result


def _build_queue_item() -> ExtractionQueueItem:
    return ExtractionQueueItem(
        id=uuid4(),
        publication_id=101,
        pubmed_id="123456",
        source_id=uuid4(),
        ingestion_job_id=uuid4(),
        status=ExtractionStatus.PENDING,
        attempts=0,
        last_error=None,
        extraction_version=1,
        metadata={},
        queued_at=datetime.now(UTC),
        started_at=None,
        completed_at=None,
        updated_at=datetime.now(UTC),
    )


def _build_publication(publication_id: int) -> Publication:
    return Publication(
        identifier=PublicationIdentifier(pubmed_id="123456"),
        title="MED13 case report",
        authors=("Tester",),
        journal="Journal",
        publication_year=2024,
        publication_type="journal_article",
        abstract="Abstract",
        keywords=("med13",),
        id=publication_id,
    )


def _build_result(status: ExtractionOutcome) -> ExtractionProcessorResult:
    facts: list[ExtractionFact] = [{"fact_type": "gene", "value": "MED13"}]
    return ExtractionProcessorResult(
        status=status,
        facts=facts,
        metadata={},
        processor_name="rule_based",
        processor_version="1.0",
        text_source="title_abstract",
        document_reference=None,
        error_message=None,
    )


def test_run_pending_persists_new_extraction() -> None:
    item = _build_queue_item()
    publication = _build_publication(item.publication_id)
    queue_repo = StubQueueRepository([item])
    extraction_repo = StubExtractionRepository()
    processor = StubProcessor(_build_result(ExtractionOutcome.COMPLETED))

    runner = ExtractionRunnerService(
        queue_repository=queue_repo,
        publication_repository=StubPublicationRepository(publication),
        extraction_repository=extraction_repo,
        processor=processor,
        batch_size=1,
    )

    summary = runner.run_pending()

    assert summary.completed == 1
    assert len(extraction_repo.created) == 1
    assert queue_repo.completed_metadata
    metadata = queue_repo.completed_metadata[0]
    assert metadata.get("extraction_id") == str(extraction_repo.created[0].id)


def test_run_pending_updates_existing_extraction() -> None:
    item = _build_queue_item()
    publication = _build_publication(item.publication_id)
    existing = PublicationExtraction(
        id=uuid4(),
        publication_id=item.publication_id,
        pubmed_id=item.pubmed_id,
        source_id=item.source_id,
        ingestion_job_id=item.ingestion_job_id,
        queue_item_id=item.id,
        status=ExtractionOutcome.COMPLETED,
        extraction_version=1,
        processor_name="rule_based",
        processor_version="1.0",
        text_source=ExtractionTextSource.TITLE_ABSTRACT,
        document_reference=None,
        facts=[],
        metadata={},
        extracted_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    queue_repo = StubQueueRepository([item])
    extraction_repo = StubExtractionRepository(existing=existing)
    processor = StubProcessor(_build_result(ExtractionOutcome.COMPLETED))

    runner = ExtractionRunnerService(
        queue_repository=queue_repo,
        publication_repository=StubPublicationRepository(publication),
        extraction_repository=extraction_repo,
        processor=processor,
        batch_size=1,
    )

    summary = runner.run_pending()

    assert summary.completed == 1
    assert extraction_repo.updated
    metadata = queue_repo.completed_metadata[0]
    assert metadata.get("extraction_id") == str(existing.id)
