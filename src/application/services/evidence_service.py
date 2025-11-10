"""
Evidence application service orchestration layer.

Coordinates domain services and repositories to implement evidence management
use cases while preserving domain purity and strong typing.
"""

from datetime import date
from typing import Any, cast

from src.domain.entities.evidence import Evidence, EvidenceType
from src.domain.repositories.evidence_repository import EvidenceRepository
from src.domain.services.evidence_domain_service import EvidenceDomainService
from src.domain.value_objects.confidence import Confidence, EvidenceLevel
from src.type_definitions.common import EvidenceUpdate, QueryFilters


class EvidenceApplicationService:
    """
    Application service for evidence management use cases.

    Orchestrates domain services and repositories to implement
    evidence-related business operations with proper dependency injection.
    """

    def __init__(
        self,
        evidence_repository: EvidenceRepository,
        evidence_domain_service: EvidenceDomainService,
    ):
        """
        Initialize the evidence application service.

        Args:
            evidence_repository: Domain repository for evidence
            evidence_domain_service: Domain service for evidence business logic
        """
        self._evidence_repository = evidence_repository
        self._evidence_domain_service = evidence_domain_service

    def create_evidence(  # noqa: PLR0913 - request fields kept explicit for clarity
        self,
        *,
        variant_id: int,
        phenotype_id: int,
        description: str,
        evidence_type: str = EvidenceType.LITERATURE_REVIEW,
        evidence_level: EvidenceLevel = EvidenceLevel.SUPPORTING,
        publication_id: int | None = None,
        summary: str | None = None,
        confidence_score: float | None = None,
        quality_score: int | None = None,
        sample_size: int | None = None,
        study_type: str | None = None,
        statistical_significance: str | None = None,
        reviewed: bool = False,
        review_date: date | None = None,
        reviewer_notes: str | None = None,
    ) -> Evidence:
        """
        Create new evidence with validation and business rules.

        Args:
            variant_id: Associated variant ID
            phenotype_id: Associated phenotype ID
            description: Evidence description
            evidence_type: Type of evidence
            evidence_level: Level of evidence confidence
            publication_id: Associated publication ID
            summary: Evidence summary text
            confidence_score: Optional confidence score override
            quality_score: Optional evidence quality score
            sample_size: Optional sample size metadata
            study_type: Optional description of study type
            statistical_significance: Optional statistical significance details
            reviewed: Whether the evidence has been reviewed
            review_date: Date the evidence was reviewed
            reviewer_notes: Additional reviewer notes

        Returns:
            Created Evidence entity

        Raises:
            ValueError: If validation fails
        """
        # Create the evidence entity
        confidence = (
            Confidence.from_score(confidence_score, sample_size=sample_size)
            if confidence_score is not None
            else Confidence.from_score(0.5, sample_size=sample_size)
        ).update_level(evidence_level)

        evidence_entity = Evidence(
            variant_id=variant_id,
            phenotype_id=phenotype_id,
            description=description,
            summary=summary,
            evidence_level=evidence_level,
            evidence_type=EvidenceType.validate(evidence_type),
            confidence=confidence,
            publication_id=publication_id,
            quality_score=quality_score,
            sample_size=sample_size,
            study_type=study_type,
            statistical_significance=statistical_significance,
            reviewed=reviewed,
            review_date=review_date,
            reviewer_notes=reviewer_notes,
        )

        # Apply domain business logic
        evidence_entity = self._evidence_domain_service.apply_business_logic(
            evidence_entity,
            "create",
        )

        # Validate business rules
        errors = self._evidence_domain_service.validate_business_rules(
            evidence_entity,
            "create",
        )
        if errors:
            msg = "Business rule violations: " + ", ".join(errors)
            raise ValueError(msg)

        # Persist the entity
        return self._evidence_repository.create(evidence_entity)

    def get_evidence_by_id(self, evidence_id: int) -> Evidence | None:
        """Retrieve a specific evidence record by its database ID."""
        return self._evidence_repository.get_by_id(evidence_id)

    def get_evidence_by_variant(self, variant_id: int) -> list[Evidence]:
        """Find evidence records for a variant."""
        return self._evidence_repository.find_by_variant(variant_id)

    def get_evidence_by_gene(self, gene_id: int) -> list[Evidence]:
        """Find evidence records for a gene."""
        return self._evidence_repository.find_by_gene(gene_id)

    def get_evidence_by_phenotype(self, phenotype_id: int) -> list[Evidence]:
        """Find evidence records for a phenotype."""
        return self._evidence_repository.find_by_phenotype(phenotype_id)

    def get_evidence_by_publication(self, publication_id: int) -> list[Evidence]:
        """Find evidence records for a publication."""
        return self._evidence_repository.find_by_publication(publication_id)

    def get_evidence_by_level(self, level: EvidenceLevel) -> list[Evidence]:
        """Find evidence records by evidence level."""
        return self._evidence_repository.find_by_evidence_level(level.value)

    def get_evidence_by_confidence_range(
        self,
        min_score: float,
        max_score: float,
    ) -> list[Evidence]:
        """Find evidence records within confidence score range."""
        return self._evidence_repository.find_by_confidence_score(min_score, max_score)

    def get_evidence_by_source(self, source: str) -> list[Evidence]:
        """Find evidence records from a specific source."""
        return self._evidence_repository.find_by_source(source)

    def find_high_confidence_evidence(
        self,
        limit: int | None = None,
    ) -> list[Evidence]:
        """Retrieve evidence records exceeding the high-confidence threshold."""
        return self._evidence_repository.find_high_confidence_evidence(limit)

    def find_relationship_evidence(
        self,
        variant_id: int,
        phenotype_id: int,
        min_confidence: float = 0.5,
    ) -> list[Evidence]:
        """Retrieve evidence linking a variant and phenotype with minimum confidence."""
        return self._evidence_repository.find_relationship_evidence(
            variant_id,
            phenotype_id,
            min_confidence,
        )

    def search_evidence(
        self,
        query: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[Evidence]:
        """Search evidence with optional filters."""
        normalized_filters = self._normalize_filters(filters)
        return self._evidence_repository.search_evidence(
            query,
            limit,
            normalized_filters,
        )

    def list_evidence(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[Evidence], int]:
        """Retrieve paginated evidence with optional filters."""
        normalized_filters = self._normalize_filters(filters)
        return self._evidence_repository.paginate_evidence(
            page,
            per_page,
            sort_by,
            sort_order,
            normalized_filters,
        )

    def update_evidence(self, evidence_id: int, updates: EvidenceUpdate) -> Evidence:
        """Update evidence fields."""
        if not updates:
            msg = "No evidence updates provided"
            raise ValueError(msg)

        updated_evidence = self._evidence_repository.update(evidence_id, updates)
        return self._evidence_domain_service.apply_business_logic(
            updated_evidence,
            "update",
        )

    def detect_evidence_conflicts(self, variant_id: int) -> list[dict[str, Any]]:
        """
        Detect conflicts between evidence records for a variant.

        Args:
            variant_id: Variant ID to analyze

        Returns:
            List of conflict descriptions with details
        """
        evidence_list = self._evidence_repository.find_by_variant(variant_id)
        return self._evidence_domain_service.detect_evidence_conflicts(evidence_list)

    def calculate_evidence_consensus(self, variant_id: int) -> dict[str, Any]:
        """
        Calculate consensus from multiple evidence records for a variant.

        Args:
            variant_id: Variant ID to analyze

        Returns:
            Consensus information
        """
        evidence_list = self._evidence_repository.find_by_variant(variant_id)
        return self._evidence_domain_service.calculate_evidence_consensus(evidence_list)

    def score_evidence_quality(self, evidence_id: int) -> float:
        """
        Score the quality of an evidence record.

        Args:
            evidence_id: Evidence record ID to score

        Returns:
            Quality score between 0.0 and 1.0
        """
        evidence = self._evidence_repository.get_by_id(evidence_id)
        if not evidence:
            return 0.0

        return self._evidence_domain_service.score_evidence_quality(evidence)

    def get_evidence_statistics(self) -> dict[str, int | float | bool | str | None]:
        """Get statistics about evidence in the repository."""
        return self._evidence_repository.get_evidence_statistics()

    def find_conflicting_evidence(self, variant_id: int) -> list[Evidence]:
        """Find conflicting evidence records for a variant."""
        return self._evidence_repository.find_conflicting_evidence(variant_id)

    def validate_evidence_exists(self, evidence_id: int) -> bool:
        """
        Validate that evidence exists.

        Args:
            evidence_id: Evidence ID to validate

        Returns:
            True if evidence exists, False otherwise
        """
        return self._evidence_repository.exists(evidence_id)

    @staticmethod
    def _normalize_filters(
        filters: dict[str, Any] | None,
    ) -> QueryFilters | None:
        if filters is None:
            return None
        return cast("QueryFilters", dict(filters))


__all__ = ["EvidenceApplicationService"]
