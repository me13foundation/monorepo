"""
Variant repository interface - domain contract for variant data access.

Defines the operations available for variant entities without specifying
the underlying implementation.
"""

from abc import abstractmethod
from typing import Dict, List, Optional, Tuple, Any

from .base import Repository
from ..entities.variant import Variant, VariantSummary


class VariantRepository(Repository[Variant, int]):
    """
    Domain repository interface for Variant entities.

    Defines all operations available for variant data access, maintaining
    domain purity by not exposing infrastructure details.
    """

    @abstractmethod
    def find_by_variant_id(self, variant_id: str) -> Optional[Variant]:
        """Find a variant by its variant_id."""
        pass

    @abstractmethod
    def find_by_clinvar_id(self, clinvar_id: str) -> Optional[Variant]:
        """Find a variant by its ClinVar ID."""
        pass

    @abstractmethod
    def find_by_gene(self, gene_id: int, limit: Optional[int] = None) -> List[Variant]:
        """Find variants associated with a gene."""
        pass

    @abstractmethod
    def find_by_chromosome_position(
        self, chromosome: str, position: int
    ) -> List[Variant]:
        """Find variants at a specific genomic position."""
        pass

    @abstractmethod
    def find_by_clinical_significance(
        self, significance: str, limit: Optional[int] = None
    ) -> List[Variant]:
        """Find variants by clinical significance."""
        pass

    @abstractmethod
    def search_variants(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Variant]:
        """Search variants with optional filters."""
        pass

    @abstractmethod
    def paginate_variants(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Variant], int]:
        """Retrieve paginated variants with optional filters."""
        pass

    @abstractmethod
    def get_variant_summaries_by_gene(self, gene_id: int) -> List[VariantSummary]:
        """Get variant summaries for a gene."""
        pass

    @abstractmethod
    def get_variant_statistics(self) -> dict[str, int | float | bool | str | None]:
        """Get statistics about variants in the repository."""
        pass

    @abstractmethod
    def find_by_gene_symbol(self, gene_symbol: str) -> List[Variant]:
        """Find variants associated with a gene symbol."""
        pass


__all__ = ["VariantRepository"]
