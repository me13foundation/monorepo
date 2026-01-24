"""Integration tests for extraction API endpoints."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text

from src.database import session as session_module
from src.main import create_app
from src.models.database import Base
from src.models.database.extraction_queue import ExtractionQueueItemModel
from src.models.database.ingestion_job import (
    IngestionJobModel,
    IngestionStatusEnum,
    IngestionTriggerEnum,
)
from src.models.database.publication import PublicationModel
from src.models.database.publication_extraction import (
    ExtractionOutcomeEnum,
    PublicationExtractionModel,
)
from src.models.database.storage import (
    StorageConfigurationModel,
    StorageProviderEnum,
)
from src.models.database.user_data_source import UserDataSourceModel

_READ_API_HEADERS = {
    "X-API-Key": "read-key-456",
    "X-TEST-USER-ID": "00000000-0000-0000-0000-000000000001",
    "X-TEST-USER-EMAIL": "test@example.com",
    "X-TEST-USER-ROLE": "read",
}

if TYPE_CHECKING:
    from pathlib import Path


def _reset_database() -> None:
    with session_module.engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            connection.execute(
                text("DROP TYPE IF EXISTS extraction_outcome_enum CASCADE"),
            )
            connection.execute(
                text("DROP TYPE IF EXISTS extraction_status_enum CASCADE"),
            )
    Base.metadata.drop_all(bind=session_module.engine)
    Base.metadata.create_all(bind=session_module.engine)


def _fetch_enum_values(
    session: session_module.SessionLocal,
    enum_name: str,
) -> set[str]:
    if session.bind.dialect.name != "postgresql":
        return set()
    rows = session.execute(
        text(f"SELECT unnest(enum_range(NULL::{enum_name}))"),
    ).fetchall()
    return {row[0] for row in rows}


def _choose_enum_value(
    values: set[str],
    preferred: tuple[str, ...],
    fallback: str,
) -> str:
    for candidate in preferred:
        if candidate in values:
            return candidate
    if values:
        return sorted(values)[0]
    return fallback


def _seed_source_and_job(
    session: session_module.SessionLocal,
) -> tuple[UUID, UUID]:
    source_id = uuid4()
    owner_id = uuid4()
    schedule_payload = {
        "enabled": True,
        "frequency": "hourly",
        "start_time": datetime.now(UTC).isoformat(),
        "timezone": "UTC",
        "backend_job_id": None,
    }
    metrics_payload = {
        "completeness_score": None,
        "consistency_score": None,
        "timeliness_score": None,
        "overall_score": None,
        "last_assessed": None,
        "issues_count": 0,
    }
    configuration_payload = {"metadata": {"query": "MED13"}}

    if session.bind.dialect.name == "postgresql":
        source_values = _fetch_enum_values(session, "sourcetypeenum")
        status_values = _fetch_enum_values(session, "sourcestatusenum")
        source_type = _choose_enum_value(
            source_values,
            ("PUBMED", "pubmed", "API", "api"),
            "API",
        )
        status = _choose_enum_value(
            status_values,
            ("ACTIVE", "active"),
            "ACTIVE",
        )

        session.execute(
            text(
                "INSERT INTO user_data_sources "
                "(id, owner_id, research_space_id, name, description, source_type, "
                "template_id, configuration, status, ingestion_schedule, "
                "quality_metrics, last_ingested_at, tags, version) "
                "VALUES "
                "(:id, :owner_id, :research_space_id, :name, :description, "
                ":source_type, :template_id, CAST(:configuration AS JSON), :status, "
                "CAST(:ingestion_schedule AS JSON), CAST(:quality_metrics AS JSON), "
                ":last_ingested_at, CAST(:tags AS JSON), :version)",
            ),
            {
                "id": str(source_id),
                "owner_id": str(owner_id),
                "research_space_id": None,
                "name": "PubMed Source",
                "description": "",
                "source_type": source_type,
                "template_id": None,
                "configuration": json.dumps(configuration_payload),
                "status": status,
                "ingestion_schedule": json.dumps(schedule_payload),
                "quality_metrics": json.dumps(metrics_payload),
                "last_ingested_at": None,
                "tags": json.dumps([]),
                "version": "1.0",
            },
        )
        session.commit()
    else:
        session.add(
            UserDataSourceModel(
                id=str(source_id),
                owner_id=str(owner_id),
                research_space_id=None,
                name="PubMed Source",
                description="",
                source_type="pubmed",
                template_id=None,
                configuration=configuration_payload,
                status="active",
                ingestion_schedule=schedule_payload,
                quality_metrics=metrics_payload,
                last_ingested_at=None,
                tags=[],
                version="1.0",
            ),
        )
        session.commit()

    job_id = uuid4()
    session.add(
        IngestionJobModel(
            id=str(job_id),
            source_id=str(source_id),
            trigger=IngestionTriggerEnum.SCHEDULED,
            triggered_by=None,
            triggered_at=datetime.now(UTC).isoformat(timespec="seconds"),
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
    return source_id, job_id


def _seed_publication(
    session: session_module.SessionLocal,
    pubmed_id: str,
) -> int:
    publication = PublicationModel(
        pubmed_id=pubmed_id,
        pmc_id=None,
        doi=None,
        title=f"MED13 paper {pubmed_id}",
        authors='["Tester"]',
        journal="Journal of Testing",
        publication_year=2024,
        publication_type="journal_article",
        abstract="Abstract",
        keywords='["med13"]',
        reviewed=False,
        open_access=False,
    )
    session.add(publication)
    session.commit()
    return publication.id


def _seed_queue_item(
    session: session_module.SessionLocal,
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


def _seed_extraction(
    session: session_module.SessionLocal,
    *,
    publication_id: int,
    source_id: UUID,
    ingestion_job_id: UUID,
    queue_item_id: UUID,
    status: ExtractionOutcomeEnum,
    document_reference: str | None = None,
) -> str:
    extraction_id = uuid4()
    now = datetime.now(UTC)
    session.add(
        PublicationExtractionModel(
            id=str(extraction_id),
            publication_id=publication_id,
            pubmed_id=str(publication_id),
            source_id=str(source_id),
            ingestion_job_id=str(ingestion_job_id),
            queue_item_id=str(queue_item_id),
            status=status,
            extraction_version=1,
            processor_name="rule_based",
            processor_version="1.0",
            text_source="title_abstract",
            document_reference=document_reference,
            facts=[{"fact_type": "gene", "value": "MED13"}],
            metadata_payload={"note": "api-test"},
            extracted_at=now,
            created_at=now,
            updated_at=now,
        ),
    )
    session.commit()
    return str(extraction_id)


def _seed_storage_configuration(
    session: session_module.SessionLocal,
    base_path: Path,
) -> UUID:
    config_id = uuid4()
    now = datetime.now(UTC)
    session.add(
        StorageConfigurationModel(
            id=str(config_id),
            name="Test Raw Source Storage",
            provider=StorageProviderEnum.LOCAL_FILESYSTEM,
            config_data={
                "provider": "local_filesystem",
                "base_path": str(base_path),
                "create_directories": True,
                "expose_file_urls": True,
            },
            enabled=True,
            supported_capabilities=["raw_source"],
            default_use_cases=["raw_source"],
            metadata_payload={},
            created_at=now,
            updated_at=now,
        ),
    )
    session.commit()
    return config_id


def _build_client() -> TestClient:
    app = create_app()
    return TestClient(app, headers=_READ_API_HEADERS)


def test_list_extractions_filters_status() -> None:
    _reset_database()
    session = session_module.SessionLocal()
    try:
        source_id, job_id = _seed_source_and_job(session)
        pub_one = _seed_publication(session, "555")
        queue_one = _seed_queue_item(
            session,
            publication_id=pub_one,
            source_id=source_id,
            ingestion_job_id=job_id,
        )
        completed_id = _seed_extraction(
            session,
            publication_id=pub_one,
            source_id=source_id,
            ingestion_job_id=job_id,
            queue_item_id=queue_one,
            status=ExtractionOutcomeEnum.COMPLETED,
        )

        pub_two = _seed_publication(session, "666")
        queue_two = _seed_queue_item(
            session,
            publication_id=pub_two,
            source_id=source_id,
            ingestion_job_id=job_id,
        )
        _seed_extraction(
            session,
            publication_id=pub_two,
            source_id=source_id,
            ingestion_job_id=job_id,
            queue_item_id=queue_two,
            status=ExtractionOutcomeEnum.SKIPPED,
        )
    finally:
        session.close()

    client = _build_client()
    response = client.get(
        "/extractions/",
        params={"status": "completed"},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == completed_id
    assert payload["items"][0]["status"] == "completed"


def test_get_extraction_by_id() -> None:
    _reset_database()
    session = session_module.SessionLocal()
    try:
        source_id, job_id = _seed_source_and_job(session)
        pub_id = _seed_publication(session, "777")
        queue_id = _seed_queue_item(
            session,
            publication_id=pub_id,
            source_id=source_id,
            ingestion_job_id=job_id,
        )
        extraction_id = _seed_extraction(
            session,
            publication_id=pub_id,
            source_id=source_id,
            ingestion_job_id=job_id,
            queue_item_id=queue_id,
            status=ExtractionOutcomeEnum.COMPLETED,
        )
    finally:
        session.close()

    client = _build_client()
    response = client.get(f"/extractions/{extraction_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == extraction_id
    assert payload["facts"][0]["fact_type"] == "gene"

    missing = client.get(f"/extractions/{uuid4()}")
    assert missing.status_code == 404


def test_get_extraction_document_url(tmp_path: Path) -> None:
    _reset_database()
    session = session_module.SessionLocal()
    try:
        base_path = tmp_path / "raw-storage"
        base_path.mkdir(parents=True, exist_ok=True)
        _seed_storage_configuration(session, base_path)

        source_id, job_id = _seed_source_and_job(session)
        pub_id = _seed_publication(session, "888")
        queue_id = _seed_queue_item(
            session,
            publication_id=pub_id,
            source_id=source_id,
            ingestion_job_id=job_id,
        )
        key = "extractions/test/doc.txt"
        file_path = base_path / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("stored document")
        extraction_id = _seed_extraction(
            session,
            publication_id=pub_id,
            source_id=source_id,
            ingestion_job_id=job_id,
            queue_item_id=queue_id,
            status=ExtractionOutcomeEnum.COMPLETED,
            document_reference=key,
        )
    finally:
        session.close()

    client = _build_client()
    response = client.get(f"/extractions/{extraction_id}/document-url")
    assert response.status_code == 200
    payload = response.json()
    assert payload["extraction_id"] == extraction_id
    assert payload["document_reference"] == key
    assert key in payload["url"]
