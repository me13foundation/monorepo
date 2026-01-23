from __future__ import annotations

from uuid import uuid4

from src.domain.entities.extraction_queue_item import ExtractionQueueItem
from src.domain.entities.publication import Publication
from src.domain.value_objects.identifiers import PublicationIdentifier
from src.infrastructure.extraction.rule_based_pubmed_extraction_processor import (
    RuleBasedPubMedExtractionProcessor,
)


def _build_publication(*, title: str, abstract: str | None) -> Publication:
    return Publication(
        identifier=PublicationIdentifier(pubmed_id="123456"),
        title=title,
        authors=("Doe J",),
        journal="Test Journal",
        publication_year=2024,
        abstract=abstract,
    )


def _build_queue_item(publication_id: int) -> ExtractionQueueItem:
    return ExtractionQueueItem(
        id=uuid4(),
        publication_id=publication_id,
        pubmed_id="123456",
        source_id=uuid4(),
        ingestion_job_id=uuid4(),
    )


def test_rule_based_extraction_finds_facts() -> None:
    publication = _build_publication(
        title="MED13 variant c.123A>G linked to HP:0001249",
        abstract="We report p.Arg123His in MED13 patients.",
    )
    queue_item = _build_queue_item(publication_id=1)
    processor = RuleBasedPubMedExtractionProcessor()

    result = processor.extract_publication(
        queue_item=queue_item,
        publication=publication,
    )

    values = {fact["value"] for fact in result.facts}
    assert result.status == "completed"
    assert "MED13" in values
    assert "c.123A>G" in values
    assert "p.Arg123His" in values
    assert "HP:0001249" in values


def test_rule_based_extraction_skips_when_no_facts() -> None:
    publication = _build_publication(
        title="Unrelated study of cell signaling",
        abstract="This work studies unrelated pathways.",
    )
    queue_item = _build_queue_item(publication_id=2)
    processor = RuleBasedPubMedExtractionProcessor()

    result = processor.extract_publication(
        queue_item=queue_item,
        publication=publication,
    )

    assert result.status == "skipped"
    assert result.facts == []
