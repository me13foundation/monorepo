from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.domain.value_objects.identifiers import PhenotypeIdentifier  # noqa: TC001


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


SEVERITY_SCORE_MIN = 1
SEVERITY_SCORE_MAX = 5


class Phenotype(BaseModel):
    identifier: PhenotypeIdentifier
    name: str
    definition: str | None = None
    synonyms: tuple[str, ...] = Field(default_factory=tuple)
    category: str = Field(default=PhenotypeCategory.OTHER)
    parent_hpo_id: str | None = None
    is_root_term: bool = False
    frequency_in_med13: str | None = None
    severity_score: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    id: int | None = None

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    @field_validator("category")
    @classmethod
    def _validate_category(cls, value: str) -> str:
        return PhenotypeCategory.validate(value)

    @field_validator("synonyms")
    @classmethod
    def _normalize_synonyms(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        seen: set[str] = set()
        normalized: list[str] = []
        for synonym in value:
            cleaned = synonym.strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key not in seen:
                seen.add(key)
                normalized.append(cleaned)
        return tuple(normalized)

    @model_validator(mode="after")
    def _validate(self) -> Phenotype:
        if not self.name:
            msg = "Phenotype name cannot be empty"
            raise ValueError(msg)
        if self.severity_score is not None and not (
            SEVERITY_SCORE_MIN <= self.severity_score <= SEVERITY_SCORE_MAX
        ):
            msg = (
                f"severity_score must be between {SEVERITY_SCORE_MIN} "
                f"and {SEVERITY_SCORE_MAX}"
            )
            raise ValueError(msg)
        return self

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


__all__ = ["Phenotype", "PhenotypeCategory"]
