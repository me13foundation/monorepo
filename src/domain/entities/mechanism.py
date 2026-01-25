"""
Mechanism entity for MED13 Resource Library.

Represents mechanistic nodes that connect protein domains to phenotypes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.domain.value_objects.confidence import EvidenceLevel

if TYPE_CHECKING:
    from src.domain.value_objects.protein_structure import ProteinDomain


class Mechanism(BaseModel):
    """
    Represents a biological mechanism used for mechanistic reasoning.
    """

    name: str
    description: str | None = None
    evidence_tier: EvidenceLevel = EvidenceLevel.SUPPORTING
    confidence_score: float = 0.5
    source: str = "manual_curation"

    # Structural context
    protein_domains: list[ProteinDomain] = Field(default_factory=list)

    # Phenotype linkage (database IDs)
    phenotype_ids: list[int] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    id: int | None = None

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    @field_validator("confidence_score")
    @classmethod
    def _validate_confidence(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            msg = "confidence_score must be between 0.0 and 1.0"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _validate_mechanism(self) -> Mechanism:
        if not self.name.strip():
            msg = "Mechanism name cannot be empty"
            raise ValueError(msg)
        return self


__all__ = ["Mechanism"]
