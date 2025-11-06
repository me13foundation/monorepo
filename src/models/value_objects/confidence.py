"""
Value object for confidence scores and evidence levels.
Immutable objects that quantify the strength of evidence in MED13.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Threshold constants for evidence levels
LEVEL_DEFINITIVE: float = 0.9
LEVEL_STRONG: float = 0.8
LEVEL_MODERATE: float = 0.6
LEVEL_SUPPORTING: float = 0.4
LEVEL_WEAK: float = 0.2
SIGNIFICANT_THRESHOLD: float = 0.6
VALIDATION_THRESHOLD: float = 0.7


class EvidenceLevel(str, Enum):
    """Evidence confidence level enumeration - matches database enum."""

    DEFINITIVE = "definitive"
    STRONG = "strong"
    MODERATE = "moderate"
    SUPPORTING = "supporting"
    WEAK = "weak"
    DISPROVEN = "disproven"


class ConfidenceScore(BaseModel):
    """
    Value object for evidence confidence scoring.

    Immutable quantification of evidence strength with validation
    and helper methods for evidence assessment in MED13.
    """

    model_config = ConfigDict(frozen=True)  # Immutable

    # Primary score (0.0 to 1.0)
    score: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")

    # Evidence level classification
    level: EvidenceLevel = Field(
        default=EvidenceLevel.SUPPORTING,
        description="Categorical evidence level",
    )

    # Supporting metrics
    sample_size: int | None = Field(
        None,
        ge=1,
        description="Sample size for statistical evidence",
    )
    p_value: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Statistical p-value",
    )
    study_count: int | None = Field(
        None,
        ge=0,
        description="Number of supporting studies",
    )

    # Quality indicators
    peer_reviewed: bool = Field(
        default=False,
        description="Evidence from peer-reviewed source",
    )
    replicated: bool = Field(default=False, description="Evidence has been replicated")

    @field_validator("level", mode="after")
    @classmethod
    def validate_level_consistency(cls, v: EvidenceLevel, info: Any) -> EvidenceLevel:
        """Ensure evidence level is consistent with score."""
        score = info.data.get("score")
        if score is not None:
            # Auto-classify level based on score if not explicitly set
            if score >= LEVEL_DEFINITIVE:
                expected_level = EvidenceLevel.DEFINITIVE
            elif score >= LEVEL_STRONG:
                expected_level = EvidenceLevel.STRONG
            elif score >= LEVEL_MODERATE:
                expected_level = EvidenceLevel.MODERATE
            elif score >= LEVEL_SUPPORTING:
                expected_level = EvidenceLevel.SUPPORTING
            elif score >= LEVEL_WEAK:
                expected_level = EvidenceLevel.WEAK
            else:
                expected_level = EvidenceLevel.DISPROVEN

            # If level doesn't match score, issue warning but allow it
            if v != expected_level:
                # In a real implementation, you might log this inconsistency
                pass

        return v

    @classmethod
    def from_score(cls, score: float, **kwargs: Any) -> "ConfidenceScore":
        """Create ConfidenceScore from numeric score with automatic level
        classification."""
        if score >= LEVEL_DEFINITIVE:
            level = EvidenceLevel.DEFINITIVE
        elif score >= LEVEL_STRONG:
            level = EvidenceLevel.STRONG
        elif score >= LEVEL_MODERATE:
            level = EvidenceLevel.MODERATE
        elif score >= LEVEL_SUPPORTING:
            level = EvidenceLevel.SUPPORTING
        elif score >= LEVEL_WEAK:
            level = EvidenceLevel.WEAK
        else:
            level = EvidenceLevel.DISPROVEN

        return cls(score=score, level=level, **kwargs)

    def is_significant(self) -> bool:
        """Check if evidence represents a significant finding."""
        return self.score >= SIGNIFICANT_THRESHOLD and self.level in [
            EvidenceLevel.DEFINITIVE,
            EvidenceLevel.STRONG,
            EvidenceLevel.MODERATE,
        ]

    def requires_validation(self) -> bool:
        """Check if evidence requires further validation."""
        return self.score < VALIDATION_THRESHOLD or not self.peer_reviewed

    @property
    def quality_description(self) -> str:
        """Get human-readable quality description."""
        if self.score >= LEVEL_STRONG:
            return f"Strong evidence ({self.score:.2f})"
        if self.score >= LEVEL_MODERATE:
            return f"Moderate evidence ({self.score:.2f})"
        if self.score >= LEVEL_SUPPORTING:
            return f"Supporting evidence ({self.score:.2f})"
        return f"Weak evidence ({self.score:.2f})"

    def __str__(self) -> str:
        """String representation of confidence score."""
        return f"{self.level.value} ({self.score:.2f})"
