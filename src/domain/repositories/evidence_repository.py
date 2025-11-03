"""
Evidence repository interface - domain contract for evidence data access.

Defines the operations available for evidence entities without specifying
the underlying implementation.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from .base import Repository
from ..entities.evidence import Evidence
from ...type_definitions.common import EvidenceUpdate


class EvidenceRepository(Repository[Evidence, int]):
    """
    Domain repository interface for Evidence entities.

    Defines all operations available for evidence data access, maintaining
    domain purity by not exposing infrastructure details.
    """

    @abstractmethod
    def find_by_variant(self, variant_id: int) -> List[Evidence]:
        """Find evidence records for a variant."""
        pass

    @abstractmethod
    def find_by_phenotype(self, phenotype_id: int) -> List[Evidence]:
        """Find evidence records for a phenotype."""
        pass

    @abstractmethod
    def find_by_gene(self, gene_id: int) -> List[Evidence]:
        """Find evidence records for a gene."""
        pass

    @abstractmethod
    def find_by_publication(self, publication_id: int) -> List[Evidence]:
        """Find evidence records for a publication."""
        pass

    @abstractmethod
    def find_by_evidence_level(self, level: str) -> List[Evidence]:
        """Find evidence records by evidence level."""
        pass

    @abstractmethod
    def find_by_confidence_score(
        self, min_score: float, max_score: float
    ) -> List[Evidence]:
        """Find evidence records within confidence score range."""
        pass

    @abstractmethod
    def find_by_source(self, source: str) -> List[Evidence]:
        """Find evidence records from a specific source."""
        pass

    @abstractmethod
    def search_evidence(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Evidence]:
        """Search evidence with optional filters."""
        pass

    @abstractmethod
    def paginate_evidence(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Evidence], int]:
        """Retrieve paginated evidence with optional filters."""
        pass

    @abstractmethod
    def get_evidence_statistics(self) -> dict[str, int | float | bool | str | None]:
        """Get statistics about evidence in the repository."""
        pass

    @abstractmethod
    def find_conflicting_evidence(self, variant_id: int) -> List[Evidence]:
        """Find conflicting evidence records for a variant."""
        pass

    @abstractmethod
    def update_evidence(self, evidence_id: int, updates: EvidenceUpdate) -> Evidence:
        """Update evidence with type-safe update parameters."""
        pass


__all__ = ["EvidenceRepository"]
