from __future__ import annotations

from datetime import UTC, date, datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.domain.entities.variant import VariantSummary  # noqa: TC001
from src.domain.value_objects.confidence import Confidence, EvidenceLevel
from src.domain.value_objects.identifiers import (  # noqa: TC001
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

    _VALID_TYPES: ClassVar[set[str]] = {
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
            msg = f"Unsupported evidence type '{value}'"
            raise ValueError(msg)
        return normalized


QUALITY_SCORE_MAX = 10


class Evidence(BaseModel):
    variant_id: int
    phenotype_id: int
    description: str
    evidence_level: EvidenceLevel = EvidenceLevel.SUPPORTING
    evidence_type: str = EvidenceType.LITERATURE_REVIEW
    confidence: Confidence = Field(
        default_factory=lambda: Confidence.from_score(0.5),
    )
    summary: str | None = None
    publication_id: int | None = None
    phenotype_identifier: PhenotypeIdentifier | None = None
    variant_identifier: VariantIdentifier | None = None
    publication_identifier: PublicationIdentifier | None = None
    variant_summary: VariantSummary | None = None
    quality_score: int | None = None
    sample_size: int | None = None
    study_type: str | None = None
    statistical_significance: str | None = None
    reviewed: bool = False
    review_date: date | None = None
    reviewer_notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    id: int | None = None

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    @field_validator("evidence_type")
    @classmethod
    def _validate_type(cls, value: str) -> str:
        return EvidenceType.validate(value)

    @model_validator(mode="after")
    def _validate_values(self) -> Evidence:
        if not self.description:
            msg = "Evidence description cannot be empty"
            raise ValueError(msg)
        if self.quality_score is not None and not (
            1 <= self.quality_score <= QUALITY_SCORE_MAX
        ):
            msg = f"quality_score must be between 1 and {QUALITY_SCORE_MAX}"
            raise ValueError(msg)
        if self.sample_size is not None and self.sample_size < 1:
            msg = "sample_size must be positive"
            raise ValueError(msg)

        aligned_confidence = self._ensure_confidence_alignment(self.confidence)
        if aligned_confidence is not self.confidence:
            return self.model_copy(
                update={"confidence": aligned_confidence},  # type: ignore[misc]
            )
        return self

    def mark_reviewed(
        self,
        *,
        reviewed: bool = True,
        review_date: date | None = None,
    ) -> None:
        self.reviewed = reviewed
        self.review_date = review_date
        self._touch()

    def attach_publication(
        self,
        publication_id: int,
        identifier: PublicationIdentifier,
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
