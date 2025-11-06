"""
Validation helpers for relationships between genes, variants, and phenotypes.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .base_rules import (
    ValidationLevel,
    ValidationOutcome,
    ValidationRule,
    ValidationSeverity,
)

IssueDict = dict[str, Any]


class RelationshipValidationRules:
    """Validation utilities for cross-entity relationships."""

    @staticmethod
    def validate_genotype_phenotype_plausibility(
        _gene: Any,
        _variant: Any,
        _phenotype: Any,
        field: str = "relationship",
    ) -> ValidationRule:
        def validator(value: Any) -> ValidationOutcome:
            if not isinstance(value, dict):
                return (
                    False,
                    "Relationship payload must be a mapping",
                    "Provide relationship details as a dictionary",
                )

            gene = value.get("gene", {})
            variant = value.get("variant", {})
            phenotype = value.get("phenotype", {})

            if (
                not isinstance(gene, dict)
                or not isinstance(variant, dict)
                or not isinstance(phenotype, dict)
            ):
                return (
                    False,
                    "Relationship must include gene, variant and phenotype mappings",
                    "Embed dictionaries for each entity within the relationship payload",
                )

            return True, "", None

        return ValidationRule(
            field=field,
            rule="genotype_phenotype_plausibility",
            validator=validator,
            severity=ValidationSeverity.WARNING,
            level=ValidationLevel.STANDARD,
        )

    @staticmethod
    def validate_evidence_strength_and_consistency(
        _placeholder: Any,
        _confidence_threshold: float | None = None,
        _evidence_level: str | None = None,
        field: str = "evidence",
    ) -> ValidationRule:
        def validator(value: Any) -> ValidationOutcome:
            valid = True
            message = ""
            suggestion: str | None = None

            if value in (None, {}):
                valid = False
                message = "Evidence is required to support the relationship"
                suggestion = "Provide at least one evidence record"
            elif not isinstance(value, dict):
                valid = False
                message = "Evidence payload must be a mapping"
                suggestion = "Provide evidence information as a dictionary"
            else:
                sources = value.get("evidence_sources", [])
                if valid and (
                    not isinstance(sources, list)
                    or not all(isinstance(source, str) for source in sources)
                ):
                    valid = False
                    message = "Evidence sources must be provided as a list of strings"
                    suggestion = "Provide textual evidence sources"
                elif valid and len(sources) == 0:
                    valid = False
                    message = "At least one evidence source is required"
                    suggestion = "Include literature or database sources supporting the relationship"

                confidence = value.get("confidence_score")
                if (
                    valid
                    and confidence is not None
                    and (
                        not isinstance(confidence, (int, float))
                        or not 0 <= float(confidence) <= 1
                    )
                ):
                    valid = False
                    message = "Confidence score must be between 0 and 1"
                    suggestion = "Provide a normalised confidence score"

                level = value.get("evidence_level")
                if valid and level is not None and not isinstance(level, str):
                    valid = False
                    message = "Evidence level must be a string"
                    suggestion = "Provide a descriptive evidence level (e.g. reviewed, predicted)"

            return valid, message, suggestion

        return ValidationRule(
            field=field,
            rule="evidence_strength",
            validator=validator,
            severity=ValidationSeverity.WARNING,
            level=ValidationLevel.LAX,
        )

    @staticmethod
    def validate_statistical_significance(
        _placeholder: Any,
        _minimum_sample_size: int | None = None,
        _minimum_effect_size: float | None = None,
        _confidence_interval_bounds: tuple[float, float] | None = None,
        field: str = "statistics",
    ) -> ValidationRule:
        def validator(value: Any) -> ValidationOutcome:
            if value is None:
                return True, "", None

            valid = True
            message = ""
            suggestion: str | None = None

            if not isinstance(value, dict):
                valid = False
                message = "Statistical metrics must be a mapping"
                suggestion = "Provide statistical data as a dictionary"
            else:
                p_value = value.get("p_value")
                if (
                    valid
                    and p_value is not None
                    and (
                        not isinstance(p_value, (int, float))
                        or not 0 <= float(p_value) <= 1
                    )
                ):
                    valid = False
                    message = "p-value must be between 0 and 1"
                    suggestion = "Provide a valid p-value"

                sample_size = value.get("sample_size")
                if (
                    valid
                    and sample_size is not None
                    and (not isinstance(sample_size, int) or sample_size < 10)
                ):
                    valid = False
                    message = "Sample size must be an integer of at least 10"
                    suggestion = (
                        "Provide the number of observations supporting the relationship"
                    )

                effect_size = value.get("effect_size")
                if (
                    valid
                    and effect_size is not None
                    and not isinstance(
                        effect_size,
                        (int, float),
                    )
                ):
                    valid = False
                    message = "Effect size must be numeric"
                    suggestion = "Provide a numeric effect size estimate"

                ci = value.get("confidence_interval")
                if valid and ci is not None:
                    if (
                        not isinstance(ci, (tuple, list))
                        or len(ci) != 2
                        or not all(isinstance(bound, (int, float)) for bound in ci)
                    ):
                        valid = False
                        message = (
                            "Confidence interval must be a two-element numeric tuple"
                        )
                        suggestion = "Provide (lower, upper) confidence interval bounds"
                    else:
                        lower, upper = float(ci[0]), float(ci[1])
                        if lower > upper:
                            valid = False
                            message = (
                                "Confidence interval lower bound exceeds upper bound"
                            )
                            suggestion = (
                                "Ensure the interval is ordered as (lower, upper)"
                            )

            return valid, message, suggestion

        return ValidationRule(
            field=field,
            rule="statistical_significance",
            validator=validator,
            severity=ValidationSeverity.INFO,
            level=ValidationLevel.STANDARD,
        )

    # ------------------------------------------------------------------ #
    # Aggregate helper
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_all_rules() -> Iterable[ValidationRule]:
        return (
            RelationshipValidationRules.validate_genotype_phenotype_plausibility(
                {},
                {},
                {},
            ),
            RelationshipValidationRules.validate_evidence_strength_and_consistency([]),
            RelationshipValidationRules.validate_statistical_significance({}),
        )

    @staticmethod
    def validate_relationship_comprehensively(
        relationship: dict[str, Any],
    ) -> list[IssueDict]:
        issues: list[IssueDict] = []

        for rule in RelationshipValidationRules.get_all_rules():
            value = (
                relationship
                if rule.field == "relationship"
                else relationship.get(rule.field)
            )
            is_valid, message, suggestion = rule.validator(value)
            if not is_valid:
                issues.append(
                    {
                        "field": rule.field,
                        "rule": rule.rule,
                        "message": message,
                        "suggestion": suggestion,
                        "severity": rule.severity.name.lower(),
                    },
                )

        return issues


__all__ = ["RelationshipValidationRules"]
