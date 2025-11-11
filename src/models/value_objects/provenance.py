"""
Value object for data provenance and lineage tracking.
Immutable objects that track the origin and history of MED13 data.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DataSource(str, Enum):
    """Enumeration of data sources for MED13."""

    CLINVAR = "clinvar"
    PUBMED = "pubmed"
    HPO = "hpo"
    UNIPROT = "uniprot"
    MANUAL = "manual"
    COMPUTED = "computed"


class Provenance(BaseModel):
    """
    Value object for tracking data provenance and lineage.

    Immutable record of where data came from, when it was acquired,
    and how it has been processed in the MED13 knowledge base.
    """

    model_config = ConfigDict(frozen=True)  # Immutable

    # Source information
    source: DataSource = Field(..., description="Original data source")
    source_version: str | None = Field(None, description="Version of source data")
    source_url: str | None = Field(None, description="URL where data was retrieved")

    # Acquisition metadata
    acquired_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When data was acquired",
    )
    acquired_by: str = Field(..., description="System/user that acquired the data")

    # Processing history
    processing_steps: list[str] = Field(
        default_factory=list,
        description="Sequence of processing steps applied",
    )

    # Quality and validation
    quality_score: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Data quality score (0-1)",
    )
    validation_status: str = Field(
        default="pending",
        description="Current validation status",
    )

    # Additional metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional source-specific metadata",
    )

    def add_processing_step(self, step: str) -> "Provenance":
        """Create new Provenance with additional processing step."""
        return self.model_copy(
            update={"processing_steps": [*self.processing_steps, step]},
        )

    def update_quality_score(self, score: float) -> "Provenance":
        """Create new Provenance with updated quality score."""
        return self.model_copy(
            update={"quality_score": score},
        )

    def mark_validated(self, status: str = "validated") -> "Provenance":
        """Create new Provenance with updated validation status."""
        return self.model_copy(
            update={"validation_status": status},
        )

    @property
    def is_validated(self) -> bool:
        """Check if data has been validated."""
        return self.validation_status in ["validated", "approved"]

    @property
    def processing_summary(self) -> str:
        """Get summary of processing history."""
        if not self.processing_steps:
            return "No processing steps recorded"
        return " → ".join(self.processing_steps)

    def __str__(self) -> str:
        """String representation of provenance."""
        return (
            f"{self.source.value} ({self.acquired_at.date()}) - "
            f"{self.validation_status}"
        )
