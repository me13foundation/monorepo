"""Unit tests for publication extraction mapper."""

from datetime import UTC, datetime
from uuid import uuid4

from src.domain.entities.publication_extraction import (
    ExtractionOutcome,
    ExtractionTextSource,
    PublicationExtraction,
)
from src.infrastructure.mappers.publication_extraction_mapper import (
    PublicationExtractionMapper,
)
from src.models.database.publication_extraction import (
    ExtractionOutcomeEnum,
    PublicationExtractionModel,
)


def test_mapper_coerces_fact_payload() -> None:
    now = datetime.now(UTC)
    model = PublicationExtractionModel(
        id=str(uuid4()),
        publication_id=1,
        pubmed_id="12345",
        source_id=str(uuid4()),
        ingestion_job_id=str(uuid4()),
        queue_item_id=str(uuid4()),
        status=ExtractionOutcomeEnum.COMPLETED,
        extraction_version=1,
        processor_name="rule_based",
        processor_version="1.0",
        text_source="title_abstract",
        document_reference=None,
        facts=[
            {
                "fact_type": "unknown",
                "value": 123,
                "normalized_id": 99,
                "attributes": ["not-a-dict"],
            },
        ],
        metadata_payload={"note": "test"},
        extracted_at=now,
        created_at=now,
        updated_at=now,
    )

    entity = PublicationExtractionMapper.to_domain(model)

    assert entity.facts[0]["fact_type"] == "other"
    assert entity.facts[0]["value"] == "123"
    assert entity.facts[0]["normalized_id"] == "99"
    assert "attributes" not in entity.facts[0]


def test_mapper_to_model_round_trip() -> None:
    now = datetime.now(UTC)
    extraction = PublicationExtraction(
        id=uuid4(),
        publication_id=10,
        pubmed_id="77777",
        source_id=uuid4(),
        ingestion_job_id=uuid4(),
        queue_item_id=uuid4(),
        status=ExtractionOutcome.COMPLETED,
        extraction_version=2,
        processor_name="rule_based",
        processor_version="1.0",
        text_source=ExtractionTextSource.TITLE_ABSTRACT,
        document_reference=None,
        facts=[{"fact_type": "gene", "value": "MED13"}],
        metadata={"note": "round-trip"},
        extracted_at=now,
        created_at=now,
        updated_at=now,
    )

    model = PublicationExtractionMapper.to_model(extraction)

    assert model.status == ExtractionOutcomeEnum.COMPLETED
    assert model.text_source == "title_abstract"
    assert model.facts[0]["fact_type"] == "gene"
    assert model.metadata_payload["note"] == "round-trip"
