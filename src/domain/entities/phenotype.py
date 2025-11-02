from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Optional, Tuple

from src.domain.value_objects.identifiers import PhenotypeIdentifier


class PhenotypeCategory:
    CONGENITAL = "congenital"
    DEVELOPMENTAL = "developmental"
    NEUROLOGICAL = "neurological"
    CARDIOVASCULAR = "cardiovascular"
    MUSCULOSKELETAL = "musculoskeletal"
    ENDOCRINE = "endocrine"
    IMMUNOLOGICAL = "immunological"
    ONCOLOGICAL = "oncological"
    OTHER = "other"

    _VALID_CATEGORIES = {
        CONGENITAL,
        DEVELOPMENTAL,
        NEUROLOGICAL,
        CARDIOVASCULAR,
        MUSCULOSKELETAL,
        ENDOCRINE,
        IMMUNOLOGICAL,
        ONCOLOGICAL,
        OTHER,
    }

    @classmethod
    def validate(cls, value: str) -> str:
        normalized = value or cls.OTHER
        if normalized not in cls._VALID_CATEGORIES:
            raise ValueError(f"Unsupported phenotype category '{value}'")
        return normalized


@dataclass
class Phenotype:
    identifier: PhenotypeIdentifier
    name: str
    definition: Optional[str] = None
    synonyms: Tuple[str, ...] = field(default_factory=tuple)
    category: str = PhenotypeCategory.OTHER
    parent_hpo_id: Optional[str] = None
    is_root_term: bool = False
    frequency_in_med13: Optional[str] = None
    severity_score: Optional[int] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: Optional[int] = None

    def __post_init__(self) -> None:
        self.category = PhenotypeCategory.validate(self.category)
        self.synonyms = self._normalize_synonyms(self.synonyms)
        if not self.name:
            raise ValueError("Phenotype name cannot be empty")
        if self.severity_score is not None:
            if not (1 <= self.severity_score <= 5):
                raise ValueError("severity_score must be between 1 and 5")

    def add_synonym(self, synonym: str) -> None:
        cleaned = synonym.strip()
        if not cleaned:
            raise ValueError("synonym cannot be empty")
        if cleaned not in self.synonyms:
            self.synonyms = tuple((*self.synonyms, cleaned))
            self._touch()

    def update_definition(self, definition: Optional[str]) -> None:
        self.definition = definition
        self._touch()

    def update_category(self, category: str) -> None:
        self.category = PhenotypeCategory.validate(category)
        self._touch()

    def mark_as_root(self, *, parent_hpo_id: Optional[str] = None) -> None:
        self.is_root_term = True
        self.parent_hpo_id = parent_hpo_id
        self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now(UTC)

    @staticmethod
    def _normalize_synonyms(synonyms: Tuple[str, ...]) -> Tuple[str, ...]:
        seen: set[str] = set()
        normalized: list[str] = []
        for synonym in synonyms:
            cleaned = synonym.strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key not in seen:
                seen.add(key)
                normalized.append(cleaned)
        return tuple(normalized)


__all__ = ["Phenotype", "PhenotypeCategory"]
