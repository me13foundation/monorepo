"""
Evidence repository interface - domain contract for evidence data access.

Defines the operations available for evidence entities without specifying
the underlying implementation.
"""

from abc import abstractmethod

from src.domain.entities.evidence import Evidence
from src.domain.repositories.base import Repository
from src.type_definitions.common import EvidenceUpdate, QueryFilters


class EvidenceRepository(Repository[Evidence, int, EvidenceUpdate]):
    """
    Domain repository interface for Evidence entities.

    Defines all operations available for evidence data access, maintaining
    domain purity by not exposing infrastructure details.
    """

    @abstractmethod
    def find_by_variant(self, variant_id: int) -> list[Evidence]:
        """Find evidence records for a variant."""

    @abstractmethod
    def find_by_phenotype(self, phenotype_id: int) -> list[Evidence]:
        """Find evidence records for a phenotype."""

    @abstractmethod
    def find_by_gene(self, gene_id: int) -> list[Evidence]:
        """Find evidence records for a gene."""

    @abstractmethod
    def find_by_publication(self, publication_id: int) -> list[Evidence]:
        """Find evidence records for a publication."""

    @abstractmethod
    def find_by_evidence_level(self, level: str) -> list[Evidence]:
        """Find evidence records by evidence level."""

    @abstractmethod
    def find_by_confidence_score(
        self,
        min_score: float,
        max_score: float,
    ) -> list[Evidence]:
        """Find evidence records within confidence score range."""

    @abstractmethod
    def find_by_source(self, source: str) -> list[Evidence]:
        """Find evidence records from a specific source."""

    @abstractmethod
    def find_high_confidence_evidence(
        self,
        limit: int | None = None,
    ) -> list[Evidence]:
        """Find evidence with high confidence scores."""

    @abstractmethod
    def find_relationship_evidence(
        self,
        variant_id: int,
        phenotype_id: int,
        min_confidence: float = 0.0,
    ) -> list[Evidence]:
        """Find evidence linking a variant and phenotype with minimum confidence."""

    @abstractmethod
    def search_evidence(
        self,
        query: str,
        limit: int = 10,
        filters: QueryFilters | None = None,
    ) -> list[Evidence]:
        """Search evidence with optional filters."""

    @abstractmethod
    def paginate_evidence(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        filters: QueryFilters | None = None,
    ) -> tuple[list[Evidence], int]:
        """Retrieve paginated evidence with optional filters."""

    @abstractmethod
    def get_evidence_statistics(self) -> dict[str, int | float | bool | str | None]:
        """Get statistics about evidence in the repository."""

    @abstractmethod
    def find_conflicting_evidence(self, variant_id: int) -> list[Evidence]:
        """Find conflicting evidence records for a variant."""

    @abstractmethod
    def update_evidence(self, evidence_id: int, updates: EvidenceUpdate) -> Evidence:
        """Update evidence with type-safe update parameters."""


__all__ = ["EvidenceRepository"]
