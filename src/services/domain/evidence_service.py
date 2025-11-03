"""
Evidence service for MED13 Resource Library.
Business logic for evidence linking variants and phenotypes.
"""

from typing import Dict, List, Optional, TYPE_CHECKING
from sqlalchemy.orm import Session

from src.domain.entities.evidence import Evidence
from src.infrastructure.repositories import SqlAlchemyEvidenceRepository
from src.services.domain.base_service import BaseService

if TYPE_CHECKING:
    pass

EvidenceStatisticsValue = int | float | bool | str | None


class EvidenceService(BaseService[SqlAlchemyEvidenceRepository]):
    """
    Service for evidence business logic and operations.

    Provides high-level operations for evidence management including
    confidence assessment and relationship validation.
    """

    def __init__(
        self,
        session: Optional[Session] = None,
        evidence_repository: Optional[SqlAlchemyEvidenceRepository] = None,
    ):
        super().__init__(session)
        self.evidence_repo = (
            evidence_repository
            if evidence_repository
            else SqlAlchemyEvidenceRepository(session)
        )

    @property
    def repository(self) -> SqlAlchemyEvidenceRepository:
        return self.evidence_repo

    def find_high_confidence_evidence(
        self, limit: Optional[int] = None
    ) -> List[Evidence]:
        """
        Find evidence with high confidence levels.

        Args:
            limit: Maximum number of evidence records to return

        Returns:
            List of high-confidence Evidence entities
        """
        return self.evidence_repo.find_high_confidence_evidence(limit)

    def find_relationship_evidence(
        self, variant_id: int, phenotype_id: int, min_confidence: float = 0.5
    ) -> List[Evidence]:
        """
        Find evidence supporting the relationship between a variant and phenotype.

        Args:
            variant_id: Variant ID
            phenotype_id: Phenotype ID
            min_confidence: Minimum confidence score

        Returns:
            List of Evidence entities supporting the relationship
        """
        return self.evidence_repo.find_relationship_evidence(
            variant_id, phenotype_id, min_confidence
        )

    def get_evidence_statistics(self) -> Dict[str, EvidenceStatisticsValue]:
        """
        Get comprehensive statistics about evidence.

        Returns:
            Dictionary with evidence statistics
        """
        raw_stats: Dict[str, object] = self.evidence_repo.get_evidence_statistics()
        stats: Dict[str, EvidenceStatisticsValue] = {}
        for key, value in raw_stats.items():
            if isinstance(value, (int, float, bool, str)) or value is None:
                stats[key] = value
        return stats
