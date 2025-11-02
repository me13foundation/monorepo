from datetime import date

from src.domain.entities.publication import Publication, PublicationType
from src.domain.entities.evidence import Evidence, EvidenceType
from src.domain.value_objects.confidence import Confidence, EvidenceLevel
from src.domain.value_objects.identifiers import PublicationIdentifier


def build_publication() -> Publication:
    identifier = PublicationIdentifier(pubmed_id="12345678")
    return Publication(
        identifier=identifier,
        title="Insights into MED13",
        authors=("Smith A", "Doe B"),
        journal="Genetics Journal",
        publication_year=2023,
        publication_type=PublicationType.JOURNAL_ARTICLE,
        keywords=("med13", "genetics"),
    )


def test_publication_add_evidence_updates_state() -> None:
    publication = build_publication()

    confidence = Confidence.from_score(0.8, peer_reviewed=True)
    evidence = Evidence(
        variant_id=1,
        phenotype_id=1,
        description="Supporting study",
        evidence_level=EvidenceLevel.STRONG,
        evidence_type=EvidenceType.CLINICAL_REPORT,
        confidence=confidence,
        review_date=date(2023, 5, 1),
    )

    publication.add_evidence(evidence)

    assert len(publication.evidence) == 1
    assert publication.reviewed is False


def test_publication_relevance_validation() -> None:
    publication = build_publication()
    publication.update_relevance(5)
    assert publication.relevance_score == 5
