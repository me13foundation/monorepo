from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
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

    _VALID_CATEGORIES: ClassVar[set[str]] = {
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
            msg = f"Unsupported phenotype category '{value}'"
            raise ValueError(msg)
        return normalized


@dataclass
class Phenotype:
    identifier: PhenotypeIdentifier
    name: str
    definition: str | None = None
    synonyms: tuple[str, ...] = field(default_factory=tuple)
    category: str = PhenotypeCategory.OTHER
    parent_hpo_id: str | None = None
    is_root_term: bool = False
    frequency_in_med13: str | None = None
    severity_score: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: int | None = None

    def __post_init__(self) -> None:
        self.category = PhenotypeCategory.validate(self.category)
        self.synonyms = self._normalize_synonyms(self.synonyms)
        if not self.name:
            msg = "Phenotype name cannot be empty"
            raise ValueError(msg)
        max_severity = 5
        if self.severity_score is not None and not (
            1 <= self.severity_score <= max_severity
        ):
            msg = "severity_score must be between 1 and 5"
            raise ValueError(msg)

    def add_synonym(self, synonym: str) -> None:
        cleaned = synonym.strip()
        if not cleaned:
            msg = "synonym cannot be empty"
            raise ValueError(msg)
        if cleaned not in self.synonyms:
            self.synonyms = (*self.synonyms, cleaned)
            self._touch()

    def update_definition(self, definition: str | None) -> None:
        self.definition = definition
        self._touch()

    def update_category(self, category: str) -> None:
        self.category = PhenotypeCategory.validate(category)
        self._touch()

    def mark_as_root(self, *, parent_hpo_id: str | None = None) -> None:
        self.is_root_term = True
        self.parent_hpo_id = parent_hpo_id
        self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now(UTC)

    @staticmethod
    def _normalize_synonyms(synonyms: tuple[str, ...]) -> tuple[str, ...]:
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
