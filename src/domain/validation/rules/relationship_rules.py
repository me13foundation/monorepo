"""
Advanced validation rules for entity relationships.

Implements business logic validation for relationships between
genes, variants, phenotypes, and publications including:
- Biological plausibility of genotype-phenotype associations
- Statistical significance of associations
- Temporal consistency of evidence
- Cross-reference validation
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from .base_rules import ValidationRule, ValidationSeverity


@dataclass
class RelationshipValidationRules:
    """
    Comprehensive validation rules for entity relationships.

    Validates relationships between biomedical entities for biological
    accuracy, statistical significance, and scientific validity.
    """

    # Confidence score thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.8
    MEDIUM_CONFIDENCE_THRESHOLD = 0.5

    # Evidence level classifications
    EVIDENCE_LEVELS = {
        "reviewed": 1.0,
        "validated": 0.9,
        "experimental": 0.8,
        "computational": 0.6,
        "predicted": 0.4,
        "uncertain": 0.2,
    }

    @staticmethod
    def validate_genotype_phenotype_plausibility(
        gene_info: Dict[str, Any],
        variant_info: Dict[str, Any],
        phenotype_info: Dict[str, Any],
    ) -> ValidationRule:
        """Validate biological plausibility of genotype-phenotype associations."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None

            gene = value.get("gene", {})
            variant = value.get("variant", {})
            phenotype = value.get("phenotype", {})

            issues = []

            # Check gene function vs phenotype
            gene_function = gene.get("function", "").lower()
            phenotype_name = phenotype.get("name", "").lower()

            # Basic biological plausibility checks
            if "kinase" in gene_function and "cancer" in phenotype_name:
                # Kinase genes are often associated with cancer - plausible
                pass
            elif "transcription" in gene_function and "developmental" in phenotype_name:
                # Transcription factors often affect development - plausible
                pass
            elif "structural" in gene_function and "skeletal" in phenotype_name:
                # Structural genes often affect skeletal phenotypes - plausible
                pass

            # Check for biologically implausible associations
            if "housekeeping" in gene_function and "specific" in phenotype_name:
                issues.append(
                    "Housekeeping gene associated with highly specific phenotype"
                )

            # Check variant type vs expected phenotype severity
            variant_type = variant.get("type", "").lower()
            clinical_sig = variant.get("clinical_significance", "").lower()

            if "frameshift" in variant_type and "benign" in clinical_sig:
                issues.append("Frameshift variant classified as benign")

            if "nonsense" in variant_type and "benign" in clinical_sig:
                issues.append("Nonsense variant classified as benign")

            # Check inheritance pattern consistency
            inheritance = phenotype.get("inheritance_pattern", "").lower()

            if "autosomal dominant" in inheritance:
                # AD conditions typically have heterozygous pathogenic variants
                zygosity = variant.get("zygosity", "").lower()
                if zygosity == "homozygous":
                    issues.append(
                        "Autosomal dominant condition with homozygous variant"
                    )

            if issues:
                return (
                    False,
                    "Genotype-phenotype plausibility issues: " + "; ".join(issues),
                    "Review biological plausibility of association",
                )

            return True, "", None

        return ValidationRule(
            field="genotype_phenotype_plausibility",
            rule="genotype_phenotype_plausibility",
            validator=rule,
            severity=ValidationSeverity.WARNING,
            level="STRICT",
        )

    @staticmethod
    def validate_evidence_strength_and_consistency(
        evidence_sources: List[str], confidence_score: float, evidence_level: str
    ) -> ValidationRule:
        """Validate evidence strength and consistency."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None

            sources = value.get("evidence_sources", [])
            confidence = value.get("confidence_score", 0.0)
            level = value.get("evidence_level", "")

            issues = []

            # Check confidence score consistency with evidence sources
            if confidence > RelationshipValidationRules.HIGH_CONFIDENCE_THRESHOLD:
                if len(sources) < 2:
                    issues.append(
                        "High confidence score with insufficient evidence sources"
                    )
            elif confidence > RelationshipValidationRules.MEDIUM_CONFIDENCE_THRESHOLD:
                if len(sources) < 1:
                    issues.append("Medium confidence score with no evidence sources")

            # Check evidence level consistency with confidence
            expected_confidence = RelationshipValidationRules.EVIDENCE_LEVELS.get(
                level.lower(), 0.5
            )
            confidence_diff = abs(confidence - expected_confidence)

            if confidence_diff > 0.3:  # Significant discrepancy
                issues.append(
                    f"Confidence score ({confidence}) doesn't match evidence level '{level}' (expected ~{expected_confidence})"
                )

            # Check for high-quality evidence sources
            high_quality_sources = ["clinvar", "omim", "pubmed", "genereviews"]
            has_high_quality = any(
                any(hq in source.lower() for hq in high_quality_sources)
                for source in sources
            )

            if confidence > 0.7 and not has_high_quality:
                issues.append(
                    "High confidence score without high-quality evidence sources"
                )

            if issues:
                return (
                    False,
                    "Evidence strength issues: " + "; ".join(issues),
                    "Review evidence quality and confidence scoring",
                )

            return True, "", None

        return ValidationRule(
            field="evidence_strength",
            rule="evidence_strength_consistency",
            validator=rule,
            severity=ValidationSeverity.WARNING,
            level="STANDARD",
        )

    @staticmethod
    def validate_temporal_consistency(
        relationship_date: datetime,
        evidence_dates: List[datetime],
        publication_dates: List[datetime],
    ) -> ValidationRule:
        """Validate temporal consistency of relationship evidence."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None

            rel_date = value.get("relationship_date")
            evidence_dates = value.get("evidence_dates", [])
            pub_dates = value.get("publication_dates", [])

            if not rel_date and not evidence_dates and not pub_dates:
                return True, "", None  # No temporal data to validate

            issues = []

            # Check that evidence dates are not in the future
            current_year = datetime.now().year
            future_threshold = current_year + 2  # Allow some future dates for preprints

            for date_list, date_type in [
                (evidence_dates, "evidence"),
                (pub_dates, "publication"),
            ]:
                for date in date_list:
                    if isinstance(date, datetime) and date.year > future_threshold:
                        issues.append(
                            f"{date_type.capitalize()} date in far future: {date.year}"
                        )

            # Check that relationship date is not before earliest evidence
            if rel_date and evidence_dates:
                earliest_evidence = min(evidence_dates)
                if rel_date < earliest_evidence:
                    issues.append(
                        f"Relationship date ({rel_date}) before earliest evidence ({earliest_evidence})"
                    )

            # Check publication timeline consistency
            if pub_dates and len(pub_dates) > 1:
                sorted_dates = sorted(pub_dates)
                # Check for publications out of chronological order (within reason)
                for i in range(1, len(sorted_dates)):
                    if (
                        sorted_dates[i] - sorted_dates[i - 1]
                    ).days < -30:  # 30 days tolerance
                        issues.append("Publications appear in non-chronological order")

            if issues:
                return (
                    False,
                    "Temporal consistency issues: " + "; ".join(issues),
                    "Review dates and timelines",
                )

            return True, "", None

        return ValidationRule(
            field="temporal_consistency",
            rule="temporal_consistency",
            validator=rule,
            severity=ValidationSeverity.INFO,
            level="STRICT",
        )

    @staticmethod
    def validate_population_genetics_consistency(
        allele_frequency: float, clinical_significance: str, population_size: int
    ) -> ValidationRule:
        """Validate population genetics consistency."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None

            af = value.get("allele_frequency")
            clinical_sig = value.get("clinical_significance", "").lower()
            pop_size = value.get("population_size", 0)

            if af is None:
                return True, "", None

            issues = []

            # Pathogenic variants should generally be rare
            if "pathogenic" in clinical_sig and af > 0.01:  # 1%
                if pop_size > 1000:  # Only flag for larger populations
                    issues.append(
                        f"Pathogenic variant with high frequency ({af:.4f}) in population of {pop_size}"
                    )

            # Very rare variants (<0.001) with benign classification
            if af < 0.001 and "benign" in clinical_sig:
                issues.append(f"Very rare variant ({af:.6f}) classified as benign")

            # Check Hardy-Weinberg equilibrium approximation
            if af > 0 and af < 1:
                # For biallelic variants, heterozygous frequency should be ~2pq
                # This is a simplified check
                if af > 0.49:  # Very common variants
                    issues.append(
                        f"Extremely common variant ({af:.4f}) - verify population genetics"
                    )

            if issues:
                return (
                    False,
                    "Population genetics issues: " + "; ".join(issues),
                    "Review allele frequency data",
                )

            return True, "", None

        return ValidationRule(
            field="population_genetics",
            rule="population_genetics_consistency",
            validator=rule,
            severity=ValidationSeverity.INFO,
            level="STRICT",
        )

    @staticmethod
    def validate_cross_database_consistency(
        primary_source: str,
        cross_references: Dict[str, List[str]],
        conflicting_data: Dict[str, Any],
    ) -> ValidationRule:
        """Validate consistency across different databases."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None

            primary = value.get("primary_source", "")
            xrefs = value.get("cross_references", {})
            conflicts = value.get("conflicting_data", {})

            issues = []

            # Check for major conflicts between databases
            if conflicts:
                for conflict_type, conflict_details in conflicts.items():
                    if conflict_type == "clinical_significance":
                        issues.append(
                            f"Conflicting clinical significance across databases: {conflict_details}"
                        )
                    elif conflict_type == "allele_frequency":
                        issues.append(
                            f"Conflicting allele frequencies: {conflict_details}"
                        )
                    elif conflict_type == "inheritance":
                        issues.append(
                            f"Conflicting inheritance patterns: {conflict_details}"
                        )

            # Check cross-reference completeness
            if primary == "clinvar":
                # ClinVar entries should have PubMed references
                pubmed_refs = xrefs.get("PubMed", [])
                if len(pubmed_refs) == 0:
                    issues.append("ClinVar entry missing PubMed references")

            if primary == "omim":
                # OMIM entries should have PubMed references
                pubmed_refs = xrefs.get("PubMed", [])
                if (
                    len(pubmed_refs) < 2
                ):  # OMIM entries typically have multiple references
                    issues.append("OMIM entry has few PubMed references")

            if issues:
                return (
                    False,
                    "Cross-database consistency issues: " + "; ".join(issues),
                    "Review data across different sources",
                )

            return True, "", None

        return ValidationRule(
            field="cross_database_consistency",
            rule="cross_database_consistency",
            validator=rule,
            severity=ValidationSeverity.WARNING,
            level="STRICT",
        )

    @staticmethod
    def validate_statistical_significance(
        p_value: float,
        sample_size: int,
        effect_size: float,
        confidence_interval: Tuple[float, float],
    ) -> ValidationRule:
        """Validate statistical significance of associations."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None

            p_val = value.get("p_value")
            n = value.get("sample_size")
            effect = value.get("effect_size")
            ci = value.get("confidence_interval")

            issues = []

            # Check p-value range
            if p_val is not None:
                if not (0 <= p_val <= 1):
                    issues.append(f"P-value out of range [0,1]: {p_val}")
                elif p_val > 0.05:  # Not statistically significant
                    issues.append(f"P-value not significant: {p_val} > 0.05")

            # Check sample size adequacy
            if n is not None and n < 10:
                issues.append(f"Very small sample size: {n}")

            # Check effect size reasonableness
            if effect is not None:
                if abs(effect) > 10:  # Extremely large effect size
                    issues.append(f"Suspiciously large effect size: {effect}")

            # Check confidence interval
            if ci and isinstance(ci, (list, tuple)) and len(ci) == 2:
                ci_lower, ci_upper = ci
                if ci_lower > ci_upper:
                    issues.append(
                        f"Invalid confidence interval: [{ci_lower}, {ci_upper}]"
                    )
                if effect is not None and (effect < ci_lower or effect > ci_upper):
                    issues.append(
                        f"Effect size {effect} outside confidence interval [{ci_lower}, {ci_upper}]"
                    )

            if issues:
                return (
                    False,
                    "Statistical significance issues: " + "; ".join(issues),
                    "Review statistical evidence",
                )

            return True, "", None

        return ValidationRule(
            field="statistical_significance",
            rule="statistical_significance",
            validator=rule,
            severity=ValidationSeverity.WARNING,
            level="STRICT",
        )

    @classmethod
    def get_all_rules(cls) -> List[ValidationRule]:
        """Get all relationship validation rules."""
        return [
            cls.validate_genotype_phenotype_plausibility({}, {}, {}),
            cls.validate_evidence_strength_and_consistency([], 0.0, ""),
            cls.validate_temporal_consistency(None, [], []),
            cls.validate_population_genetics_consistency(0.0, "", 0),
            cls.validate_cross_database_consistency("", {}, {}),
            cls.validate_statistical_significance(1.0, 0, 0.0, (0.0, 0.0)),
        ]

    @classmethod
    def validate_relationship_comprehensively(
        cls, relationship_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Run comprehensive validation on relationship data.

        Returns list of validation issues found.
        """
        issues = []

        for rule in cls.get_all_rules():
            # Apply rule-specific validation logic
            if rule.rule == "genotype_phenotype_plausibility":
                combined_data = {
                    "gene": relationship_data.get("gene_info", {}),
                    "variant": relationship_data.get("variant_info", {}),
                    "phenotype": relationship_data.get("phenotype_info", {}),
                }
                is_valid, message, suggestion = rule.validator(combined_data)
            elif rule.rule == "evidence_strength_consistency":
                combined_data = {
                    "evidence_sources": relationship_data.get("evidence_sources", []),
                    "confidence_score": relationship_data.get("confidence_score", 0.0),
                    "evidence_level": relationship_data.get("evidence_level", ""),
                }
                is_valid, message, suggestion = rule.validator(combined_data)
            elif rule.rule == "temporal_consistency":
                combined_data = {
                    "relationship_date": relationship_data.get("relationship_date"),
                    "evidence_dates": relationship_data.get("evidence_dates", []),
                    "publication_dates": relationship_data.get("publication_dates", []),
                }
                is_valid, message, suggestion = rule.validator(combined_data)
            elif rule.rule == "population_genetics_consistency":
                combined_data = {
                    "allele_frequency": relationship_data.get("allele_frequency"),
                    "clinical_significance": relationship_data.get(
                        "clinical_significance", ""
                    ),
                    "population_size": relationship_data.get("population_size", 0),
                }
                is_valid, message, suggestion = rule.validator(combined_data)
            elif rule.rule == "cross_database_consistency":
                combined_data = {
                    "primary_source": relationship_data.get("primary_source", ""),
                    "cross_references": relationship_data.get("cross_references", {}),
                    "conflicting_data": relationship_data.get("conflicting_data", {}),
                }
                is_valid, message, suggestion = rule.validator(combined_data)
            elif rule.rule == "statistical_significance":
                combined_data = {
                    "p_value": relationship_data.get("p_value"),
                    "sample_size": relationship_data.get("sample_size"),
                    "effect_size": relationship_data.get("effect_size"),
                    "confidence_interval": relationship_data.get("confidence_interval"),
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
