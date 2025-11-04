"""
Phenotype repository for MED13 Resource Library.
Data access layer for clinical phenotype entities with HPO queries.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, or_

from .base import BaseRepository, NotFoundError
from src.models.database import (
    PhenotypeModel,
    PhenotypeCategory,
    EvidenceModel,
    VariantModel,
)


class PhenotypeRepository(BaseRepository[PhenotypeModel, int]):
    """
    Repository for Phenotype entities with specialized HPO-specific queries.

    Provides data access operations for clinical phenotypes including
    HPO term lookups, category filtering, and hierarchy queries.
    """

    @property
    def model_class(self) -> type[PhenotypeModel]:
        return PhenotypeModel

    def find_by_hpo_id(self, hpo_id: str) -> Optional[PhenotypeModel]:
        """
        Find a phenotype by its HPO ID.

        Args:
            hpo_id: HPO identifier (e.g., "HP:0001234")

        Returns:
            PhenotypeModel instance or None if not found
        """
        stmt = select(PhenotypeModel).where(PhenotypeModel.hpo_id == hpo_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def find_by_hpo_term(self, hpo_term: str) -> List[PhenotypeModel]:
        """
        Find phenotypes by HPO term (partial match).

        Args:
            hpo_term: HPO term to search for

        Returns:
            List of PhenotypeModel instances matching the term
        """
        search_pattern = f"%{hpo_term}%"
        stmt = select(PhenotypeModel).where(
            PhenotypeModel.hpo_term.ilike(search_pattern)
        )
        return list(self.session.execute(stmt).scalars())

    def find_by_category(
        self, category: PhenotypeCategory, limit: Optional[int] = None
    ) -> List[PhenotypeModel]:
        """
        Find phenotypes in a specific category.

        Args:
            category: Phenotype category
            limit: Maximum number of phenotypes to return

        Returns:
            List of PhenotypeModel instances in the category
        """
        stmt = select(PhenotypeModel).where(PhenotypeModel.category == category)
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def find_root_terms(self) -> List[PhenotypeModel]:
        """
        Find root HPO terms (terms with no parent).

        Returns:
            List of root PhenotypeModel instances
        """
        stmt = select(PhenotypeModel).where(PhenotypeModel.is_root_term)
        return list(self.session.execute(stmt).scalars())

    def find_children(self, parent_hpo_id: str) -> List[PhenotypeModel]:
        """
        Find child phenotypes of a parent HPO term.

        Args:
            parent_hpo_id: Parent HPO ID

        Returns:
            List of child PhenotypeModel instances
        """
        stmt = select(PhenotypeModel).where(
            PhenotypeModel.parent_hpo_id == parent_hpo_id
        )
        return list(self.session.execute(stmt).scalars())

    def find_with_evidence(self, phenotype_id: int) -> Optional[PhenotypeModel]:
        """
        Find a phenotype with its associated evidence loaded.

        Args:
            phenotype_id: Phenotype ID to retrieve

        Returns:
            PhenotypeModel with evidence relationship loaded, or None if not found
        """
        stmt = select(PhenotypeModel).where(PhenotypeModel.id == phenotype_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def search_phenotypes(self, query: str, limit: int = 20) -> List[PhenotypeModel]:
        """
        Search phenotypes by name, definition, or synonyms.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of matching PhenotypeModel instances
        """
        search_pattern = f"%{query}%"
        stmt = (
            select(PhenotypeModel)
            .where(
                or_(
                    PhenotypeModel.name.ilike(search_pattern),
                    PhenotypeModel.definition.ilike(search_pattern),
                    PhenotypeModel.synonyms.ilike(search_pattern),
                )
            )
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def get_phenotype_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about phenotypes in the database.

        Returns:
            Dictionary with phenotype statistics
        """
        total_phenotypes = self.count()
        root_terms = len(self.find_root_terms())

        return {
            "total_phenotypes": total_phenotypes,
            "root_terms": root_terms,
            "phenotypes_with_evidence": 0,  # Would need join query
        }

    def find_by_hpo_id_or_fail(self, hpo_id: str) -> PhenotypeModel:
        """
        Find a phenotype by HPO ID, raising NotFoundError if not found.

        Args:
            hpo_id: HPO identifier to search for

        Returns:
            PhenotypeModel instance

        Raises:
            NotFoundError: If phenotype is not found
        """
        phenotype = self.find_by_hpo_id(hpo_id)
        if phenotype is None:
            raise NotFoundError(f"Phenotype with HPO ID '{hpo_id}' not found")
        return phenotype

    def find_by_variant_associations(self, variant_id: int) -> List[PhenotypeModel]:
        """
        Find phenotypes linked to a variant via evidence associations.
        """
        stmt = (
            select(PhenotypeModel)
            .join(EvidenceModel, EvidenceModel.phenotype_id == PhenotypeModel.id)
            .where(EvidenceModel.variant_id == variant_id)
            .order_by(PhenotypeModel.name.asc())
        ).distinct()
        return list(self.session.execute(stmt).scalars())

    def find_by_gene_associations(self, gene_id: int) -> List[PhenotypeModel]:
        """
        Find phenotypes indirectly associated with a gene via variants.
        """
        stmt = (
            select(PhenotypeModel)
            .join(EvidenceModel, EvidenceModel.phenotype_id == PhenotypeModel.id)
            .join(VariantModel, VariantModel.id == EvidenceModel.variant_id)
            .where(VariantModel.gene_id == gene_id)
            .order_by(PhenotypeModel.name.asc())
        ).distinct()
        return list(self.session.execute(stmt).scalars())
