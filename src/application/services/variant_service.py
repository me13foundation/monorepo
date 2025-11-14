"""Application-level orchestration for variant workflows."""

from collections.abc import Sequence
from typing import cast

from src.domain.entities.evidence import Evidence
from src.domain.entities.variant import EvidenceSummary, Variant
from src.domain.repositories.evidence_repository import EvidenceRepository
from src.domain.repositories.variant_repository import VariantRepository
from src.domain.services.variant_domain_service import VariantDomainService
from src.type_definitions.common import QueryFilters, VariantUpdate


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

    def create_variant(  # noqa: PLR0913 - explicit variant creation fields
        self,
        chromosome: str,
        position: int,
        reference_allele: str,
        alternate_allele: str,
        *,
        variant_id: str | None = None,
        clinvar_id: str | None = None,
        variant_type: str = "unknown",
        clinical_significance: str = "not_provided",
        hgvs_genomic: str | None = None,
        hgvs_protein: str | None = None,
        hgvs_cdna: str | None = None,
        condition: str | None = None,
        review_status: str | None = None,
        allele_frequency: float | None = None,
        gnomad_af: float | None = None,
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
            variant_entity,
            "create",
        )

        # Validate business rules
        errors = self._variant_domain_service.validate_business_rules(
            variant_entity,
            "create",
        )
        if errors:
            msg = f"Business rule violations: {', '.join(errors)}"
            raise ValueError(msg)

        # Persist the entity
        return self._variant_repository.create(variant_entity)

    def get_variant_by_id(self, variant_id: str) -> Variant | None:
        """Retrieve a variant by its variant_id."""
        return self._variant_repository.find_by_variant_id(variant_id)

    def get_variant_by_clinvar_id(self, clinvar_id: str) -> Variant | None:
        """Retrieve a variant by its ClinVar ID."""
        return self._variant_repository.find_by_clinvar_id(clinvar_id)

    def get_variants_by_gene(
        self,
        gene_id: int,
        limit: int | None = None,
    ) -> list[Variant]:
        """Find variants associated with a gene."""
        return self._variant_repository.find_by_gene(gene_id, limit)

    def get_variants_by_chromosome_position(
        self,
        chromosome: str,
        position: int,
    ) -> list[Variant]:
        """Find variants at a specific genomic position."""
        return self._variant_repository.find_by_chromosome_position(
            chromosome,
            position,
        )

    def get_variants_by_clinical_significance(
        self,
        significance: str,
        limit: int | None = None,
    ) -> list[Variant]:
        """Find variants by clinical significance."""
        return self._variant_repository.find_by_clinical_significance(
            significance,
            limit,
        )

    def search_variants(
        self,
        query: str,
        limit: int = 10,
        filters: QueryFilters | None = None,
    ) -> list[Variant]:
        """Search variants with optional filters."""
        normalized_filters = self._normalize_filters(filters)
        return self._variant_repository.search_variants(
            query,
            limit,
            normalized_filters,
        )

    def get_pathogenic_variants(
        self,
        limit: int | None = None,
    ) -> list[Variant]:
        """Retrieve variants classified as pathogenic or likely pathogenic."""
        return self._variant_repository.find_pathogenic_variants(limit)

    def list_variants(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        filters: QueryFilters | None = None,
    ) -> tuple[list[Variant], int]:
        """Retrieve paginated variants with optional filters."""
        normalized_filters = self._normalize_filters(filters)
        return self._variant_repository.paginate_variants(
            page,
            per_page,
            sort_by,
            sort_order,
            normalized_filters,
        )

    def update_variant(self, variant_id: int, updates: VariantUpdate) -> Variant:
        """Update variant fields."""
        if not updates:
            msg = "No variant updates provided"
            raise ValueError(msg)

        updated_variant = self._variant_repository.update(variant_id, updates)
        return self._variant_domain_service.apply_business_logic(
            updated_variant,
            "update",
        )

    def update_variant_classification(
        self,
        variant_id: int,
        *,
        variant_type: str | None = None,
        clinical_significance: str | None = None,
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
            msg = f"Variant with id {variant_id} not found"
            raise ValueError(msg)

        # Use domain service to update classification
        variant.update_classification(
            variant_type=variant_type,
            clinical_significance=clinical_significance,
        )

        # Validate the changes
        errors = self._variant_domain_service.validate_business_rules(variant, "update")
        if errors:
            msg = f"Business rule violations: {', '.join(errors)}"
            raise ValueError(msg)

        # Persist the changes
        return self._variant_repository.update(
            variant_id,
            {
                "variant_type": variant.variant_type,
                "clinical_significance": variant.clinical_significance,
            },
        )

    def get_variant_with_evidence(self, variant_id: int) -> Variant | None:
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
        evidence_summaries = self._summarize_evidence(evidence_list)
        return self._variant_domain_service.assess_clinical_significance_confidence(
            variant,
            evidence_summaries,
        )

    def detect_evidence_conflicts(self, variant_id: int) -> list[str]:
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
        evidence_summaries = self._summarize_evidence(evidence_list)
        return self._variant_domain_service.detect_evidence_conflicts(
            variant,
            evidence_summaries,
        )

    def get_variant_statistics(self) -> dict[str, int | float | bool | str | None]:
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

    @staticmethod
    def _normalize_filters(
        filters: QueryFilters | None,
    ) -> QueryFilters | None:
        if filters is None:
            return None
        return cast("QueryFilters", dict(filters))

    @staticmethod
    def _summarize_evidence(
        evidence_list: Sequence[Evidence],
    ) -> tuple[EvidenceSummary, ...]:
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
        return tuple(summaries)


__all__ = ["VariantApplicationService"]
