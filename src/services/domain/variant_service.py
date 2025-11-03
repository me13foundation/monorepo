"""
Variant service for MED13 Resource Library.
Business logic for genetic variant operations.
"""

from typing import Dict, List, Optional, TYPE_CHECKING
from sqlalchemy.orm import Session

from src.domain.entities.evidence import Evidence
from src.domain.entities.variant import EvidenceSummary, Variant
from src.infrastructure.repositories import (
    SqlAlchemyEvidenceRepository,
    SqlAlchemyVariantRepository,
)
from src.services.domain.base_service import BaseService

if TYPE_CHECKING:
    pass

VariantStatisticsValue = int | float | bool | str | None


class VariantService(BaseService[SqlAlchemyVariantRepository]):
    """
    Service for variant business logic and operations.

    Provides high-level operations for variant management including
    clinical significance assessment and relationship management.
    """

    def __init__(
        self,
        session: Optional[Session] = None,
        variant_repository: Optional[SqlAlchemyVariantRepository] = None,
    ):
        super().__init__(session)
        self.variant_repo = (
            variant_repository
            if variant_repository
            else SqlAlchemyVariantRepository(session)
        )
        self.evidence_repo = SqlAlchemyEvidenceRepository(session)

    @property
    def repository(self) -> SqlAlchemyVariantRepository:
        return self.variant_repo

    def get_pathogenic_variants(self, limit: Optional[int] = None) -> List[Variant]:
        """
        Get variants classified as pathogenic or likely pathogenic.

        Args:
            limit: Maximum number of variants to return

        Returns:
            List of pathogenic Variant entities
        """
        return self.variant_repo.find_pathogenic_variants(limit)

    def get_variant_with_evidence(self, variant_id: int) -> Optional[Variant]:
        """
        Get a variant with its associated evidence loaded.

        Args:
            variant_id: Variant ID to retrieve

        Returns:
            Variant entity with evidence summaries
        """
        variant = self.variant_repo.get_by_id(variant_id)
        if variant is None:
            return None

        evidence_records = self.evidence_repo.find_by_variant(variant_id)
        variant.evidence = [
            self._build_evidence_summary(evidence) for evidence in evidence_records
        ]
        variant.evidence_count = len(variant.evidence)
        return variant

    def get_variant_statistics(self) -> Dict[str, VariantStatisticsValue]:
        """
        Get comprehensive statistics about variants.

        Returns:
            Dictionary with variant statistics
        """
        raw_stats: Dict[
            str, VariantStatisticsValue
        ] = self.variant_repo.get_variant_statistics()
        return dict(raw_stats)

    @staticmethod
    def _build_evidence_summary(evidence_model: Evidence) -> EvidenceSummary:
        return EvidenceSummary(
            evidence_id=evidence_model.id,
            evidence_level=evidence_model.evidence_level.value,
            evidence_type=evidence_model.evidence_type,
            description=evidence_model.description,
            reviewed=evidence_model.reviewed,
        )
