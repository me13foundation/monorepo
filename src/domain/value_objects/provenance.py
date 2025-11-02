from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import Enum
from typing import Mapping, MutableSequence, Optional, Sequence


class DataSource(str, Enum):
    """Enumeration of domain-level data sources."""

    CLINVAR = "clinvar"
    PUBMED = "pubmed"
    HPO = "hpo"
    UNIPROT = "uniprot"
    MANUAL = "manual"
    COMPUTED = "computed"


@dataclass(frozen=True)
class Provenance:
    source: DataSource
    acquired_by: str
    source_version: Optional[str] = None
    source_url: Optional[str] = None
    acquired_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    processing_steps: Sequence[str] = field(default_factory=tuple)
    quality_score: Optional[float] = None
    validation_status: str = "pending"
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.acquired_by:
            raise ValueError("acquired_by must be provided")
        if self.quality_score is not None and not (0.0 <= self.quality_score <= 1.0):
            raise ValueError("quality_score must be between 0.0 and 1.0")
        if isinstance(self.processing_steps, MutableSequence):
            object.__setattr__(self, "processing_steps", tuple(self.processing_steps))

    def add_processing_step(self, step: str) -> Provenance:
        """Return a new Provenance with an additional processing step."""
        if not step:
            raise ValueError("processing step cannot be empty")
        return replace(self, processing_steps=tuple(self.processing_steps) + (step,))

    def update_quality_score(self, score: float) -> Provenance:
        """Return a new Provenance with an updated quality score."""
        if not (0.0 <= score <= 1.0):
            raise ValueError("quality_score must be between 0.0 and 1.0")
        return replace(self, quality_score=score)

    def mark_validated(self, status: str = "validated") -> Provenance:
        """Return a new Provenance with updated validation status."""
        if not status:
            raise ValueError("validation status cannot be empty")
        return replace(self, validation_status=status)

    @property
    def is_validated(self) -> bool:
        return self.validation_status in ("validated", "approved")

    @property
    def processing_summary(self) -> str:
        if not self.processing_steps:
            return "No processing steps recorded"
        return " → ".join(self.processing_steps)

    def __str__(self) -> str:
        return f"{self.source.value} ({self.acquired_at.date()}) - {self.validation_status}"


__all__ = ["Provenance", "DataSource"]
