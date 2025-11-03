"""
Gene repository interface - domain contract for gene data access.

Defines the operations available for gene entities without specifying
the underlying implementation.
"""

from abc import abstractmethod
from typing import List, Optional, Tuple

from .base import Repository
from ..entities.gene import Gene
from ..value_objects.identifiers import GeneIdentifier


class GeneRepository(Repository[Gene, int]):
    """
    Domain repository interface for Gene entities.

    Defines all operations available for gene data access, maintaining
    domain purity by not exposing infrastructure details.
    """

    @abstractmethod
    def find_by_symbol(self, symbol: str) -> Optional[Gene]:
        """Find a gene by its symbol (case-insensitive)."""
        pass

    @abstractmethod
    def find_by_gene_id(self, gene_id: str) -> Optional[Gene]:
        """Find a gene by its gene_id."""
        pass

    @abstractmethod
    def find_by_external_id(self, external_id: str) -> Optional[Gene]:
        """Find a gene by any external identifier (Ensembl, NCBI, UniProt)."""
        pass

    @abstractmethod
    def find_by_identifier(self, identifier: GeneIdentifier) -> Optional[Gene]:
        """Find a gene by its identifier (supports multiple ID types)."""
        pass

    @abstractmethod
    def search_by_name_or_symbol(self, query: str, limit: int = 10) -> List[Gene]:
        """Search genes by name or symbol containing the query string."""
        pass

    @abstractmethod
    def paginate_genes(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        search: Optional[str] = None,
    ) -> Tuple[List[Gene], int]:
        """Retrieve paginated genes with optional search and sorting."""
        pass

    @abstractmethod
    def find_with_variants(self, gene_id: int) -> Optional[Gene]:
        """Find a gene with its associated variants loaded."""
        pass

    @abstractmethod
    def find_by_symbol_or_fail(self, symbol: str) -> Gene:
        """Find a gene by symbol, raising NotFoundError if not found."""
        pass

    @abstractmethod
    def find_by_gene_id_or_fail(self, gene_id: str) -> Gene:
        """Find a gene by gene_id, raising NotFoundError if not found."""
        pass

    @abstractmethod
    def get_gene_statistics(self) -> dict[str, int | float | bool | str | None]:
        """Get statistics about genes in the repository."""
        pass


__all__ = ["GeneRepository"]
