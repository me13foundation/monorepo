"""
Evidence service for MED13 Resource Library.
Business logic for evidence linking variants and phenotypes.
"""

from sqlalchemy.orm import Session

from src.domain.entities.evidence import Evidence
from src.infrastructure.repositories import SqlAlchemyEvidenceRepository
from src.services.domain.base_service import BaseService

EvidenceStatisticsValue = int | float | bool | str | None


class EvidenceService(BaseService[SqlAlchemyEvidenceRepository]):
    """
    Service for evidence business logic and operations.

    Provides high-level operations for evidence management including
    confidence assessment and relationship validation.
    """

    def __init__(
        self,
        session: Session | None = None,
        evidence_repository: SqlAlchemyEvidenceRepository | None = None,
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
        self,
        limit: int | None = None,
    ) -> list[Evidence]:
        """
        Find evidence with high confidence levels.

        Args:
            limit: Maximum number of evidence records to return

        Returns:
            List of high-confidence Evidence entities
        """
        return self.evidence_repo.find_high_confidence_evidence(limit)

    def find_relationship_evidence(
        self,
        variant_id: int,
        phenotype_id: int,
        min_confidence: float = 0.5,
    ) -> list[Evidence]:
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
            variant_id,
            phenotype_id,
            min_confidence,
        )

    def get_evidence_statistics(self) -> dict[str, EvidenceStatisticsValue]:
        """
        Get comprehensive statistics about evidence.

        Returns:
            Dictionary with evidence statistics
        """
        raw_stats: dict[
            str,
            EvidenceStatisticsValue,
        ] = self.evidence_repo.get_evidence_statistics()
        return dict(raw_stats)
