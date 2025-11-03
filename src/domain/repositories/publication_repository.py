"""
Publication repository interface - domain contract for publication data access.

Defines the operations available for publication entities without specifying
the underlying implementation.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from .base import Repository
from ..entities.publication import Publication
from ...types.common import PublicationUpdate


class PublicationRepository(Repository[Publication, int]):
    """
    Domain repository interface for Publication entities.

    Defines all operations available for publication data access, maintaining
    domain purity by not exposing infrastructure details.
    """

    @abstractmethod
    def find_by_pmid(self, pmid: str) -> Optional[Publication]:
        """Find a publication by PubMed ID."""
        pass

    @abstractmethod
    def find_by_doi(self, doi: str) -> Optional[Publication]:
        """Find a publication by DOI."""
        pass

    @abstractmethod
    def find_by_title(self, title: str, fuzzy: bool = False) -> List[Publication]:
        """Find publications by title (exact or fuzzy match)."""
        pass

    @abstractmethod
    def find_by_author(self, author_name: str) -> List[Publication]:
        """Find publications by author name."""
        pass

    @abstractmethod
    def find_by_year_range(self, start_year: int, end_year: int) -> List[Publication]:
        """Find publications within a year range."""
        pass

    @abstractmethod
    def find_by_gene_associations(self, gene_id: int) -> List[Publication]:
        """Find publications associated with a gene."""
        pass

    @abstractmethod
    def find_by_variant_associations(self, variant_id: int) -> List[Publication]:
        """Find publications associated with a variant."""
        pass

    @abstractmethod
    def search_publications(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Publication]:
        """Search publications with optional filters."""
        pass

    @abstractmethod
    def paginate_publications(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Publication], int]:
        """Retrieve paginated publications with optional filters."""
        pass

    @abstractmethod
    def get_publication_statistics(self) -> dict[str, int | float | bool | str | None]:
        """Get statistics about publications in the repository."""
        pass

    @abstractmethod
    def find_recent_publications(self, days: int = 30) -> List[Publication]:
        """Find publications from the last N days."""
        pass

    @abstractmethod
    def update_publication(
        self, publication_id: int, updates: PublicationUpdate
    ) -> Publication:
        """Update a publication with type-safe update parameters."""
        pass


__all__ = ["PublicationRepository"]
