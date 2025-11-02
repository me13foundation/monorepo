from datetime import date

from src.domain.entities.evidence import Evidence, EvidenceType
from src.domain.value_objects.confidence import Confidence, EvidenceLevel


def test_evidence_confidence_alignment() -> None:
    confidence = Confidence.from_score(0.9, peer_reviewed=False)
    evidence = Evidence(
        variant_id=1,
        phenotype_id=2,
        description="Functional assay",
        evidence_level=EvidenceLevel.DEFINITIVE,
        evidence_type=EvidenceType.FUNCTIONAL_STUDY,
        confidence=confidence,
        quality_score=8,
        reviewed=True,
        review_date=date(2024, 1, 1),
    )

    assert evidence.confidence.level == EvidenceLevel.DEFINITIVE
    assert evidence.reviewed is True


def test_evidence_quality_validation() -> None:
    confidence = Confidence.from_score(0.6)
    evidence = Evidence(
        variant_id=1,
        phenotype_id=1,
        description="Literature review",
        evidence_level=EvidenceLevel.MODERATE,
        evidence_type=EvidenceType.LITERATURE_REVIEW,
        confidence=confidence,
    )

    evidence.update_confidence(Confidence.from_score(0.7))
    assert evidence.confidence.score == 0.7
