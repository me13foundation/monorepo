"""
Phenotype repository interface - domain contract for phenotype data access.

Defines the operations available for phenotype entities without specifying
the underlying implementation.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from .base import Repository
from ..entities.phenotype import Phenotype
from ...type_definitions.common import PhenotypeUpdate


class PhenotypeRepository(Repository[Phenotype, int]):
    """
    Domain repository interface for Phenotype entities.

    Defines all operations available for phenotype data access, maintaining
    domain purity by not exposing infrastructure details.
    """

    @abstractmethod
    def find_by_hpo_id(self, hpo_id: str) -> Optional[Phenotype]:
        """Find a phenotype by its HPO ID."""
        pass

    @abstractmethod
    def find_by_name(self, name: str, fuzzy: bool = False) -> List[Phenotype]:
        """Find phenotypes by name (exact or fuzzy match)."""
        pass

    @abstractmethod
    def find_by_gene_associations(self, gene_id: int) -> List[Phenotype]:
        """Find phenotypes associated with a gene."""
        pass

    @abstractmethod
    def find_by_variant_associations(self, variant_id: int) -> List[Phenotype]:
        """Find phenotypes associated with a variant."""
        pass

    @abstractmethod
    def find_by_category(self, category: str) -> List[Phenotype]:
        """Find phenotypes by category."""
        pass

    @abstractmethod
    def search_phenotypes(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Phenotype]:
        """Search phenotypes with optional filters."""
        pass

    @abstractmethod
    def paginate_phenotypes(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Phenotype], int]:
        """Retrieve paginated phenotypes with optional filters."""
        pass

    @abstractmethod
    def get_phenotype_statistics(self) -> dict[str, int | float | bool | str | None]:
        """Get statistics about phenotypes in the repository."""
        pass

    @abstractmethod
    def find_by_ontology_term(self, term_id: str) -> Optional[Phenotype]:
        """Find a phenotype by ontology term ID."""
        pass

    @abstractmethod
    def update_phenotype(
        self, phenotype_id: int, updates: PhenotypeUpdate
    ) -> Phenotype:
        """Update a phenotype with type-safe update parameters."""
        pass


__all__ = ["PhenotypeRepository"]
