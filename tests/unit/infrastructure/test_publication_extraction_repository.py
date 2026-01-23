"""Tests for the SQLAlchemy publication extraction repository."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.domain.entities.publication_extraction import (
    ExtractionOutcome,
    ExtractionTextSource,
    PublicationExtraction,
)
from src.domain.repositories.base import QuerySpecification
from src.infrastructure.repositories import SqlAlchemyPublicationExtractionRepository
from src.models.database import (
    Base,
    ExtractionQueueItemModel,
    IngestionJobModel,
    PublicationModel,
    UserDataSourceModel,
)
from src.models.database.ingestion_job import (
    IngestionStatusEnum,
    IngestionTriggerEnum,
)


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def _seed_source(session) -> UUID:
    source_id = uuid4()
    session.add(
        UserDataSourceModel(
            id=str(source_id),
            owner_id=str(uuid4()),
            research_space_id=None,
            name="PubMed Source",
            description="",
            source_type="pubmed",
            template_id=None,
            configuration={"metadata": {"query": "MED13"}},
            status="active",
            ingestion_schedule={
                "enabled": True,
                "frequency": "hourly",
                "start_time": datetime.now(UTC).isoformat(),
                "timezone": "UTC",
                "backend_job_id": None,
            },
            quality_metrics={
                "completeness_score": None,
                "consistency_score": None,
                "timeliness_score": None,
                "overall_score": None,
                "last_assessed": None,
                "issues_count": 0,
            },
            last_ingested_at=None,
            tags=[],
            version="1.0",
        ),
    )
    session.commit()
    return source_id


def _seed_ingestion_job(session, source_id: UUID) -> UUID:
    job_id = uuid4()
    session.add(
        IngestionJobModel(
            id=str(job_id),
            source_id=str(source_id),
            trigger=IngestionTriggerEnum.SCHEDULED,
            triggered_by=None,
            triggered_at=datetime.now(UTC).isoformat(),
            status=IngestionStatusEnum.COMPLETED,
            started_at=None,
            completed_at=None,
            metrics={},
            errors=[],
            provenance={},
            job_metadata={},
            source_config_snapshot={"metadata": {"query": "MED13"}},
        ),
    )
    session.commit()
    return job_id


def _seed_publication(session, *, pubmed_id: str) -> int:
    publication = PublicationModel(
        pubmed_id=pubmed_id,
        pmc_id=None,
        doi=None,
        title="MED13 case report",
        authors='["Tester"]',
        journal="Journal of Testing",
        publication_year=2024,
        publication_type="journal_article",
        abstract="MED13 case report abstract",
        keywords='["med13"]',
        reviewed=False,
        open_access=False,
    )
    session.add(publication)
    session.commit()
    return publication.id


def _seed_queue_item(
    session,
    *,
    publication_id: int,
    source_id: UUID,
    ingestion_job_id: UUID,
) -> UUID:
    queue_id = uuid4()
    session.add(
        ExtractionQueueItemModel(
            id=str(queue_id),
            publication_id=publication_id,
            pubmed_id=str(publication_id),
            source_id=str(source_id),
            ingestion_job_id=str(ingestion_job_id),
            status="pending",
            attempts=0,
            last_error=None,
            extraction_version=1,
            metadata_payload={},
            queued_at=datetime.now(UTC),
            started_at=None,
            completed_at=None,
            updated_at=datetime.now(UTC),
        ),
    )
    session.commit()
    return queue_id


def _build_extraction(
    *,
    publication_id: int,
    pubmed_id: str,
    source_id: UUID,
    ingestion_job_id: UUID,
    queue_item_id: UUID,
    status: ExtractionOutcome,
) -> PublicationExtraction:
    now = datetime.now(UTC)
    return PublicationExtraction(
        id=uuid4(),
        publication_id=publication_id,
        pubmed_id=pubmed_id,
        source_id=source_id,
        ingestion_job_id=ingestion_job_id,
        queue_item_id=queue_item_id,
        status=status,
        extraction_version=1,
        processor_name="rule_based",
        processor_version="1.0",
        text_source=ExtractionTextSource.TITLE_ABSTRACT,
        document_reference=None,
        facts=[{"fact_type": "gene", "value": "MED13"}],
        metadata={"note": "test"},
        extracted_at=now,
        created_at=now,
        updated_at=now,
    )


def test_create_and_find_by_queue_item(session) -> None:
    source_id = _seed_source(session)
    job_id = _seed_ingestion_job(session, source_id)
    publication_id = _seed_publication(session, pubmed_id="111")
    queue_id = _seed_queue_item(
        session,
        publication_id=publication_id,
        source_id=source_id,
        ingestion_job_id=job_id,
    )

    repository = SqlAlchemyPublicationExtractionRepository(session)
    extraction = _build_extraction(
        publication_id=publication_id,
        pubmed_id="111",
        source_id=source_id,
        ingestion_job_id=job_id,
        queue_item_id=queue_id,
        status=ExtractionOutcome.COMPLETED,
    )

    created = repository.create(extraction)
    assert created.id == extraction.id

    fetched = repository.find_by_queue_item_id(queue_id)
    assert fetched is not None
    assert fetched.status == ExtractionOutcome.COMPLETED
    assert fetched.facts[0]["value"] == "MED13"


def test_find_and_count_by_criteria(session) -> None:
    source_id = _seed_source(session)
    job_id = _seed_ingestion_job(session, source_id)

    publication_id = _seed_publication(session, pubmed_id="222")
    queue_id = _seed_queue_item(
        session,
        publication_id=publication_id,
        source_id=source_id,
        ingestion_job_id=job_id,
    )
    repository = SqlAlchemyPublicationExtractionRepository(session)
    extraction = _build_extraction(
        publication_id=publication_id,
        pubmed_id="222",
        source_id=source_id,
        ingestion_job_id=job_id,
        queue_item_id=queue_id,
        status=ExtractionOutcome.COMPLETED,
    )
    repository.create(extraction)

    publication_id_two = _seed_publication(session, pubmed_id="333")
    queue_id_two = _seed_queue_item(
        session,
        publication_id=publication_id_two,
        source_id=source_id,
        ingestion_job_id=job_id,
    )
    extraction_two = _build_extraction(
        publication_id=publication_id_two,
        pubmed_id="333",
        source_id=source_id,
        ingestion_job_id=job_id,
        queue_item_id=queue_id_two,
        status=ExtractionOutcome.SKIPPED,
    )
    repository.create(extraction_two)

    spec = QuerySpecification(filters={"status": "completed"})
    completed = repository.find_by_criteria(spec)
    assert len(completed) == 1
    assert completed[0].status == ExtractionOutcome.COMPLETED

    count = repository.count_by_criteria(
        QuerySpecification(filters={"source_id": source_id}),
    )
    assert count == 2


def test_update_status(session) -> None:
    source_id = _seed_source(session)
    job_id = _seed_ingestion_job(session, source_id)
    publication_id = _seed_publication(session, pubmed_id="444")
    queue_id = _seed_queue_item(
        session,
        publication_id=publication_id,
        source_id=source_id,
        ingestion_job_id=job_id,
    )

    repository = SqlAlchemyPublicationExtractionRepository(session)
    extraction = _build_extraction(
        publication_id=publication_id,
        pubmed_id="444",
        source_id=source_id,
        ingestion_job_id=job_id,
        queue_item_id=queue_id,
        status=ExtractionOutcome.COMPLETED,
    )
    created = repository.create(extraction)

    updated = repository.update(
        created.id,
        {
            "status": "failed",
            "metadata": {"error": "timeout"},
        },
    )

    assert updated.status == ExtractionOutcome.FAILED
    assert updated.metadata["error"] == "timeout"
