from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from src.domain.entities.evidence import Evidence

if TYPE_CHECKING:
    from src.domain.value_objects.identifiers import PublicationIdentifier


class PublicationType:
    JOURNAL_ARTICLE = "journal_article"
    REVIEW_ARTICLE = "review_article"
    CASE_REPORT = "case_report"
    CONFERENCE_ABSTRACT = "conference_abstract"
    BOOK_CHAPTER = "book_chapter"
    THESIS = "thesis"
    PREPRINT = "preprint"

    _VALID_TYPES: ClassVar[set[str]] = {
        JOURNAL_ARTICLE,
        REVIEW_ARTICLE,
        CASE_REPORT,
        CONFERENCE_ABSTRACT,
        BOOK_CHAPTER,
        THESIS,
        PREPRINT,
    }

    @classmethod
    def validate(cls, value: str) -> str:
        normalized = value or cls.JOURNAL_ARTICLE
        if normalized not in cls._VALID_TYPES:
            msg = f"Unsupported publication type '{value}'"
            raise ValueError(msg)
        return normalized


@dataclass
class Publication:
    identifier: PublicationIdentifier
    title: str
    authors: tuple[str, ...]
    journal: str
    publication_year: int
    publication_type: str = PublicationType.JOURNAL_ARTICLE
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    publication_date: date | None = None
    abstract: str | None = None
    keywords: tuple[str, ...] = field(default_factory=tuple)
    citation_count: int = 0
    impact_factor: float | None = None
    reviewed: bool = False
    relevance_score: int | None = None
    full_text_url: str | None = None
    open_access: bool = False
    evidence: list[Evidence] = field(default_factory=list, repr=False)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: int | None = None

    def __post_init__(self) -> None:
        if not self.title:
            msg = "Publication title cannot be empty"
            raise ValueError(msg)
        if not self.authors:
            msg = "Publication must have at least one author"
            raise ValueError(msg)
        min_publication_year = 1800
        if self.publication_year < min_publication_year:
            msg = "publication_year must be 1800 or later"
            raise ValueError(msg)
        if self.impact_factor is not None and self.impact_factor < 0:
            msg = "impact_factor cannot be negative"
            raise ValueError(msg)
        max_relevance = 5
        if self.relevance_score is not None and not (
            1 <= self.relevance_score <= max_relevance
        ):
            msg = "relevance_score must be between 1 and 5"
            raise ValueError(msg)
        self.publication_type = PublicationType.validate(self.publication_type)
        self.authors = self._normalize_people(self.authors)
        self.keywords = self._normalize_keywords(self.keywords)

    def add_author(self, author: str) -> None:
        cleaned = author.strip()
        if not cleaned:
            msg = "author cannot be empty"
            raise ValueError(msg)
        if cleaned not in self.authors:
            self.authors = (*self.authors, cleaned)
            self._touch()

    def add_keyword(self, keyword: str) -> None:
        cleaned = keyword.strip().lower()
        if not cleaned:
            msg = "keyword cannot be empty"
            raise ValueError(msg)
        if cleaned not in self.keywords:
            self.keywords = (*self.keywords, cleaned)
            self._touch()

    def add_evidence(self, evidence: Evidence) -> None:
        self.evidence.append(evidence)
        self._touch()

    def record_citations(self, citation_count: int) -> None:
        if citation_count < 0:
            msg = "citation_count cannot be negative"
            raise ValueError(msg)
        self.citation_count = citation_count
        self._touch()

    def update_relevance(self, relevance_score: int | None) -> None:
        max_relevance = 5
        if relevance_score is not None and not (1 <= relevance_score <= max_relevance):
            msg = "relevance_score must be between 1 and 5"
            raise ValueError(msg)
        self.relevance_score = relevance_score
        self._touch()

    def mark_reviewed(self, *, reviewed: bool = True) -> None:
        self.reviewed = reviewed
        self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now(UTC)

    @staticmethod
    def _normalize_people(names: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(name.strip() for name in names if name.strip())

    @staticmethod
    def _normalize_keywords(keywords: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            sorted(
                {keyword.strip().lower() for keyword in keywords if keyword.strip()},
            ),
        )


__all__ = ["Publication", "PublicationType"]
