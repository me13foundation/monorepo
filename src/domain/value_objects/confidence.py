from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, Optional


class EvidenceLevel(str, Enum):
    """Evidence confidence level enumeration."""

    DEFINITIVE = "definitive"
    STRONG = "strong"
    MODERATE = "moderate"
    SUPPORTING = "supporting"
    WEAK = "weak"
    DISPROVEN = "disproven"


@dataclass(frozen=True)
class Confidence:
    score: float
    level: EvidenceLevel
    sample_size: Optional[int] = None
    p_value: Optional[float] = None
    study_count: Optional[int] = None
    peer_reviewed: bool = False
    replicated: bool = False

    def __post_init__(self) -> None:
        if not (0.0 <= self.score <= 1.0):
            raise ValueError("score must be between 0.0 and 1.0")
        if self.sample_size is not None and self.sample_size < 1:
            raise ValueError("sample_size must be positive")
        if self.p_value is not None and not (0.0 <= self.p_value <= 1.0):
            raise ValueError("p_value must be between 0.0 and 1.0")
        if self.study_count is not None and self.study_count < 0:
            raise ValueError("study_count cannot be negative")

    @classmethod
    def from_score(cls, score: float, **kwargs: Any) -> Confidence:
        level = cls._infer_level(score)
        return cls(score=score, level=level, **kwargs)

    @staticmethod
    def _infer_level(score: float) -> EvidenceLevel:
        if score >= 0.9:
            return EvidenceLevel.DEFINITIVE
        if score >= 0.8:
            return EvidenceLevel.STRONG
        if score >= 0.6:
            return EvidenceLevel.MODERATE
        if score >= 0.4:
            return EvidenceLevel.SUPPORTING
        if score >= 0.2:
            return EvidenceLevel.WEAK
        return EvidenceLevel.DISPROVEN

    def update_level(self, level: EvidenceLevel) -> Confidence:
        return replace(self, level=level)

    def is_significant(self) -> bool:
        return self.score >= 0.6 and self.level in {
            EvidenceLevel.DEFINITIVE,
            EvidenceLevel.STRONG,
            EvidenceLevel.MODERATE,
        }

    def requires_validation(self) -> bool:
        return self.score < 0.7 or not self.peer_reviewed

    @property
    def quality_description(self) -> str:
        if self.score >= 0.8:
            return f"Strong evidence ({self.score:.2f})"
        if self.score >= 0.6:
            return f"Moderate evidence ({self.score:.2f})"
        if self.score >= 0.4:
            return f"Supporting evidence ({self.score:.2f})"
        return f"Weak evidence ({self.score:.2f})"

    def __str__(self) -> str:
        return f"{self.level.value} ({self.score:.2f})"


__all__ = ["Confidence", "EvidenceLevel"]
