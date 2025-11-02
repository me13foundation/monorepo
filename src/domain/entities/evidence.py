from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, date
from typing import Optional

from src.domain.entities.variant import VariantSummary
from src.domain.value_objects.confidence import Confidence, EvidenceLevel
from src.domain.value_objects.identifiers import (
    PhenotypeIdentifier,
    PublicationIdentifier,
    VariantIdentifier,
)


class EvidenceType:
    CLINICAL_REPORT = "clinical_report"
    FUNCTIONAL_STUDY = "functional_study"
    ANIMAL_MODEL = "animal_model"
    BIOCHEMICAL = "biochemical"
    COMPUTATIONAL = "computational"
    LITERATURE_REVIEW = "literature_review"
    EXPERT_OPINION = "expert_opinion"

    _VALID_TYPES = {
        CLINICAL_REPORT,
        FUNCTIONAL_STUDY,
        ANIMAL_MODEL,
        BIOCHEMICAL,
        COMPUTATIONAL,
        LITERATURE_REVIEW,
        EXPERT_OPINION,
    }

    @classmethod
    def validate(cls, value: str) -> str:
        normalized = value or cls.LITERATURE_REVIEW
        if normalized not in cls._VALID_TYPES:
            raise ValueError(f"Unsupported evidence type '{value}'")
        return normalized


@dataclass
class Evidence:
    variant_id: int
    phenotype_id: int
    description: str
    evidence_level: EvidenceLevel = EvidenceLevel.SUPPORTING
    evidence_type: str = EvidenceType.LITERATURE_REVIEW
    confidence: Confidence = field(default_factory=lambda: Confidence.from_score(0.5))
    summary: Optional[str] = None
    publication_id: Optional[int] = None
    phenotype_identifier: Optional[PhenotypeIdentifier] = None
    variant_identifier: Optional[VariantIdentifier] = None
    publication_identifier: Optional[PublicationIdentifier] = None
    variant_summary: Optional[VariantSummary] = None
    quality_score: Optional[int] = None
    sample_size: Optional[int] = None
    study_type: Optional[str] = None
    statistical_significance: Optional[str] = None
    reviewed: bool = False
    review_date: Optional[date] = None
    reviewer_notes: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: Optional[int] = None

    def __post_init__(self) -> None:
        self.evidence_type = EvidenceType.validate(self.evidence_type)
        self.confidence = self._ensure_confidence_alignment(self.confidence)
        if not self.description:
            raise ValueError("Evidence description cannot be empty")
        if self.quality_score is not None and not (1 <= self.quality_score <= 10):
            raise ValueError("quality_score must be between 1 and 10")
        if self.sample_size is not None and self.sample_size < 1:
            raise ValueError("sample_size must be positive")

    def mark_reviewed(
        self, reviewed: bool = True, *, review_date: Optional[date] = None
    ) -> None:
        self.reviewed = reviewed
        self.review_date = review_date
        self._touch()

    def attach_publication(
        self, publication_id: int, identifier: PublicationIdentifier
    ) -> None:
        self.publication_id = publication_id
        self.publication_identifier = identifier
        self._touch()

    def update_confidence(self, confidence: Confidence) -> None:
        self.confidence = self._ensure_confidence_alignment(confidence)
        self._touch()

    def _ensure_confidence_alignment(self, confidence: Confidence) -> Confidence:
        if confidence.level != self.evidence_level:
            return confidence.update_level(self.evidence_level)
        return confidence

    def _touch(self) -> None:
        self.updated_at = datetime.now(UTC)


__all__ = ["Evidence", "EvidenceType"]
