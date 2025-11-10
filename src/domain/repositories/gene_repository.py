"""
Gene repository interface - domain contract for gene data access.

Defines the operations available for gene entities without specifying
the underlying implementation.
"""

from abc import abstractmethod

from src.domain.entities.gene import Gene
from src.domain.repositories.base import Repository
from src.domain.value_objects.identifiers import GeneIdentifier
from src.type_definitions.common import GeneUpdate


class GeneRepository(Repository[Gene, int, GeneUpdate]):
    """
    Domain repository interface for Gene entities.

    Defines all operations available for gene data access, maintaining
    domain purity by not exposing infrastructure details.
    """

    @abstractmethod
    def find_by_symbol(self, symbol: str) -> Gene | None:
        """Find a gene by its symbol (case-insensitive)."""

    @abstractmethod
    def find_by_gene_id(self, gene_id: str) -> Gene | None:
        """Find a gene by its gene_id."""

    @abstractmethod
    def find_by_external_id(self, external_id: str) -> Gene | None:
        """Find a gene by any external identifier (Ensembl, NCBI, UniProt)."""

    @abstractmethod
    def find_by_identifier(self, identifier: GeneIdentifier) -> Gene | None:
        """Find a gene by its identifier (supports multiple ID types)."""

    @abstractmethod
    def search_by_name_or_symbol(self, query: str, limit: int = 10) -> list[Gene]:
        """Search genes by name or symbol containing the query string."""

    @abstractmethod
    def paginate_genes(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        search: str | None = None,
    ) -> tuple[list[Gene], int]:
        """Retrieve paginated genes with optional search and sorting."""

    @abstractmethod
    def find_with_variants(self, gene_id: int) -> Gene | None:
        """Find a gene with its associated variants loaded."""

    @abstractmethod
    def find_by_symbol_or_fail(self, symbol: str) -> Gene:
        """Find a gene by symbol, raising NotFoundError if not found."""

    @abstractmethod
    def find_by_gene_id_or_fail(self, gene_id: str) -> Gene:
        """Find a gene by gene_id, raising NotFoundError if not found."""

    @abstractmethod
    def get_gene_statistics(self) -> dict[str, int | float | bool | str | None]:
        """Get statistics about genes in the repository."""

    @abstractmethod
    def update_gene(self, gene_id: int, updates: GeneUpdate) -> Gene:
        """Update a gene with type-safe update parameters."""


__all__ = ["GeneRepository"]
