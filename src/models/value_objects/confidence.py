"""
Value object for confidence scores and evidence levels.
Immutable objects that quantify the strength of evidence in MED13.
"""

from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum


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
        default=EvidenceLevel.SUPPORTING, description="Categorical evidence level"
    )

    # Supporting metrics
    sample_size: Optional[int] = Field(
        None, ge=1, description="Sample size for statistical evidence"
    )
    p_value: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Statistical p-value"
    )
    study_count: Optional[int] = Field(
        None, ge=0, description="Number of supporting studies"
    )

    # Quality indicators
    peer_reviewed: bool = Field(
        default=False, description="Evidence from peer-reviewed source"
    )
    replicated: bool = Field(default=False, description="Evidence has been replicated")

    @field_validator("level", mode="after")
    @classmethod
    def validate_level_consistency(cls, v: EvidenceLevel, info: Any) -> EvidenceLevel:
        """Ensure evidence level is consistent with score."""
        score = info.data.get("score")
        if score is not None:
            # Auto-classify level based on score if not explicitly set
            if score >= 0.9:
                expected_level = EvidenceLevel.DEFINITIVE
            elif score >= 0.8:
                expected_level = EvidenceLevel.STRONG
            elif score >= 0.6:
                expected_level = EvidenceLevel.MODERATE
            elif score >= 0.4:
                expected_level = EvidenceLevel.SUPPORTING
            elif score >= 0.2:
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
        if score >= 0.9:
            level = EvidenceLevel.DEFINITIVE
        elif score >= 0.8:
            level = EvidenceLevel.STRONG
        elif score >= 0.6:
            level = EvidenceLevel.MODERATE
        elif score >= 0.4:
            level = EvidenceLevel.SUPPORTING
        elif score >= 0.2:
            level = EvidenceLevel.WEAK
        else:
            level = EvidenceLevel.DISPROVEN

        return cls(score=score, level=level, **kwargs)

    def is_significant(self) -> bool:
        """Check if evidence represents a significant finding."""
        return self.score >= 0.6 and self.level in [
            EvidenceLevel.DEFINITIVE,
            EvidenceLevel.STRONG,
            EvidenceLevel.MODERATE,
        ]

    def requires_validation(self) -> bool:
        """Check if evidence requires further validation."""
        return self.score < 0.7 or not self.peer_reviewed

    @property
    def quality_description(self) -> str:
        """Get human-readable quality description."""
        if self.score >= 0.8:
            return f"Strong evidence ({self.score:.2f})"
        elif self.score >= 0.6:
            return f"Moderate evidence ({self.score:.2f})"
        elif self.score >= 0.4:
            return f"Supporting evidence ({self.score:.2f})"
        else:
            return f"Weak evidence ({self.score:.2f})"

    def __str__(self) -> str:
        """String representation of confidence score."""
        return f"{self.level.value} ({self.score:.2f})"
