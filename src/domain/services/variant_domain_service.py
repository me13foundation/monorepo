"""
Variant domain service - pure business logic for variant entities.

Encapsulates variant-specific business rules, validations, and logic
without infrastructure dependencies.
"""

from collections import Counter
from collections.abc import Mapping, Sequence

from src.domain.entities.variant import EvidenceSummary, Variant, VariantType
from src.domain.services.base import DomainService
from src.type_definitions.domain import VariantDerivedProperties


class VariantDomainService(DomainService[Variant]):
    """
    Domain service for Variant business logic.

    Contains pure business rules for variant validation, clinical significance
    assessment, and derived property calculations.
    """

    def validate_business_rules(
        self,
        entity: Variant,
        operation: str,
        context: Mapping[str, object] | None = None,
    ) -> list[str]:
        """
        Validate variant business rules.

        Args:
            entity: Variant entity to validate
            operation: Operation being performed
            context: Additional validation context

        Returns:
            List of validation error messages
        """
        del operation, context
        errors = []

        # Genomic coordinate validation
        if entity.position < 1:
            errors.append("Genomic position must be positive")

        # Allele validation
        if not entity.reference_allele or not entity.alternate_allele:
            errors.append("Reference and alternate alleles are required")

        # Frequency validation
        if entity.allele_frequency is not None and not (
            0.0 <= entity.allele_frequency <= 1.0
        ):
            errors.append("Allele frequency must be between 0.0 and 1.0")

        if entity.gnomad_af is not None and not (0.0 <= entity.gnomad_af <= 1.0):
            errors.append("gnomAD frequency must be between 0.0 and 1.0")

        # HGVS validation (basic)
        if entity.hgvs_genomic and not self._is_valid_hgvs(entity.hgvs_genomic):
            errors.append("Invalid HGVS genomic notation format")

        if entity.hgvs_protein and not self._is_valid_hgvs(entity.hgvs_protein):
            errors.append("Invalid HGVS protein notation format")

        return errors

    def apply_business_logic(self, entity: Variant, operation: str) -> Variant:
        """
        Apply variant business logic transformations.

        Args:
            entity: Variant entity to transform
            operation: Operation being performed

        Returns:
            Transformed variant entity
        """
        # Infer variant type if not specified
        if (
            operation in ("create", "update")
            and entity.variant_type == VariantType.UNKNOWN
        ):
            entity.variant_type = self._infer_variant_type(
                entity.reference_allele,
                entity.alternate_allele,
            )

        # Normalize chromosome format
        entity.chromosome = self._normalize_chromosome(entity.chromosome)

        return entity

    def calculate_derived_properties(self, entity: Variant) -> dict[str, object]:
        """
        Calculate derived properties for a variant.

        Args:
            entity: Variant entity

        Returns:
            Dictionary of derived properties
        """
        # Check if variant has population frequency data
        raw_frequencies = [entity.allele_frequency, entity.gnomad_af]
        population_frequencies: list[float] = [
            freq for freq in raw_frequencies if freq is not None
        ]
        has_population_data = bool(population_frequencies)
        population_frequency_count = len(population_frequencies)

        # Calculate average population frequency
        average_population_frequency = None
        if has_population_data:
            average_population_frequency = sum(population_frequencies) / len(
                population_frequencies,
            )

        # Determine functional impact (simplified - based on variant type)
        has_functional_impact = entity.variant_type in [
            "nonsense",
            "frameshift",
            "splice_site",
        ]

        # Count evidence
        evidence_count = len(entity.evidence) if entity.evidence else 0

        # Calculate significance consistency score
        significance_consistency_score = 0.5  # Default neutral score
        if entity.evidence:
            significance_consistency_score = self._calculate_significance_consistency(
                entity.evidence,
            )

        # Create typed result for internal type safety
        result = VariantDerivedProperties(
            has_population_data=has_population_data,
            population_frequency_count=population_frequency_count,
            average_population_frequency=average_population_frequency,
            has_functional_impact=has_functional_impact,
            evidence_count=evidence_count,
            significance_consistency_score=significance_consistency_score,
        )

        # Return as dict for base class compatibility
        return result.__dict__

    def assess_clinical_significance_confidence(
        self,
        _variant: Variant,
        evidence_list: Sequence[EvidenceSummary],
    ) -> float:
        """
        Assess confidence in clinical significance based on evidence.

        Args:
            variant: Variant entity
            evidence_list: List of evidence records

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not evidence_list:
            return 0.0

        # Simplified confidence calculation
        base_confidence = 0.5

        # Evidence count factor
        evidence_factor = min(len(evidence_list) * 0.1, 0.3)

        # Clinical significance consistency factor
        significance_consistency = self._calculate_significance_consistency(
            evidence_list,
        )
        consistency_factor = significance_consistency * 0.2

        return min(base_confidence + evidence_factor + consistency_factor, 1.0)

    def detect_evidence_conflicts(
        self,
        _variant: Variant,
        evidence_list: Sequence[EvidenceSummary],
    ) -> list[str]:
        """
        Detect conflicting evidence for a variant.

        Args:
            variant: Variant entity
            evidence_list: List of evidence records

        Returns:
            List of conflict descriptions
        """
        conflicts: list[str] = []

        evidence_conflict_min = 2
        if len(evidence_list) < evidence_conflict_min:
            return conflicts

        significances = [
            ev.clinical_significance
            for ev in evidence_list
            if hasattr(ev, "clinical_significance")
        ]

        # Check for pathogenic vs benign conflicts
        pathogenic_count = sum(1 for s in significances if "pathogenic" in s.lower())
        benign_count = sum(1 for s in significances if "benign" in s.lower())

        if pathogenic_count > 0 and benign_count > 0:
            conflicts.append(
                f"Conflicting clinical significance: {pathogenic_count} pathogenic vs {benign_count} benign",
            )

        # Check frequency discrepancies
        frequencies = [
            ev.allele_frequency
            for ev in evidence_list
            if hasattr(ev, "allele_frequency") and ev.allele_frequency is not None
        ]
        if len(frequencies) > 1:
            freq_range = max(frequencies) - min(frequencies)
            freq_discrepancy_threshold = 0.01
            if freq_range > freq_discrepancy_threshold:  # More than 1% difference
                conflicts.append(f"Large frequency discrepancy: {freq_range:.4f}")

        return conflicts

    def normalize_hgvs_notation(self, hgvs: str) -> str:
        """
        Normalize HGVS notation according to standards.

        Args:
            hgvs: Raw HGVS notation

        Returns:
            Normalized HGVS notation
        """
        if not hgvs:
            return hgvs

        # Basic normalization - in reality this would be much more complex
        # Ensure consistent formatting for common patterns (simplified)
        return hgvs.strip()

    def _is_rare_variant(self, variant: Variant) -> bool:
        """Determine if a variant is considered rare."""
        # Use the lower frequency for assessment
        frequency = variant.allele_frequency
        if variant.gnomad_af is not None and (
            frequency is None or variant.gnomad_af < frequency
        ):
            frequency = variant.gnomad_af

        if frequency is None:
            return False  # Unknown frequency

        rare_variant_threshold = 0.01
        return frequency < rare_variant_threshold  # Less than 1%

    def _calculate_complexity_score(self, variant: Variant) -> float:
        """Calculate variant complexity score."""
        score = 0.0

        # Type complexity
        if variant.variant_type == VariantType.STRUCTURAL:
            score += 1.0
        elif variant.variant_type == VariantType.CNV:
            score += 0.7
        elif variant.variant_type == VariantType.INDEL:
            score += 0.5

        # Allele complexity
        ref_len = len(variant.reference_allele)
        alt_len = len(variant.alternate_allele)
        if ref_len != alt_len:
            score += min(abs(ref_len - alt_len) * 0.1, 0.5)

        return min(score, 1.0)

    def _assess_pathogenicity_likelihood(self, variant: Variant) -> str:
        """Assess likelihood of pathogenicity."""
        significance = variant.clinical_significance.lower()

        if "pathogenic" in significance:
            return "high"
        if "likely_pathogenic" in significance:
            return "medium"
        if "uncertain" in significance:
            return "unknown"
        if "likely_benign" in significance:
            return "low"
        if "benign" in significance:
            return "very_low"
        return "unknown"

    def _check_frequency_discrepancy(self, variant: Variant) -> bool:
        """Check for discrepancies between reported and population frequencies."""
        if variant.allele_frequency is None or variant.gnomad_af is None:
            return False

        # Flag if difference is more than 5%
        mismatch_threshold = 0.05
        return abs(variant.allele_frequency - variant.gnomad_af) > mismatch_threshold

    def _calculate_significance_consistency(
        self,
        evidence_list: Sequence[EvidenceSummary],
    ) -> float:
        """Calculate consistency of clinical significance across evidence."""
        if not evidence_list:
            return 0.0

        significances = [
            ev.clinical_significance.lower()
            for ev in evidence_list
            if hasattr(ev, "clinical_significance") and ev.clinical_significance
        ]

        if not significances:
            return 0.0

        # Count most common significance
        most_common = Counter(significances).most_common(1)[0][1]

        return most_common / len(significances)

    def _infer_variant_type(self, ref: str, alt: str) -> str:
        """Infer variant type from alleles."""
        ref_len = len(ref)
        alt_len = len(alt)

        if ref_len == 1 and alt_len == 1:
            return VariantType.SNV
        if ref_len != alt_len:
            return VariantType.INDEL
        # Could be more complex analysis here
        return VariantType.UNKNOWN

    def _normalize_chromosome(self, chromosome: str) -> str:
        """Normalize chromosome notation."""
        if not chromosome:
            return chromosome

        chrom = chromosome.strip().upper()
        if not chrom.startswith("CHR"):
            chrom = f"CHR{chrom}"

        return chrom

    def _is_valid_hgvs(self, hgvs: str) -> bool:
        """Basic HGVS notation validation."""
        if not hgvs:
            return False

        # Very basic validation - real implementation would be much more sophisticated
        return ":" in hgvs and any(
            hgvs.startswith(prefix) for prefix in ["c.", "g.", "m.", "n.", "p."]
        )


__all__ = ["VariantDomainService"]
