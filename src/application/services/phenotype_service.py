"""Application-level orchestration for phenotype use cases."""

from typing import Any, Dict, List, Optional, Tuple

from src.domain.entities.phenotype import Phenotype, PhenotypeCategory
from src.domain.repositories.phenotype_repository import PhenotypeRepository
from src.domain.value_objects.identifiers import PhenotypeIdentifier


class PhenotypeApplicationService:
    """
    Application service for phenotype management use cases.

    Orchestrates domain services and repositories to implement
    phenotype-related business operations with proper dependency injection.
    """

    def __init__(self, phenotype_repository: PhenotypeRepository):
        """
        Initialize the phenotype application service.

        Args:
            phenotype_repository: Domain repository for phenotypes
        """
        self._phenotype_repository = phenotype_repository

    def create_phenotype(
        self,
        hpo_id: str,
        name: str,
        definition: Optional[str] = None,
        category: str = PhenotypeCategory.OTHER,
        synonyms: Optional[List[str]] = None,
    ) -> Phenotype:
        """
        Create a new phenotype.

        Args:
            hpo_id: HPO identifier
            name: Phenotype name
            definition: Phenotype definition
            category: Phenotype category
            synonyms: Alternative names

        Returns:
            Created Phenotype entity
        """
        identifiers = PhenotypeIdentifier(hpo_id=hpo_id, hpo_term=name)
        phenotype_entity = Phenotype(
            identifier=identifiers,
            name=name,
            definition=definition,
            category=PhenotypeCategory.validate(category),
            synonyms=tuple(synonyms or []),
        )

        return self._phenotype_repository.create(phenotype_entity)

    def get_phenotype_by_hpo_id(self, hpo_id: str) -> Optional[Phenotype]:
        """Find a phenotype by its HPO ID."""
        return self._phenotype_repository.find_by_hpo_id(hpo_id)

    def search_phenotypes_by_name(
        self, name: str, fuzzy: bool = False
    ) -> List[Phenotype]:
        """Find phenotypes by name."""
        return self._phenotype_repository.find_by_name(name, fuzzy)

    def get_phenotypes_by_category(self, category: str) -> List[Phenotype]:
        """Find phenotypes by category."""
        return self._phenotype_repository.find_by_category(category)

    def search_phenotypes(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Phenotype]:
        """Search phenotypes with optional filters."""
        return self._phenotype_repository.search_phenotypes(query, limit, filters)

    def list_phenotypes(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Phenotype], int]:
        """Retrieve paginated phenotypes with optional filters."""
        return self._phenotype_repository.paginate_phenotypes(
            page, per_page, sort_by, sort_order, filters
        )

    def update_phenotype(self, phenotype_id: int, updates: Dict[str, Any]) -> Phenotype:
        """Update phenotype fields."""
        return self._phenotype_repository.update(phenotype_id, updates)

    def get_phenotype_statistics(self) -> Dict[str, int | float | bool | str | None]:
        """Get statistics about phenotypes in the repository."""
        return self._phenotype_repository.get_phenotype_statistics()

    def validate_phenotype_exists(self, phenotype_id: int) -> bool:
        """
        Validate that a phenotype exists.

        Args:
            phenotype_id: Phenotype ID to validate

        Returns:
            True if phenotype exists, False otherwise
        """
        return self._phenotype_repository.exists(phenotype_id)


__all__ = ["PhenotypeApplicationService"]
