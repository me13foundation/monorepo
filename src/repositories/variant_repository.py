"""
Variant repository for MED13 Resource Library.
Data access layer for genetic variant entities with specialized queries.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_

from .base import BaseRepository, NotFoundError
from src.models.database import VariantModel, ClinicalSignificance


class VariantRepository(BaseRepository[VariantModel, int]):
    """
    Repository for Variant entities with specialized variant-specific queries.

    Provides data access operations for genetic variants including
    ClinVar lookups, genomic coordinate searches, and clinical significance filtering.
    """

    @property
    def model_class(self) -> type[VariantModel]:
        return VariantModel

    def find_by_variant_id(self, variant_id: str) -> Optional[VariantModel]:
        """
        Find a variant by its variant_id.

        Args:
            variant_id: Variant ID to search for

        Returns:
            VariantModel instance or None if not found
        """
        stmt = select(VariantModel).where(VariantModel.variant_id == variant_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def find_by_clinvar_id(self, clinvar_id: str) -> Optional[VariantModel]:
        """
        Find a variant by its ClinVar ID.

        Args:
            clinvar_id: ClinVar accession ID

        Returns:
            VariantModel instance or None if not found
        """
        stmt = select(VariantModel).where(VariantModel.clinvar_id == clinvar_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def find_by_gene(
        self, gene_id: int, limit: Optional[int] = None
    ) -> List[VariantModel]:
        """
        Find all variants associated with a specific gene.

        Args:
            gene_id: Gene ID to search variants for
            limit: Maximum number of variants to return

        Returns:
            List of VariantModel instances
        """
        stmt = select(VariantModel).where(VariantModel.gene_id == gene_id)
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def find_by_genomic_location(
        self, chromosome: str, start_pos: int, end_pos: int
    ) -> List[VariantModel]:
        """
        Find variants within a genomic region.

        Args:
            chromosome: Chromosome name
            start_pos: Start position (inclusive)
            end_pos: End position (inclusive)

        Returns:
            List of VariantModel instances in the region
        """
        stmt = select(VariantModel).where(
            and_(
                VariantModel.chromosome == chromosome,
                VariantModel.position >= start_pos,
                VariantModel.position <= end_pos,
            )
        )
        return list(self.session.execute(stmt).scalars())

    def find_by_clinical_significance(
        self, significance: ClinicalSignificance, limit: Optional[int] = None
    ) -> List[VariantModel]:
        """
        Find variants with specific clinical significance.

        Args:
            significance: Clinical significance level
            limit: Maximum number of variants to return

        Returns:
            List of VariantModel instances with the specified significance
        """
        stmt = select(VariantModel).where(
            VariantModel.clinical_significance == significance
        )
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def find_pathogenic_variants(
        self, limit: Optional[int] = None
    ) -> List[VariantModel]:
        """
        Find variants classified as pathogenic or likely pathogenic.

        Args:
            limit: Maximum number of variants to return

        Returns:
            List of pathogenic VariantModel instances
        """
        stmt = select(VariantModel).where(
            or_(
                VariantModel.clinical_significance == ClinicalSignificance.PATHOGENIC,
                VariantModel.clinical_significance
                == ClinicalSignificance.LIKELY_PATHOGENIC,
            )
        )
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def find_with_evidence(self, variant_id: int) -> Optional[VariantModel]:
        """
        Find a variant with its associated evidence loaded.

        Args:
            variant_id: Variant ID to retrieve

        Returns:
            VariantModel with evidence relationship loaded, or None if not found
        """
        stmt = select(VariantModel).where(VariantModel.id == variant_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_variant_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about variants in the database.

        Returns:
            Dictionary with variant statistics
        """
        # This would typically use aggregation queries
        total_variants = self.count()

        # Count by clinical significance (would need aggregation queries)
        pathogenic_count = len(self.find_pathogenic_variants())

        return {
            "total_variants": total_variants,
            "pathogenic_variants": pathogenic_count,
            "variants_with_evidence": 0,  # Would need join query
        }

    def find_by_variant_id_or_fail(self, variant_id: str) -> VariantModel:
        """
        Find a variant by variant_id, raising NotFoundError if not found.

        Args:
            variant_id: Variant ID to search for

        Returns:
            VariantModel instance

        Raises:
            NotFoundError: If variant is not found
        """
        variant = self.find_by_variant_id(variant_id)
        if variant is None:
            raise NotFoundError(f"Variant with variant_id '{variant_id}' not found")
        return variant
