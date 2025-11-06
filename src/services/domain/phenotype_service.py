"""
Phenotype service for MED13 Resource Library.
Business logic for clinical phenotype operations.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.domain.entities.phenotype import Phenotype, PhenotypeCategory
from src.infrastructure.repositories import SqlAlchemyPhenotypeRepository
from src.services.domain.base_service import BaseService


@dataclass
class PhenotypeHierarchy:
    phenotype: Phenotype
    children: list[Phenotype]
    parent_hpo_id: str | None


class PhenotypeService(BaseService[SqlAlchemyPhenotypeRepository]):
    """
    Service for phenotype business logic and operations.

    Provides high-level operations for phenotype management including
    HPO hierarchy navigation and clinical categorization.
    """

    def __init__(
        self,
        session: Session | None = None,
        phenotype_repository: SqlAlchemyPhenotypeRepository | None = None,
    ):
        super().__init__(session)
        self.phenotype_repo = (
            phenotype_repository
            if phenotype_repository
            else SqlAlchemyPhenotypeRepository(session)
        )

    @property
    def repository(self) -> SqlAlchemyPhenotypeRepository:
        return self.phenotype_repo

    def find_phenotypes_by_category(
        self,
        category: str,
        limit: int | None = None,
    ) -> list[Phenotype]:
        """
        Find phenotypes in a specific clinical category.

        Args:
            category: Phenotype category
            limit: Maximum number of phenotypes to return

        Returns:
            List of Phenotype entities in the category
        """
        normalized_category = PhenotypeCategory.validate(category)
        return self.phenotype_repo.find_by_category(normalized_category, limit)

    def get_phenotype_hierarchy(self, hpo_id: str) -> PhenotypeHierarchy | None:
        """
        Get the phenotype hierarchy for an HPO term.

        Args:
            hpo_id: HPO ID to get hierarchy for

        Returns:
            Dictionary with parent and child relationships
        """
        phenotype = self.phenotype_repo.find_by_hpo_id(hpo_id)
        if phenotype is None:
            return None

        children = self.phenotype_repo.find_children(hpo_id)

        return PhenotypeHierarchy(
            phenotype=phenotype,
            children=children,
            parent_hpo_id=phenotype.parent_hpo_id,
        )

    def search_phenotypes(self, query: str, limit: int = 20) -> list[Phenotype]:
        """
        Search phenotypes by name, definition, or synonyms.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching Phenotype entities
        """
        return self.phenotype_repo.search_phenotypes(query, limit)
