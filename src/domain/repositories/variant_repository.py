"""
Variant repository interface - domain contract for variant data access.

Defines the operations available for variant entities without specifying
the underlying implementation.
"""

from abc import abstractmethod

from src.domain.entities.variant import Variant, VariantSummary
from src.domain.repositories.base import Repository
from src.type_definitions.common import JSONObject, QueryFilters, VariantUpdate


class VariantRepository(Repository[Variant, int, VariantUpdate]):
    """
    Domain repository interface for Variant entities.

    Defines all operations available for variant data access, maintaining
    domain purity by not exposing infrastructure details.
    """

    @abstractmethod
    def find_by_variant_id(self, variant_id: str) -> Variant | None:
        """Find a variant by its variant_id."""

    @abstractmethod
    def find_by_clinvar_id(self, clinvar_id: str) -> Variant | None:
        """Find a variant by its ClinVar ID."""

    @abstractmethod
    def find_by_gene(self, gene_id: int, limit: int | None = None) -> list[Variant]:
        """Find variants associated with a gene."""

    @abstractmethod
    def find_by_chromosome_position(
        self,
        chromosome: str,
        position: int,
    ) -> list[Variant]:
        """Find variants at a specific genomic position."""

    @abstractmethod
    def find_by_clinical_significance(
        self,
        significance: str,
        limit: int | None = None,
    ) -> list[Variant]:
        """Find variants by clinical significance."""

    @abstractmethod
    def search_variants(
        self,
        query: str,
        limit: int = 10,
        filters: QueryFilters | None = None,
    ) -> list[Variant]:
        """Search variants with optional filters."""

    @abstractmethod
    def paginate_variants(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        filters: QueryFilters | None = None,
    ) -> tuple[list[Variant], int]:
        """Retrieve paginated variants with optional filters."""

    @abstractmethod
    def get_variant_summaries_by_gene(self, gene_id: int) -> list[VariantSummary]:
        """Get variant summaries for a gene."""

    @abstractmethod
    def get_variant_statistics(self) -> JSONObject:
        """Get statistics about variants in the repository."""

    @abstractmethod
    def find_by_gene_symbol(self, gene_symbol: str) -> list[Variant]:
        """Find variants associated with a gene symbol."""

    @abstractmethod
    def find_pathogenic_variants(
        self,
        limit: int | None = None,
    ) -> list[Variant]:
        """Find variants classified as pathogenic or likely pathogenic."""

    @abstractmethod
    def update_variant(self, variant_id: int, updates: VariantUpdate) -> Variant:
        """Update a variant with type-safe update parameters."""


__all__ = ["VariantRepository"]
