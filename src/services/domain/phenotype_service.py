"""
Phenotype service for MED13 Resource Library.
Business logic for clinical phenotype operations.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from src.repositories import PhenotypeRepository, EvidenceRepository
from src.models.database import PhenotypeModel, PhenotypeCategory
from src.services.domain.base_service import BaseService


class PhenotypeService(BaseService[PhenotypeModel]):
    """
    Service for phenotype business logic and operations.

    Provides high-level operations for phenotype management including
    HPO hierarchy navigation and clinical categorization.
    """

    def __init__(self, session: Optional[Session] = None):
        super().__init__(session)
        self.phenotype_repo = PhenotypeRepository(session)
        self.evidence_repo = EvidenceRepository(session)

    @property
    def repository(self) -> PhenotypeRepository:
        return self.phenotype_repo

    def find_phenotypes_by_category(
        self, category: PhenotypeCategory, limit: Optional[int] = None
    ) -> List[PhenotypeModel]:
        """
        Find phenotypes in a specific clinical category.

        Args:
            category: Phenotype category
            limit: Maximum number of phenotypes to return

        Returns:
            List of PhenotypeModel instances in the category
        """
        return self.phenotype_repo.find_by_category(category, limit)

    def get_phenotype_hierarchy(self, hpo_id: str) -> Dict[str, Any]:
        """
        Get the phenotype hierarchy for an HPO term.

        Args:
            hpo_id: HPO ID to get hierarchy for

        Returns:
            Dictionary with parent and child relationships
        """
        phenotype = self.phenotype_repo.find_by_hpo_id(hpo_id)
        if not phenotype:
            return {}

        children = self.phenotype_repo.find_children(hpo_id)

        return {
            "phenotype": phenotype,
            "children": children,
            "parent_hpo_id": phenotype.parent_hpo_id,
        }

    def search_phenotypes(self, query: str, limit: int = 20) -> List[PhenotypeModel]:
        """
        Search phenotypes by name, definition, or synonyms.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching PhenotypeModel instances
        """
        return self.phenotype_repo.search_phenotypes(query, limit)
