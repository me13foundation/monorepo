"""
Evidence service for MED13 Resource Library.
Business logic for evidence linking variants and phenotypes.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from src.repositories import EvidenceRepository
from src.models.database import EvidenceModel
from src.services.domain.base_service import BaseService


class EvidenceService(BaseService[EvidenceModel]):
    """
    Service for evidence business logic and operations.

    Provides high-level operations for evidence management including
    confidence assessment and relationship validation.
    """

    def __init__(self, session: Optional[Session] = None):
        super().__init__(session)
        self.evidence_repo = EvidenceRepository(session)

    @property
    def repository(self) -> EvidenceRepository:
        return self.evidence_repo

    def find_high_confidence_evidence(
        self, limit: Optional[int] = None
    ) -> List[EvidenceModel]:
        """
        Find evidence with high confidence levels.

        Args:
            limit: Maximum number of evidence records to return

        Returns:
            List of high-confidence EvidenceModel instances
        """
        return self.evidence_repo.find_high_confidence_evidence(limit)

    def find_relationship_evidence(
        self, variant_id: int, phenotype_id: int, min_confidence: float = 0.5
    ) -> List[EvidenceModel]:
        """
        Find evidence supporting the relationship between a variant and phenotype.

        Args:
            variant_id: Variant ID
            phenotype_id: Phenotype ID
            min_confidence: Minimum confidence score

        Returns:
            List of EvidenceModel instances supporting the relationship
        """
        return self.evidence_repo.find_relationship_evidence(
            variant_id, phenotype_id, min_confidence
        )

    def get_evidence_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about evidence.

        Returns:
            Dictionary with evidence statistics
        """
        return self.evidence_repo.get_evidence_statistics()
