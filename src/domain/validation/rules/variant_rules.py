"""
Advanced validation rules for genetic variant entities.

Implements business logic validation for variants including:
- HGVS notation compliance
- Clinical significance validation
- Allele frequency checks
- Functional impact assessment
- Population genetics validation
"""

import re
from typing import Dict, List, Any
from dataclasses import dataclass

from .base_rules import ValidationRule, ValidationSeverity


@dataclass
class VariantValidationRules:
    """
    Comprehensive validation rules for genetic variant entities.

    Validates variant notations, clinical data, population frequencies,
    and functional annotations for scientific accuracy.
    """

    # HGVS notation patterns (more comprehensive than basic validation)
    HGVS_PATTERNS = {
        "c": re.compile(r"^c\.\d+[_+-]\d+.*$|^c\.\d+.*$|^c\.\*\d+.*$"),
        "p": re.compile(
            r"^p\.\([A-Z][a-z]{2}\d+[A-Z][a-z]{2}\)$|^p\.[A-Z][a-z]{2}\d+[A-Z][a-z]{2}$|^p\.\w+\d+\w+$"
        ),
        "g": re.compile(r"^g\.\d+[_+-]\d+.*$|^g\.\d+.*$|^g\.\*\d+.*$"),
        "n": re.compile(r"^n\.\d+.*$"),
        "r": re.compile(r"^r\.\d+.*$"),
    }

    # Valid clinical significance terms (expanded)
    VALID_CLINICAL_SIGNIFICANCE = {
        "pathogenic",
        "likely pathogenic",
        "uncertain significance",
        "likely benign",
        "benign",
        "conflicting interpretations",
        "not provided",
        "other",
        "drug response",
        "protective",
        "risk factor",
        "association",
        "affects",
    }

    # Population frequency thresholds
    COMMON_VARIANT_THRESHOLD = 0.01  # 1%
    RARE_VARIANT_THRESHOLD = 0.001  # 0.1%

    @staticmethod
    def validate_hgvs_notation_comprehensive(
        hgvs_notation: str, notation_type: str
    ) -> ValidationRule:
        """Comprehensive HGVS notation validation."""

        def rule(value):
            if not value:
                return True, "", None  # Optional field

            if not isinstance(value, str):
                return (
                    False,
                    f"HGVS notation must be string: {type(value)}",
                    "Provide HGVS notation as string",
                )

            notation = value.strip()

            # Check basic format
            if notation_type in VariantValidationRules.HGVS_PATTERNS:
                pattern = VariantValidationRules.HGVS_PATTERNS[notation_type]
                if not pattern.match(notation):
                    return (
                        False,
                        f"Invalid HGVS {notation_type} format: {notation}",
                        f"Check HGVS {notation_type} notation syntax",
                    )

            # Additional validation for specific types
            if notation_type == "p":
                # Protein notation specific checks
                if "=" in notation:
                    return (
                        False,
                        "HGVS p. notation should not contain '=' for substitutions",
                        "Use amino acid codes, not '='",
                    )

                # Check for common mistakes
                if re.search(r"p\.\w+\d+\w+/\w+", notation):  # Old format with slash
                    return (
                        False,
                        "Old HGVS format detected",
                        "Use parentheses for complex changes: p.(Arg123His)",
                    )

            elif notation_type in ["c", "g", "n"]:
                # DNA notation checks
                if re.search(r"[acgtu][ACGTU]", notation):  # Mixed case nucleotides
                    return (
                        False,
                        "Mixed case nucleotides in HGVS notation",
                        "Use uppercase for nucleotides",
                    )

            # Check for suspicious patterns
            suspicious_patterns = [
                (r"\?+", "Excessive uncertainty markers"),
                (r"\(\)", "Empty parentheses"),
                (r"\[\]", "Empty brackets"),
            ]

            for pattern, description in suspicious_patterns:
                if re.search(pattern, notation):
                    return (
                        False,
                        f"Suspicious pattern in HGVS notation: {description}",
                        "Review HGVS notation",
                    )

            return True, "", None

        return ValidationRule(
            field="hgvs_notations",
            rule=f"hgvs_{notation_type}_comprehensive",
            validator=rule,
            severity=ValidationSeverity.ERROR,
            level="STANDARD",
        )

    @staticmethod
    def validate_clinical_significance_comprehensive(
        clinical_sig: str,
    ) -> ValidationRule:
        """Comprehensive clinical significance validation."""

        def rule(value):
            if not value:
                return True, "", None  # Can be empty

            if not isinstance(value, str):
                return (
                    False,
                    f"Clinical significance must be string: {type(value)}",
                    "Provide clinical significance as string",
                )

            sig_lower = value.lower().strip()

            # Check against valid terms
            if sig_lower not in VariantValidationRules.VALID_CLINICAL_SIGNIFICANCE:
                # Check for close matches or typos
                close_matches = []
                for valid_term in VariantValidationRules.VALID_CLINICAL_SIGNIFICANCE:
                    if sig_lower in valid_term or valid_term in sig_lower:
                        close_matches.append(valid_term)

                if close_matches:
                    return (
                        False,
                        f"Possible typo in clinical significance: '{value}'",
                        f"Did you mean: {', '.join(close_matches)}?",
                    )
                else:
                    return (
                        False,
                        f"Unknown clinical significance: '{value}'",
                        f"Valid terms: {', '.join(sorted(VariantValidationRules.VALID_CLINICAL_SIGNIFICANCE))}",
                    )

            # Check for conflicting terms
            conflicting_terms = [
                ("pathogenic", "benign"),
                ("likely pathogenic", "likely benign"),
                ("pathogenic", "protective"),
            ]

            for term1, term2 in conflicting_terms:
                if term1 in sig_lower and term2 in sig_lower:
                    return (
                        False,
                        f"Conflicting clinical significance terms: {term1} vs {term2}",
                        "Clinical significance should not contain conflicting terms",
                    )

            return True, "", None

        return ValidationRule(
            field="clinical_significance",
            rule="clinical_significance_comprehensive",
            validator=rule,
            severity=ValidationSeverity.WARNING,
            level="STANDARD",
        )

    @staticmethod
    def validate_population_frequencies(
        frequencies: Dict[str, float],
    ) -> ValidationRule:
        """Validate population allele frequencies."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None  # Optional field

            issues = []

            for population, frequency in value.items():
                if not isinstance(frequency, (int, float)):
                    issues.append(
                        f"Frequency for {population} must be numeric: {type(frequency)}"
                    )
                    continue

                if not (0.0 <= frequency <= 1.0):
                    issues.append(
                        f"Frequency for {population} out of range [0,1]: {frequency}"
                    )

                # Check for biologically implausible frequencies
                if frequency > 0.5:
                    issues.append(
                        f"Suspiciously high frequency for {population}: {frequency} (>50%)"
                    )

            # Check consistency between populations
            if len(value) > 1:
                frequencies_list = list(value.values())
                max_freq = max(frequencies_list)
                min_freq = min(frequencies_list)

                # Large discrepancies might indicate data issues
                if max_freq > min_freq * 10:
                    issues.append("Large frequency discrepancies between populations")

            if issues:
                return (
                    False,
                    "Population frequency issues: " + "; ".join(issues),
                    "Review frequency data",
                )

            return True, "", None

        return ValidationRule(
            field="population_frequencies",
            rule="population_frequencies",
            validator=rule,
            severity=ValidationSeverity.WARNING,
            level="STANDARD",
        )

    @staticmethod
    def validate_allele_frequencies_vs_clinical_sig(
        frequencies: Dict[str, Any], clinical_sig: str
    ) -> ValidationRule:
        """Validate consistency between allele frequencies and clinical significance."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None

            freq_data = value.get("frequencies", {})
            clinical_sig = value.get("clinical_significance", "")

            if not freq_data or not clinical_sig:
                return True, "", None  # Cannot validate without both

            clinical_lower = clinical_sig.lower()
            max_freq = max(freq_data.values()) if freq_data else 0

            # Pathogenic variants should generally be rare
            if (
                "pathogenic" in clinical_lower
                and max_freq > VariantValidationRules.COMMON_VARIANT_THRESHOLD
            ):
                return (
                    False,
                    f"Pathogenic variant with high frequency ({max_freq:.4f})",
                    "Pathogenic variants are typically rare (<1% frequency)",
                )

            # Common benign variants should have higher frequencies
            if (
                "benign" in clinical_lower
                and max_freq < VariantValidationRules.RARE_VARIANT_THRESHOLD
            ):
                return (
                    False,
                    f"Benign variant with very low frequency ({max_freq:.6f})",
                    "Common benign variants typically have higher frequencies",
                )

            return True, "", None

        return ValidationRule(
            field="frequency_clinical_consistency",
            rule="frequency_clinical_consistency",
            validator=rule,
            severity=ValidationSeverity.INFO,
            level="STRICT",
        )

    @staticmethod
    def validate_functional_impact_annotations(
        annotations: Dict[str, Any],
    ) -> ValidationRule:
        """Validate functional impact annotations."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None  # Optional field

            issues = []

            # Check prediction tools consistency
            prediction_tools = value.get("prediction_tools", {})
            if prediction_tools:
                # Common prediction tools and their score ranges
                tool_ranges = {
                    "sift": (0.0, 1.0),  # SIFT: 0-1, lower = more damaging
                    "polyphen2": (0.0, 1.0),  # PolyPhen-2: 0-1, higher = more damaging
                    "mutationtaster": (
                        0.0,
                        1.0,
                    ),  # MutationTaster: 0-1, higher = more damaging
                    "cadd": (0.0, 50.0),  # CADD: 0-50+, higher = more damaging
                    "revel": (0.0, 1.0),  # REVEL: 0-1, higher = more damaging
                }

                for tool, score in prediction_tools.items():
                    tool_lower = tool.lower()
                    if tool_lower in tool_ranges:
                        min_val, max_val = tool_ranges[tool_lower]
                        if not isinstance(score, (int, float)):
                            issues.append(
                                f"{tool} score must be numeric: {type(score)}"
                            )
                        elif not (min_val <= score <= max_val):
                            issues.append(
                                f"{tool} score {score} out of expected range [{min_val}, {max_val}]"
                            )

            # Check conservation scores
            conservation = value.get("conservation_score")
            if conservation is not None:
                if not isinstance(conservation, (int, float)):
                    issues.append("Conservation score must be numeric")
                elif not (0.0 <= conservation <= 1.0):
                    issues.append(
                        f"Conservation score out of range [0,1]: {conservation}"
                    )

            # Check functional categories
            functional_class = value.get("functional_class")
            if functional_class:
                valid_classes = {
                    "missense",
                    "nonsense",
                    "frameshift",
                    "splice_site",
                    "synonymous",
                    "inframe_deletion",
                    "inframe_insertion",
                    "start_lost",
                    "stop_lost",
                    "initiator_codon_variant",
                }
                if functional_class.lower() not in valid_classes:
                    issues.append(f"Unknown functional class: {functional_class}")

            if issues:
                return (
                    False,
                    "Functional impact issues: " + "; ".join(issues),
                    "Review functional annotations",
                )

            return True, "", None

        return ValidationRule(
            field="functional_impact",
            rule="functional_impact",
            validator=rule,
            severity=ValidationSeverity.WARNING,
            level="STANDARD",
        )

    @staticmethod
    def validate_variant_coordinates_vs_gene(
        coordinates: Dict[str, Any], gene_info: Dict[str, Any]
    ) -> ValidationRule:
        """Validate variant coordinates against associated gene."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None

            var_coords = value.get("variant_coordinates", {})
            gene_coords = value.get("gene_coordinates", {})

            if not var_coords or not gene_coords:
                return True, "", None  # Cannot validate without both

            var_chrom = var_coords.get("chromosome")
            var_pos = var_coords.get("position")
            gene_chrom = gene_coords.get("chromosome")
            gene_start = gene_coords.get("start_position")
            gene_end = gene_coords.get("end_position")

            if var_chrom and gene_chrom and var_chrom != gene_chrom:
                return (
                    False,
                    f"Variant chromosome ({var_chrom}) doesn't match gene chromosome ({gene_chrom})",
                    "Check variant-gene association",
                )

            if all([var_pos, gene_start, gene_end]):
                if not (gene_start <= var_pos <= gene_end):
                    # Calculate distance from gene
                    if var_pos < gene_start:
                        distance = gene_start - var_pos
                        region = "upstream"
                    else:
                        distance = var_pos - gene_end
                        region = "downstream"

                    # Flag if too far from gene (more than 100kb)
                    if distance > 100_000:
                        return (
                            False,
                            f"Variant {distance:,} bp {region} from gene",
                            "Verify variant-gene association",
                        )

            return True, "", None

        return ValidationRule(
            field="variant_gene_coordinates",
            rule="variant_gene_coordinates",
            validator=rule,
            severity=ValidationSeverity.WARNING,
            level="STRICT",
        )

    @staticmethod
    def validate_inheritance_pattern_consistency(
        inheritance: str, zygosity_info: Dict[str, Any]
    ) -> ValidationRule:
        """Validate inheritance pattern consistency with zygosity."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None

            inheritance = value.get("inheritance_pattern", "")
            zygosity = value.get("zygosity", "")

            if not inheritance or not zygosity:
                return True, "", None

            inheritance_lower = inheritance.lower()
            zygosity_lower = zygosity.lower()

            # Check for consistency issues
            if "autosomal dominant" in inheritance_lower:
                if "homozygous" in zygosity_lower:
                    return (
                        False,
                        "Autosomal dominant inheritance with homozygous genotype",
                        "Autosomal dominant typically shows heterozygous genotypes",
                    )

            if "x_linked" in inheritance_lower and zygosity_lower == "homozygous":
                # For X-linked in females, homozygous might be possible
                # But this is complex - simplified check
                pass

            # Check for compound heterozygous in recessive diseases
            if "autosomal recessive" in inheritance_lower:
                if zygosity_lower not in [
                    "compound_heterozygous",
                    "homozygous",
                    "heterozygous",
                ]:
                    return (
                        False,
                        "Autosomal recessive with unexpected zygosity",
                        "Recessive diseases typically show compound heterozygous or homozygous genotypes",
                    )

            return True, "", None

        return ValidationRule(
            field="inheritance_zygosity_consistency",
            rule="inheritance_zygosity_consistency",
            validator=rule,
            severity=ValidationSeverity.INFO,
            level="STRICT",
        )

    @classmethod
    def get_all_rules(cls) -> List[ValidationRule]:
        """Get all variant validation rules."""
        rules = []

        # HGVS notation rules for each type
        for notation_type in ["c", "p", "g", "n", "r"]:
            rules.append(cls.validate_hgvs_notation_comprehensive("", notation_type))

        # Other rules
        rules.extend(
            [
                cls.validate_clinical_significance_comprehensive(""),
                cls.validate_population_frequencies({}),
                cls.validate_allele_frequencies_vs_clinical_sig({}, ""),
                cls.validate_functional_impact_annotations({}),
                cls.validate_variant_coordinates_vs_gene({}, {}),
                cls.validate_inheritance_pattern_consistency("", {}),
            ]
        )

        return rules

    @classmethod
    def validate_variant_comprehensively(
        cls, variant_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Run comprehensive validation on variant data.

        Returns list of validation issues found.
        """
        issues = []

        for rule in cls.get_all_rules():
            field_value = variant_data.get(rule.field)

            # Apply rule-specific validation logic
            if rule.rule.startswith("hgvs_") and rule.rule.endswith("_comprehensive"):
                notation_type = rule.rule.split("_")[1]
                hgvs_notations = variant_data.get("hgvs_notations", {})
                notation_value = hgvs_notations.get(notation_type)
                is_valid, message, suggestion = rule.validator(notation_value)
            elif rule.rule == "clinical_significance_comprehensive":
                is_valid, message, suggestion = rule.validator(field_value)
            elif rule.rule == "population_frequencies":
                is_valid, message, suggestion = rule.validator(field_value or {})
            elif rule.rule == "frequency_clinical_consistency":
                combined_data = {
                    "frequencies": variant_data.get("population_frequencies", {}),
                    "clinical_significance": variant_data.get(
                        "clinical_significance", ""
                    ),
                }
                is_valid, message, suggestion = rule.validator(combined_data)
            elif rule.rule == "functional_impact":
                is_valid, message, suggestion = rule.validator(field_value or {})
            elif rule.rule == "variant_gene_coordinates":
                combined_data = {
                    "variant_coordinates": {
                        "chromosome": variant_data.get("chromosome"),
                        "position": variant_data.get("start_position"),
                    },
                    "gene_coordinates": variant_data.get("gene_coordinates", {}),
                }
                is_valid, message, suggestion = rule.validator(combined_data)
            elif rule.rule == "inheritance_zygosity_consistency":
                combined_data = {
                    "inheritance_pattern": variant_data.get("inheritance_pattern"),
                    "zygosity": variant_data.get("zygosity"),
                }
                is_valid, message, suggestion = rule.validator(combined_data)
            else:
                continue

            if not is_valid:
                issues.append(
                    {
                        "field": rule.field,
                        "rule": rule.rule,
                        "severity": rule.severity.value,
                        "message": message,
                        "suggestion": suggestion,
                    }
                )

        return issues
