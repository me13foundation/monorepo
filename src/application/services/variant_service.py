"""Application-level orchestration for variant workflows."""

from typing import Any, Dict, List, Optional, Tuple

from src.domain.entities.variant import EvidenceSummary, Variant
from src.domain.repositories.variant_repository import VariantRepository
from src.domain.repositories.evidence_repository import EvidenceRepository
from src.domain.services.variant_domain_service import VariantDomainService


class VariantApplicationService:
    """
    Application service for variant management use cases.

    Orchestrates domain services and repositories to implement
    variant-related business operations with proper dependency injection.
    """

    def __init__(
        self,
        variant_repository: VariantRepository,
        variant_domain_service: VariantDomainService,
        evidence_repository: EvidenceRepository,
    ):
        """
        Initialize the variant application service.

        Args:
            variant_repository: Domain repository for variants
            variant_domain_service: Domain service for variant business logic
            evidence_repository: Domain repository for evidence
        """
        self._variant_repository = variant_repository
        self._variant_domain_service = variant_domain_service
        self._evidence_repository = evidence_repository

    def create_variant(
        self,
        chromosome: str,
        position: int,
        reference_allele: str,
        alternate_allele: str,
        *,
        variant_id: Optional[str] = None,
        clinvar_id: Optional[str] = None,
        variant_type: str = "unknown",
        clinical_significance: str = "not_provided",
        hgvs_genomic: Optional[str] = None,
        hgvs_protein: Optional[str] = None,
        hgvs_cdna: Optional[str] = None,
        condition: Optional[str] = None,
        review_status: Optional[str] = None,
        allele_frequency: Optional[float] = None,
        gnomad_af: Optional[float] = None,
    ) -> Variant:
        """
        Create a new variant with validation and business rules.

        Args:
            chromosome: Chromosome location
            position: Genomic position
            reference_allele: Reference allele
            alternate_allele: Alternate allele
            variant_id: Optional variant identifier
            clinvar_id: ClinVar accession
            variant_type: Type of variant
            clinical_significance: Clinical significance
            hgvs_genomic: HGVS genomic notation
            hgvs_protein: HGVS protein notation
            hgvs_cdna: HGVS cDNA notation
            condition: Associated condition
            review_status: Review status
            allele_frequency: Allele frequency
            gnomad_af: gnomAD allele frequency

        Returns:
            Created Variant entity

        Raises:
            ValueError: If validation fails
        """
        # Create the variant entity
        variant_entity = Variant.create(
            chromosome=chromosome,
            position=position,
            reference_allele=reference_allele,
            alternate_allele=alternate_allele,
            variant_id=variant_id,
            clinvar_id=clinvar_id,
            variant_type=variant_type,
            clinical_significance=clinical_significance,
            hgvs_genomic=hgvs_genomic,
            hgvs_protein=hgvs_protein,
            hgvs_cdna=hgvs_cdna,
            condition=condition,
            review_status=review_status,
            allele_frequency=allele_frequency,
            gnomad_af=gnomad_af,
        )

        # Apply domain business logic
        variant_entity = self._variant_domain_service.apply_business_logic(
            variant_entity, "create"
        )

        # Validate business rules
        errors = self._variant_domain_service.validate_business_rules(
            variant_entity, "create"
        )
        if errors:
            raise ValueError(f"Business rule violations: {', '.join(errors)}")

        # Persist the entity
        return self._variant_repository.create(variant_entity)

    def get_variant_by_id(self, variant_id: str) -> Optional[Variant]:
        """Retrieve a variant by its variant_id."""
        return self._variant_repository.find_by_variant_id(variant_id)

    def get_variant_by_clinvar_id(self, clinvar_id: str) -> Optional[Variant]:
        """Retrieve a variant by its ClinVar ID."""
        return self._variant_repository.find_by_clinvar_id(clinvar_id)

    def get_variants_by_gene(
        self, gene_id: int, limit: Optional[int] = None
    ) -> List[Variant]:
        """Find variants associated with a gene."""
        return self._variant_repository.find_by_gene(gene_id, limit)

    def get_variants_by_chromosome_position(
        self, chromosome: str, position: int
    ) -> List[Variant]:
        """Find variants at a specific genomic position."""
        return self._variant_repository.find_by_chromosome_position(
            chromosome, position
        )

    def get_variants_by_clinical_significance(
        self, significance: str, limit: Optional[int] = None
    ) -> List[Variant]:
        """Find variants by clinical significance."""
        return self._variant_repository.find_by_clinical_significance(
            significance, limit
        )

    def search_variants(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Variant]:
        """Search variants with optional filters."""
        return self._variant_repository.search_variants(query, limit, filters)

    def list_variants(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Variant], int]:
        """Retrieve paginated variants with optional filters."""
        return self._variant_repository.paginate_variants(
            page, per_page, sort_by, sort_order, filters
        )

    def update_variant(self, variant_id: int, updates: Dict[str, Any]) -> Variant:
        """Update variant fields."""
        updated_variant = self._variant_repository.update(variant_id, updates)

        # Apply domain business logic to updated entity
        updated_variant = self._variant_domain_service.apply_business_logic(
            updated_variant, "update"
        )

        return updated_variant

    def update_variant_classification(
        self,
        variant_id: int,
        *,
        variant_type: Optional[str] = None,
        clinical_significance: Optional[str] = None,
    ) -> Variant:
        """
        Update variant classification information.

        Args:
            variant_id: Variant ID to update
            variant_type: New variant type
            clinical_significance: New clinical significance

        Returns:
            Updated Variant entity
        """
        variant = self._variant_repository.get_by_id(variant_id)
        if variant is None:
            raise ValueError(f"Variant with id {variant_id} not found")

        # Use domain service to update classification
        variant.update_classification(
            variant_type=variant_type,
            clinical_significance=clinical_significance,
        )

        # Validate the changes
        errors = self._variant_domain_service.validate_business_rules(variant, "update")
        if errors:
            raise ValueError(f"Business rule violations: {', '.join(errors)}")

        # Persist the changes
        return self._variant_repository.update(
            variant_id,
            {
                "variant_type": variant.variant_type,
                "clinical_significance": variant.clinical_significance,
            },
        )

    def get_variant_with_evidence(self, variant_id: int) -> Optional[Variant]:
        """
        Get a variant with its associated evidence loaded.

        Args:
            variant_id: Variant ID to retrieve

        Returns:
            Variant entity with evidence relationship loaded
        """
        variant = self._variant_repository.get_by_id(variant_id)
        if not variant:
            return None

        evidence_list = self._evidence_repository.find_by_variant(variant_id)
        summaries = [
            EvidenceSummary(
                evidence_id=evidence.id,
                evidence_level=evidence.evidence_level.value,
                evidence_type=evidence.evidence_type,
                description=evidence.description,
                reviewed=evidence.reviewed,
            )
            for evidence in evidence_list
        ]
        variant.evidence = summaries
        variant.evidence_count = len(summaries)
        return variant

    def assess_clinical_significance_confidence(self, variant_id: int) -> float:
        """
        Assess confidence in clinical significance based on evidence.

        Args:
            variant_id: Variant ID to assess

        Returns:
            Confidence score between 0.0 and 1.0
        """
        variant = self._variant_repository.get_by_id(variant_id)
        if not variant:
            return 0.0

        evidence_list = self._evidence_repository.find_by_variant(variant_id)
        return self._variant_domain_service.assess_clinical_significance_confidence(
            variant, evidence_list
        )

    def detect_evidence_conflicts(self, variant_id: int) -> List[str]:
        """
        Detect conflicting evidence for a variant.

        Args:
            variant_id: Variant ID to analyze

        Returns:
            List of conflict descriptions
        """
        variant = self._variant_repository.get_by_id(variant_id)
        if not variant:
            return []

        evidence_list = self._evidence_repository.find_by_variant(variant_id)
        conflicts = self._variant_domain_service.detect_evidence_conflicts(
            variant, evidence_list
        )

        return conflicts

    def get_variant_statistics(self) -> Dict[str, int | float | bool | str | None]:
        """Get statistics about variants in the repository."""
        return self._variant_repository.get_variant_statistics()

    def validate_variant_exists(self, variant_id: int) -> bool:
        """
        Validate that a variant exists.

        Args:
            variant_id: Variant ID to validate

        Returns:
            True if variant exists, False otherwise
        """
        return self._variant_repository.exists(variant_id)


__all__ = ["VariantApplicationService"]
