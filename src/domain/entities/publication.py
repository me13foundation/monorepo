from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, date
from typing import Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.entities.evidence import Evidence

from src.domain.value_objects.identifiers import PublicationIdentifier


class PublicationType:
    JOURNAL_ARTICLE = "journal_article"
    REVIEW_ARTICLE = "review_article"
    CASE_REPORT = "case_report"
    CONFERENCE_ABSTRACT = "conference_abstract"
    BOOK_CHAPTER = "book_chapter"
    THESIS = "thesis"
    PREPRINT = "preprint"

    _VALID_TYPES = {
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
            raise ValueError(f"Unsupported publication type '{value}'")
        return normalized


@dataclass
class Publication:
    identifier: PublicationIdentifier
    title: str
    authors: Tuple[str, ...]
    journal: str
    publication_year: int
    publication_type: str = PublicationType.JOURNAL_ARTICLE
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    publication_date: Optional[date] = None
    abstract: Optional[str] = None
    keywords: Tuple[str, ...] = field(default_factory=tuple)
    citation_count: int = 0
    impact_factor: Optional[float] = None
    reviewed: bool = False
    relevance_score: Optional[int] = None
    full_text_url: Optional[str] = None
    open_access: bool = False
    evidence: list["Evidence"] = field(default_factory=list, repr=False)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.title:
            raise ValueError("Publication title cannot be empty")
        if not self.authors:
            raise ValueError("Publication must have at least one author")
        if self.publication_year < 1800:
            raise ValueError("publication_year must be 1800 or later")
        if self.impact_factor is not None and self.impact_factor < 0:
            raise ValueError("impact_factor cannot be negative")
        if self.relevance_score is not None and not (1 <= self.relevance_score <= 5):
            raise ValueError("relevance_score must be between 1 and 5")
        self.publication_type = PublicationType.validate(self.publication_type)
        self.authors = self._normalize_people(self.authors)
        self.keywords = self._normalize_keywords(self.keywords)

    def add_author(self, author: str) -> None:
        cleaned = author.strip()
        if not cleaned:
            raise ValueError("author cannot be empty")
        if cleaned not in self.authors:
            self.authors = tuple((*self.authors, cleaned))
            self._touch()

    def add_keyword(self, keyword: str) -> None:
        cleaned = keyword.strip().lower()
        if not cleaned:
            raise ValueError("keyword cannot be empty")
        if cleaned not in self.keywords:
            self.keywords = tuple((*self.keywords, cleaned))
            self._touch()

    def add_evidence(self, evidence: "Evidence") -> None:
        self.evidence.append(evidence)
        self._touch()

    def record_citations(self, citation_count: int) -> None:
        if citation_count < 0:
            raise ValueError("citation_count cannot be negative")
        self.citation_count = citation_count
        self._touch()

    def update_relevance(self, relevance_score: Optional[int]) -> None:
        if relevance_score is not None and not (1 <= relevance_score <= 5):
            raise ValueError("relevance_score must be between 1 and 5")
        self.relevance_score = relevance_score
        self._touch()

    def mark_reviewed(self, reviewed: bool = True) -> None:
        self.reviewed = reviewed
        self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now(UTC)

    @staticmethod
    def _normalize_people(names: Tuple[str, ...]) -> Tuple[str, ...]:
        return tuple(name.strip() for name in names if name.strip())

    @staticmethod
    def _normalize_keywords(keywords: Tuple[str, ...]) -> Tuple[str, ...]:
        return tuple(
            sorted({keyword.strip().lower() for keyword in keywords if keyword.strip()})
        )


__all__ = ["Publication", "PublicationType"]
