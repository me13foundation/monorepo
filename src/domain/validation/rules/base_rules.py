"""
Core validation helpers used across the validation rule modules.

This module provides a minimal, strongly-typed foundation for building
validation rules.  It intentionally favours clarity over feature breadth so the
rest of the codebase can rely on predictable behaviour when running under
strict MyPy settings.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol

from src.type_definitions.common import JSONObject, JSONValue


class ValidatorFn(Protocol):
    def __call__(self, value: JSONValue) -> tuple[bool, str, str | None]:
        ...


ValidationOutcome = tuple[bool, str, str | None]


class ValidationLevel(Enum):
    """Levels of validation strictness."""

    LAX = auto()
    STANDARD = auto()
    STRICT = auto()


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    ERROR = auto()
    WARNING = auto()
    INFO = auto()


@dataclass(frozen=True)
class ValidationRule:
    """Configuration describing a validation rule."""

    field: str
    rule: str
    validator: ValidatorFn
    severity: ValidationSeverity
    level: ValidationLevel


@dataclass
class ValidationIssue:
    """A single validation issue discovered for an entity."""

    field: str
    value: JSONValue
    rule: str
    message: str
    severity: ValidationSeverity
    suggestion: str | None = None

    def __getitem__(
        self,
        key: str,
    ) -> JSONValue | str | ValidationSeverity | None:
        if key == "field":
            return self.field
        if key == "value":
            return self.value
        if key == "rule":
            return self.rule
        if key == "message":
            return self.message
        if key == "severity":
            return self.severity
        if key == "suggestion":
            return self.suggestion
        message = f"Unknown validation issue attribute: {key}"
        raise KeyError(message)

    def get(
        self,
        key: str,
        default: JSONValue | str | None = None,
    ) -> JSONValue | str | ValidationSeverity | None:
        try:
            return self[key]
        except KeyError:
            return default


@dataclass
class ValidationResult:
    """Collection of validation issues with a derived quality score."""

    is_valid: bool
    issues: list[ValidationIssue]
    score: float = 0.0


class DataQualityValidator:
    """Simple rule-based validator for transformed entities."""

    def __init__(self, level: ValidationLevel = ValidationLevel.STANDARD):
        self.level = level
        self._rules: dict[str, list[ValidationRule]] = self._build_rules()

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #

    def validate_entity(
        self,
        entity_type: str,
        payload: JSONObject,
    ) -> ValidationResult:
        """Validate a single entity payload and return the aggregated result."""

        issues: list[ValidationIssue] = []

        for rule in self._rules.get(entity_type, []):
            if not self._rule_is_applicable(rule):
                continue

            value: JSONValue = payload.get(rule.field)
            is_valid, message, suggestion = rule.validator(value)

            if not is_valid:
                issues.append(
                    ValidationIssue(
                        field=rule.field,
                        value=value,
                        rule=rule.rule,
                        message=message,
                        severity=rule.severity,
                        suggestion=suggestion,
                    ),
                )

        score = self._calculate_quality_score(issues)
        is_valid = not any(
            issue.severity is ValidationSeverity.ERROR for issue in issues
        )

        return ValidationResult(is_valid=is_valid, issues=issues, score=score)

    def validate_batch(
        self,
        entity_type: str,
        entities: Iterable[JSONObject],
    ) -> list[ValidationResult]:
        """Validate a collection of entities."""

        return [self.validate_entity(entity_type, entity) for entity in entities]

    # --------------------------------------------------------------------- #
    # Rule construction helpers
    # --------------------------------------------------------------------- #

    def _build_rules(self) -> dict[str, list[ValidationRule]]:
        """Construct the validation rules we support."""

        return {
            "gene": [
                ValidationRule(
                    field="symbol",
                    rule="gene_symbol_format",
                    validator=self._validate_gene_symbol,
                    severity=ValidationSeverity.ERROR,
                    level=ValidationLevel.STANDARD,
                ),
                ValidationRule(
                    field="confidence_score",
                    rule="confidence_score_range",
                    validator=lambda value: self._validate_numeric_range(
                        value,
                        0.0,
                        1.0,
                    ),
                    severity=ValidationSeverity.ERROR,
                    level=ValidationLevel.LAX,
                ),
            ],
            "variant": [
                ValidationRule(
                    field="chromosome",
                    rule="chromosome_format",
                    validator=self._validate_chromosome,
                    severity=ValidationSeverity.ERROR,
                    level=ValidationLevel.STANDARD,
                ),
                ValidationRule(
                    field="position",
                    rule="position_range",
                    validator=lambda value: self._validate_integer_range(
                        value,
                        0,
                        1_000_000_000,
                    ),
                    severity=ValidationSeverity.ERROR,
                    level=ValidationLevel.STANDARD,
                ),
                ValidationRule(
                    field="reference_allele",
                    rule="allele_required",
                    validator=self._validate_allele,
                    severity=ValidationSeverity.ERROR,
                    level=ValidationLevel.STANDARD,
                ),
                ValidationRule(
                    field="alternate_allele",
                    rule="allele_required",
                    validator=self._validate_allele,
                    severity=ValidationSeverity.ERROR,
                    level=ValidationLevel.STANDARD,
                ),
            ],
            "publication": [
                ValidationRule(
                    field="pubmed_id",
                    rule="pubmed_id_format",
                    validator=self._validate_pubmed_id,
                    severity=ValidationSeverity.ERROR,
                    level=ValidationLevel.STANDARD,
                ),
                ValidationRule(
                    field="title",
                    rule="title_length",
                    validator=lambda value: self._validate_string_length(
                        value,
                        min_len=5,
                        max_len=512,
                    ),
                    severity=ValidationSeverity.ERROR,
                    level=ValidationLevel.STANDARD,
                ),
                ValidationRule(
                    field="authors",
                    rule="author_list",
                    validator=self._validate_author_list,
                    severity=ValidationSeverity.WARNING,
                    level=ValidationLevel.LAX,
                ),
            ],
        }

    # --------------------------------------------------------------------- #
    # Individual rule validators
    # --------------------------------------------------------------------- #

    @staticmethod
    def _validate_gene_symbol(value: JSONValue) -> ValidationOutcome:
        if not isinstance(value, str) or not value:
            return False, "Gene symbol is required", "Provide a valid HGNC gene symbol"

        if not re.fullmatch(r"[A-Z][A-Z0-9_-]{1,19}", value):
            return (
                False,
                f"Invalid gene symbol format: {value}",
                "Symbols must be 2-20 characters, uppercase A-Z, digits, '_' or '-'",
            )

        return True, "", None

    @staticmethod
    def _validate_chromosome(value: JSONValue) -> ValidationOutcome:
        if not isinstance(value, str):
            return False, "Chromosome must be a string", "Provide chromosome as text"

        valid = {str(i) for i in range(1, 23)} | {"X", "Y", "MT", "M"}
        if value.upper() not in valid:
            return (
                False,
                f"Invalid chromosome value: {value}",
                "Expected 1-22, X, Y, M or MT",
            )

        return True, "", None

    @staticmethod
    def _validate_numeric_range(
        value: JSONValue,
        minimum: float,
        maximum: float,
    ) -> ValidationOutcome:
        if not isinstance(value, (int, float)):
            return (
                False,
                "Value must be numeric",
                f"Provide a value between {minimum} and {maximum}",
            )

        numeric_value = float(value)
        if not (minimum <= numeric_value <= maximum):
            return (
                False,
                f"Value {numeric_value} out of range [{minimum}, {maximum}]",
                f"Provide a value between {minimum} and {maximum}",
            )

        return True, "", None

    @staticmethod
    def _validate_integer_range(
        value: JSONValue,
        minimum: int,
        maximum: int,
    ) -> ValidationOutcome:
        if not isinstance(value, int):
            return (
                False,
                "Value must be an integer",
                f"Provide an integer between {minimum} and {maximum}",
            )

        if not (minimum <= value <= maximum):
            return (
                False,
                f"Value {value} out of range [{minimum}, {maximum}]",
                f"Provide an integer between {minimum} and {maximum}",
            )

        return True, "", None

    @staticmethod
    def _validate_allele(value: JSONValue) -> ValidationOutcome:
        if not isinstance(value, str) or not value:
            return (
                False,
                "Allele must be a non-empty string",
                "Provide the allele sequence",
            )
        if not re.fullmatch(r"[ACGTN]+", value.upper()):
            return (
                False,
                f"Invalid allele sequence: {value}",
                "Alleles should contain only A, C, G, T, or N",
            )
        return True, "", None

    @staticmethod
    def _validate_pubmed_id(value: JSONValue) -> ValidationOutcome:
        if value is None:
            return False, "PubMed ID is required", "Provide the PubMed identifier"
        if isinstance(value, int):
            numeric_value = value
        elif isinstance(value, str) and value.isdigit():
            numeric_value = int(value)
        else:
            return (
                False,
                f"Invalid PubMed ID format: {value}",
                "PubMed IDs should contain only digits",
            )

        if numeric_value < 1_000 or numeric_value > 99_999_999:
            return (
                False,
                f"PubMed ID {numeric_value} is out of the expected range",
                "Verify the identifier with the source publication",
            )

        return True, "", None

    @staticmethod
    def _validate_string_length(
        value: JSONValue,
        *,
        min_len: int = 0,
        max_len: int = 1024,
    ) -> ValidationOutcome:
        if value is None:
            return (
                (min_len == 0),
                "Value is required",
                f"Provide a value with at least {min_len} characters",
            )
        if not isinstance(value, str):
            return False, "Value must be a string", "Provide textual content"

        length = len(value.strip())
        if length < min_len:
            return (
                False,
                f"Value is too short ({length} < {min_len})",
                f"Provide at least {min_len} characters",
            )
        if length > max_len:
            return (
                False,
                f"Value is too long ({length} > {max_len})",
                f"Limit to at most {max_len} characters",
            )

        return True, "", None

    @staticmethod
    def _validate_author_list(value: JSONValue) -> ValidationOutcome:
        if value is None:
            return True, "", None  # optional field

        if not isinstance(value, list) or not all(
            isinstance(item, str) and item for item in value
        ):
            return (
                False,
                "Author list must contain non-empty strings",
                "Provide authors as a list of names",
            )
        return True, "", None

    # --------------------------------------------------------------------- #
    # Utility helpers
    # --------------------------------------------------------------------- #

    def _rule_is_applicable(self, rule: ValidationRule) -> bool:
        if self.level is ValidationLevel.STRICT:
            return True
        if self.level is ValidationLevel.STANDARD:
            return rule.level in (ValidationLevel.STANDARD, ValidationLevel.LAX)
        return rule.level is ValidationLevel.LAX

    @staticmethod
    def _calculate_quality_score(issues: list[ValidationIssue]) -> float:
        if not issues:
            return 1.0

        penalty = 0.0
        for issue in issues:
            if issue.severity is ValidationSeverity.ERROR:
                penalty += 0.5
            elif issue.severity is ValidationSeverity.WARNING:
                penalty += 0.25
            else:
                penalty += 0.1

        return max(0.0, 1.0 - min(penalty, 1.0))

    @staticmethod
    def calculate_quality_score(issues: list[ValidationIssue]) -> float:
        """Public wrapper for quality-score calculation."""
        return DataQualityValidator._calculate_quality_score(issues)


class ValidationRuleEngine:
    """Facade that coordinates rule validation across entity types."""

    def __init__(self, level: ValidationLevel = ValidationLevel.STANDARD):
        self.level = level
        self.rule_registry: dict[str, list[ValidationRule]] = self._load_default_rules()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def get_available_rules(
        self,
        entity_type: str | None = None,
    ) -> dict[str, list[ValidationRule]]:
        if entity_type is None:
            return {key: list(value) for key, value in self.rule_registry.items()}
        return {entity_type: list(self.rule_registry.get(entity_type, []))}

    def validate_entity(
        self,
        entity_type: str,
        entity_data: JSONObject,
        rule_names: Sequence[str] | None = None,
    ) -> ValidationResult:
        rules = self._select_rules(entity_type, rule_names)

        if not rules:
            issue = ValidationIssue(
                field="entity_type",
                value=entity_type,
                rule="unknown_entity_type",
                message=f"Unknown entity type: {entity_type}",
                severity=ValidationSeverity.ERROR,
            )
            return ValidationResult(is_valid=False, issues=[issue], score=0.0)

        issues: list[ValidationIssue] = []
        for rule in rules:
            if not self._rule_is_applicable(rule):
                continue

            value: JSONValue = (
                entity_data
                if rule.field == "relationship"
                else entity_data.get(rule.field)
            )
            is_valid, message, suggestion = rule.validator(value)
            if not is_valid:
                issues.append(
                    ValidationIssue(
                        field=rule.field,
                        value=value,
                        rule=rule.rule,
                        message=message,
                        severity=rule.severity,
                        suggestion=suggestion,
                    ),
                )

        score = DataQualityValidator.calculate_quality_score(issues)
        is_valid = not any(
            issue.severity is ValidationSeverity.ERROR for issue in issues
        )
        return ValidationResult(is_valid=is_valid, issues=issues, score=score)

    def validate_batch(
        self,
        entity_type: str,
        entities: Iterable[JSONObject],
        rule_names: Sequence[str] | None = None,
    ) -> list[ValidationResult]:
        return [
            self.validate_entity(entity_type, entity, rule_names) for entity in entities
        ]

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _load_default_rules(self) -> dict[str, list[ValidationRule]]:
        from .gene_rules import GeneValidationRules
        from .phenotype_rules import PhenotypeValidationRules
        from .publication_rules import PublicationValidationRules
        from .relationship_rules import RelationshipValidationRules
        from .variant_rules import VariantValidationRules

        return {
            "gene": list(GeneValidationRules.get_all_rules()),
            "variant": list(VariantValidationRules.get_all_rules()),
            "phenotype": list(PhenotypeValidationRules.get_all_rules()),
            "publication": [
                PublicationValidationRules.validate_doi_format_and_accessibility(""),
                PublicationValidationRules.validate_author_information([]),
            ],
            "relationship": list(RelationshipValidationRules.get_all_rules()),
        }

    def _select_rules(
        self,
        entity_type: str,
        rule_names: Sequence[str] | None,
    ) -> list[ValidationRule]:
        rules = self.rule_registry.get(entity_type, [])
        if not rule_names:
            return list(rules)

        selected = [rule for rule in rules if rule.rule in rule_names]
        return selected or list(rules)

    def _rule_is_applicable(self, rule: ValidationRule) -> bool:
        if self.level is ValidationLevel.STRICT:
            return True
        if self.level is ValidationLevel.STANDARD:
            return rule.level in (ValidationLevel.STANDARD, ValidationLevel.LAX)
        return rule.level is ValidationLevel.LAX


__all__ = [
    "DataQualityValidator",
    "ValidationIssue",
    "ValidationLevel",
    "ValidationResult",
    "ValidationRule",
    "ValidationRuleEngine",
    "ValidationSeverity",
]
