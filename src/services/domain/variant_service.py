"""
Variant service for MED13 Resource Library.
Business logic for genetic variant operations.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from src.repositories import VariantRepository, GeneRepository, EvidenceRepository
from src.models.database import VariantModel
from src.services.domain.base_service import BaseService


class VariantService(BaseService[VariantModel]):
    """
    Service for variant business logic and operations.

    Provides high-level operations for variant management including
    clinical significance assessment and relationship management.
    """

    def __init__(self, session: Optional[Session] = None):
        super().__init__(session)
        self.variant_repo = VariantRepository(session)
        self.gene_repo = GeneRepository(session)
        self.evidence_repo = EvidenceRepository(session)

    @property
    def repository(self) -> VariantRepository:
        return self.variant_repo

    def get_pathogenic_variants(
        self, limit: Optional[int] = None
    ) -> List[VariantModel]:
        """
        Get variants classified as pathogenic or likely pathogenic.

        Args:
            limit: Maximum number of variants to return

        Returns:
            List of pathogenic VariantModel instances
        """
        return self.variant_repo.find_pathogenic_variants(limit)

    def get_variant_with_evidence(self, variant_id: int) -> Optional[VariantModel]:
        """
        Get a variant with its associated evidence loaded.

        Args:
            variant_id: Variant ID to retrieve

        Returns:
            VariantModel with evidence relationship loaded
        """
        variant = self.variant_repo.get_by_id(variant_id)
        if variant:
            variant.evidence = self.evidence_repo.find_by_variant(variant_id)
        return variant

    def get_variant_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about variants.

        Returns:
            Dictionary with variant statistics
        """
        return self.variant_repo.get_variant_statistics()
