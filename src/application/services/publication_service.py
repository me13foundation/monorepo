"""
Publication application service orchestration layer.

Coordinates domain services and repositories to implement publication management
use cases while preserving strong typing.
"""

from typing import Any, Dict, List, Optional, Tuple

from src.domain.entities.publication import Publication, PublicationType
from src.domain.repositories.publication_repository import PublicationRepository
from src.domain.value_objects.identifiers import PublicationIdentifier


class PublicationApplicationService:
    """
    Application service for publication management use cases.

    Orchestrates domain services and repositories to implement
    publication-related business operations with proper dependency injection.
    """

    def __init__(self, publication_repository: PublicationRepository):
        """
        Initialize the publication application service.

        Args:
            publication_repository: Domain repository for publications
        """
        self._publication_repository = publication_repository

    def create_publication(
        self,
        title: str,
        authors: List[str],
        publication_year: int,
        journal: str,
        *,
        doi: Optional[str] = None,
        pmid: Optional[str] = None,
        pmc_id: Optional[str] = None,
        abstract: Optional[str] = None,
        publication_type: str = PublicationType.JOURNAL_ARTICLE,
        keywords: Optional[List[str]] = None,
        citation_count: int = 0,
        impact_factor: Optional[float] = None,
        relevance_score: Optional[int] = None,
        open_access: bool = False,
    ) -> Publication:
        """
        Create a new publication.

        Args:
            title: Publication title
            authors: List of authors
            publication_year: Year of publication
            journal: Journal name
            doi: DOI identifier
            pmid: PubMed ID
            abstract: Publication abstract
            publication_type: Type of publication

        Returns:
            Created Publication entity
        """
        identifier = PublicationIdentifier(
            pubmed_id=pmid,
            pmc_id=pmc_id,
            doi=doi,
        )

        publication_entity = Publication(
            identifier=identifier,
            title=title,
            authors=tuple(authors),
            journal=journal,
            publication_year=publication_year,
            publication_type=PublicationType.validate(publication_type),
            abstract=abstract,
            keywords=tuple(keywords) if keywords else tuple(),
            citation_count=citation_count,
            impact_factor=impact_factor,
            relevance_score=relevance_score,
            open_access=open_access,
        )

        return self._publication_repository.create(publication_entity)

    def get_publication_by_pmid(self, pmid: str) -> Optional[Publication]:
        """Find a publication by PubMed ID."""
        return self._publication_repository.find_by_pmid(pmid)

    def get_publication_by_doi(self, doi: str) -> Optional[Publication]:
        """Find a publication by DOI."""
        return self._publication_repository.find_by_doi(doi)

    def search_publications_by_title(
        self, title: str, fuzzy: bool = False
    ) -> List[Publication]:
        """Find publications by title."""
        return self._publication_repository.find_by_title(title, fuzzy)

    def search_publications_by_author(self, author_name: str) -> List[Publication]:
        """Find publications by author name."""
        return self._publication_repository.find_by_author(author_name)

    def get_publications_by_year_range(
        self, start_year: int, end_year: int
    ) -> List[Publication]:
        """Find publications within a year range."""
        return self._publication_repository.find_by_year_range(start_year, end_year)

    def search_publications(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Publication]:
        """Search publications with optional filters."""
        return self._publication_repository.search_publications(query, limit, filters)

    def list_publications(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Publication], int]:
        """Retrieve paginated publications with optional filters."""
        return self._publication_repository.paginate_publications(
            page, per_page, sort_by, sort_order, filters
        )

    def update_publication(
        self, publication_id: int, updates: Dict[str, Any]
    ) -> Publication:
        """Update publication fields."""
        return self._publication_repository.update(publication_id, updates)

    def get_publication_statistics(self) -> Dict[str, int | float | bool | str | None]:
        """Get statistics about publications in the repository."""
        return self._publication_repository.get_publication_statistics()

    def find_recent_publications(self, days: int = 30) -> List[Publication]:
        """Find publications from the last N days."""
        return self._publication_repository.find_recent_publications(days)

    def validate_publication_exists(self, publication_id: int) -> bool:
        """
        Validate that a publication exists.

        Args:
            publication_id: Publication ID to validate

        Returns:
            True if publication exists, False otherwise
        """
        return self._publication_repository.exists(publication_id)


__all__ = ["PublicationApplicationService"]
