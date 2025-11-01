"""
Data quality validation service for transformation pipeline.

Provides comprehensive validation rules and quality checks for all
transformed biomedical data entities and relationships.
"""

import re
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class ValidationLevel(Enum):
    """Levels of validation strictness."""

    LAX = "lax"  # Basic validation, allow most data through
    STANDARD = "standard"  # Standard validation with common checks
    STRICT = "strict"  # Strict validation, reject any questionable data


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    ERROR = "error"  # Critical issues that should prevent processing
    WARNING = "warning"  # Issues that should be flagged but allow processing
    INFO = "info"  # Informational notes about data quality


@dataclass
class ValidationIssue:
    """A data validation issue."""

    field: str
    value: Any
    rule: str
    message: str
    severity: ValidationSeverity
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validating a data entity."""

    is_valid: bool
    issues: List[ValidationIssue]
    score: float  # Quality score from 0.0 to 1.0


class DataQualityValidator:
    """
    Comprehensive data quality validator for biomedical entities.

    Applies domain-specific validation rules to ensure data quality
    and consistency across all transformed entities.
    """

    def __init__(self, level: ValidationLevel = ValidationLevel.STANDARD):
        self.level = level
        self.validation_rules = self._build_validation_rules()

    def _build_validation_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build validation rules for different entity types."""
        return {
            "gene": [
                {
                    "field": "symbol",
                    "rule": "gene_symbol_format",
                    "validator": self._validate_gene_symbol,
                    "severity": ValidationSeverity.ERROR,
                    "level": ValidationLevel.STANDARD,
                },
                {
                    "field": "symbol",
                    "rule": "gene_symbol_case",
                    "validator": self._validate_gene_symbol_case,
                    "severity": ValidationSeverity.WARNING,
                    "level": ValidationLevel.STRICT,
                },
                {
                    "field": "confidence_score",
                    "rule": "confidence_range",
                    "validator": lambda x: self._validate_range(x, 0.0, 1.0),
                    "severity": ValidationSeverity.ERROR,
                    "level": ValidationLevel.LAX,
                },
            ],
            "variant": [
                {
                    "field": "chromosome",
                    "rule": "chromosome_format",
                    "validator": self._validate_chromosome,
                    "severity": ValidationSeverity.ERROR,
                    "level": ValidationLevel.STANDARD,
                },
                {
                    "field": "position",
                    "rule": "genomic_position",
                    "validator": self._validate_genomic_position,
                    "severity": ValidationSeverity.ERROR,
                    "level": ValidationLevel.STANDARD,
                },
                {
                    "field": "alleles",
                    "rule": "allele_format",
                    "validator": self._validate_alleles,
                    "severity": ValidationSeverity.WARNING,
                    "level": ValidationLevel.STRICT,
                },
                {
                    "field": "hgvs_notations",
                    "rule": "hgvs_format",
                    "validator": self._validate_hgvs_notations,
                    "severity": ValidationSeverity.WARNING,
                    "level": ValidationLevel.STRICT,
                },
            ],
            "phenotype": [
                {
                    "field": "hpo_id",
                    "rule": "hpo_id_format",
                    "validator": self._validate_hpo_id,
                    "severity": ValidationSeverity.ERROR,
                    "level": ValidationLevel.STANDARD,
                },
                {
                    "field": "name",
                    "rule": "phenotype_name_length",
                    "validator": lambda x: self._validate_length(x, min_len=3),
                    "severity": ValidationSeverity.WARNING,
                    "level": ValidationLevel.STANDARD,
                },
                {
                    "field": "name",
                    "rule": "phenotype_name_case",
                    "validator": self._validate_phenotype_name_case,
                    "severity": ValidationSeverity.INFO,
                    "level": ValidationLevel.STRICT,
                },
            ],
            "publication": [
                {
                    "field": "pubmed_id",
                    "rule": "pubmed_id_format",
                    "validator": self._validate_pubmed_id,
                    "severity": ValidationSeverity.ERROR,
                    "level": ValidationLevel.STANDARD,
                },
                {
                    "field": "doi",
                    "rule": "doi_format",
                    "validator": self._validate_doi,
                    "severity": ValidationSeverity.WARNING,
                    "level": ValidationLevel.STANDARD,
                },
                {
                    "field": "title",
                    "rule": "title_length",
                    "validator": lambda x: self._validate_length(x, min_len=10),
                    "severity": ValidationSeverity.WARNING,
                    "level": ValidationLevel.STANDARD,
                },
                {
                    "field": "authors",
                    "rule": "author_count",
                    "validator": lambda x: self._validate_list_length(x, min_len=1),
                    "severity": ValidationSeverity.WARNING,
                    "level": ValidationLevel.STANDARD,
                },
            ],
            "relationship": [
                {
                    "field": "confidence_score",
                    "rule": "relationship_confidence",
                    "validator": lambda x: self._validate_range(x, 0.0, 1.0),
                    "severity": ValidationSeverity.ERROR,
                    "level": ValidationLevel.LAX,
                },
                {
                    "field": "evidence_sources",
                    "rule": "evidence_sources",
                    "validator": lambda x: self._validate_list_length(x, min_len=1),
                    "severity": ValidationSeverity.WARNING,
                    "level": ValidationLevel.STANDARD,
                },
            ],
        }

    def validate_entity(
        self, entity_type: str, entity_data: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate a single entity.

        Args:
            entity_type: Type of entity ('gene', 'variant', 'phenotype', 'publication')
            entity_data: Entity data dictionary

        Returns:
            ValidationResult with issues and quality score
        """
        issues = []

        # Get applicable rules for this entity type
        rules = self.validation_rules.get(entity_type, [])

        for rule in rules:
            # Check if this rule applies at our validation level
            if self._rule_applies_at_level(rule):
                field_value = entity_data.get(rule["field"])

                # Run validation
                is_valid, message, suggestion = rule["validator"](field_value)

                if not is_valid:
                    issues.append(
                        ValidationIssue(
                            field=rule["field"],
                            value=field_value,
                            rule=rule["rule"],
                            message=message,
                            severity=rule["severity"],
                            suggestion=suggestion,
                        )
                    )

        # Calculate quality score
        score = self._calculate_quality_score(issues)

        return ValidationResult(
            is_valid=len([i for i in issues if i.severity == ValidationSeverity.ERROR])
            == 0,
            issues=issues,
            score=score,
        )

    def validate_relationship(
        self, relationship_data: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate a relationship between entities.

        Args:
            relationship_data: Relationship data dictionary

        Returns:
            ValidationResult with issues and quality score
        """
        return self.validate_entity("relationship", relationship_data)

    def validate_batch(
        self, entity_type: str, entities: List[Dict[str, Any]]
    ) -> List[ValidationResult]:
        """
        Validate a batch of entities.

        Args:
            entity_type: Type of entities
            entities: List of entity data dictionaries

        Returns:
            List of ValidationResult objects
        """
        return [self.validate_entity(entity_type, entity) for entity in entities]

    def _rule_applies_at_level(self, rule: Dict[str, Any]) -> bool:
        """Check if a validation rule applies at the current validation level."""
        rule_level = rule.get("level", ValidationLevel.STANDARD)

        if self.level == ValidationLevel.LAX:
            return rule_level in [ValidationLevel.LAX]
        elif self.level == ValidationLevel.STANDARD:
            return rule_level in [ValidationLevel.LAX, ValidationLevel.STANDARD]
        else:  # STRICT
            return True  # All rules apply in strict mode

    def _calculate_quality_score(self, issues: List[ValidationIssue]) -> float:
        """Calculate quality score based on validation issues."""
        if not issues:
            return 1.0

        # Weight issues by severity
        error_weight = 0.5
        warning_weight = 0.25
        info_weight = 0.1

        total_penalty = 0.0

        for issue in issues:
            if issue.severity == ValidationSeverity.ERROR:
                total_penalty += error_weight
            elif issue.severity == ValidationSeverity.WARNING:
                total_penalty += warning_weight
            else:  # INFO
                total_penalty += info_weight

        # Cap penalty at 1.0
        return max(0.0, 1.0 - min(1.0, total_penalty))

    # Gene validation methods

    def _validate_gene_symbol(
        self, symbol: Optional[str]
    ) -> tuple[bool, str, Optional[str]]:
        """Validate gene symbol format."""
        if not symbol:
            return False, "Gene symbol is required", "Provide a valid gene symbol"

        # Basic format check
        if not re.match(r"^[A-Z][A-Z0-9_-]*$", symbol):
            return (
                False,
                f"Invalid gene symbol format: {symbol}",
                "Gene symbols should start with a letter and contain only letters, numbers, underscores, and hyphens",
            )

        # Length check
        if len(symbol) < 2 or len(symbol) > 20:
            return (
                False,
                f"Gene symbol length invalid: {len(symbol)}",
                "Gene symbols should be 2-20 characters long",
            )

        return True, "", None

    def _validate_gene_symbol_case(
        self, symbol: Optional[str]
    ) -> tuple[bool, str, Optional[str]]:
        """Validate gene symbol case (should be uppercase)."""
        if not symbol:
            return True, "", None  # Skip if no symbol

        if symbol != symbol.upper():
            return (
                False,
                f"Gene symbol should be uppercase: {symbol}",
                f"Use {symbol.upper()} instead",
            )

        return True, "", None

    # Variant validation methods

    def _validate_chromosome(
        self, chromosome: Optional[Union[str, int]]
    ) -> tuple[bool, str, Optional[str]]:
        """Validate chromosome format."""
        if chromosome is None:
            return False, "Chromosome is required", "Provide chromosome information"

        # Convert to string for validation
        chrom_str = str(chromosome)

        # Remove 'chr' prefix if present
        chrom_str = chrom_str.replace("chr", "")

        # Check valid chromosome names
        valid_chroms = [str(i) for i in range(1, 23)] + ["X", "Y", "M", "MT"]

        if chrom_str not in valid_chroms:
            return (
                False,
                f"Invalid chromosome: {chromosome}",
                f"Valid chromosomes: {', '.join(valid_chroms)}",
            )

        return True, "", None

    def _validate_genomic_position(
        self, position: Optional[int]
    ) -> tuple[bool, str, Optional[str]]:
        """Validate genomic position."""
        if position is None:
            return False, "Genomic position is required", "Provide genomic coordinate"

        if position < 0:
            return (
                False,
                f"Invalid negative position: {position}",
                "Genomic positions must be positive",
            )

        # Check for unreasonably large positions (beyond human genome size)
        if position > 3_100_000_000:  # Approximate human genome size
            return (
                False,
                f"Suspiciously large position: {position}",
                "Verify genomic coordinate",
            )

        return True, "", None

    def _validate_alleles(
        self, alleles: Optional[Dict[str, str]]
    ) -> tuple[bool, str, Optional[str]]:
        """Validate allele formats."""
        if not alleles:
            return True, "", None  # Optional field

        ref = alleles.get("reference", alleles.get("ref", ""))
        alt = alleles.get("alternate", alleles.get("alt", ""))

        # Check for valid nucleotide characters
        valid_nucleotides = set("ACGTN")

        if ref and not all(c.upper() in valid_nucleotides for c in ref):
            return (
                False,
                f"Invalid reference allele: {ref}",
                "Reference alleles should contain only A, C, G, T, N",
            )

        if alt and not all(c.upper() in valid_nucleotides for c in alt):
            return (
                False,
                f"Invalid alternate allele: {alt}",
                "Alternate alleles should contain only A, C, G, T, N",
            )

        return True, "", None

    def _validate_hgvs_notations(
        self, hgvs_dict: Optional[Dict[str, str]]
    ) -> tuple[bool, str, Optional[str]]:
        """Validate HGVS notation formats."""
        if not hgvs_dict:
            return True, "", None  # Optional field

        # Basic pattern checks for different HGVS types
        patterns = {
            "c": re.compile(r"^c\.\d+.*$"),
            "p": re.compile(r"^p\.\w+\d+\w+$"),
            "g": re.compile(r"^g\.\d+.*$"),
        }

        for hgvs_type, notation in hgvs_dict.items():
            if hgvs_type in patterns:
                if not patterns[hgvs_type].match(notation):
                    return (
                        False,
                        f"Invalid HGVS {hgvs_type} notation: {notation}",
                        f"Check HGVS {hgvs_type} format",
                    )

        return True, "", None

    # Phenotype validation methods

    def _validate_hpo_id(
        self, hpo_id: Optional[str]
    ) -> tuple[bool, str, Optional[str]]:
        """Validate HPO ID format."""
        if not hpo_id:
            return (
                False,
                "HPO ID is required for HPO terms",
                "Provide valid HPO identifier",
            )

        if not re.match(r"^HP:\d+$", hpo_id):
            return (
                False,
                f"Invalid HPO ID format: {hpo_id}",
                "HPO IDs should be in format HP:NNNNNN",
            )

        return True, "", None

    def _validate_phenotype_name_case(
        self, name: Optional[str]
    ) -> tuple[bool, str, Optional[str]]:
        """Validate phenotype name capitalization."""
        if not name:
            return True, "", None  # Skip if no name

        # Check if first letter is capitalized
        if not name[0].isupper():
            return (
                False,
                f"Phenotype name should start with capital letter: {name}",
                f"Use {name[0].upper() + name[1:]} instead",
            )

        return True, "", None

    # Publication validation methods

    def _validate_pubmed_id(
        self, pubmed_id: Optional[Union[str, int]]
    ) -> tuple[bool, str, Optional[str]]:
        """Validate PubMed ID format."""
        if pubmed_id is None:
            return False, "PubMed ID is required", "Provide valid PubMed identifier"

        # Convert to string and check format
        id_str = str(pubmed_id)

        if not re.match(r"^\d+$", id_str):
            return (
                False,
                f"Invalid PubMed ID format: {pubmed_id}",
                "PubMed IDs should contain only digits",
            )

        # Check reasonable range (PubMed started in 1966, current IDs are ~30M+)
        id_num = int(id_str)
        if id_num < 1000 or id_num > 50_000_000:
            return (
                False,
                f"Suspicious PubMed ID range: {pubmed_id}",
                "Verify PubMed ID is correct",
            )

        return True, "", None

    def _validate_doi(self, doi: Optional[str]) -> tuple[bool, str, Optional[str]]:
        """Validate DOI format."""
        if not doi:
            return True, "", None  # Optional field

        # Standard DOI format check
        if not re.match(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", doi, re.IGNORECASE):
            return (
                False,
                f"Invalid DOI format: {doi}",
                "DOIs should start with 10. followed by registrant code",
            )

        return True, "", None

    # Generic validation methods

    def _validate_range(
        self, value: Optional[Union[int, float]], min_val: float, max_val: float
    ) -> tuple[bool, str, Optional[str]]:
        """Validate value is within range."""
        if value is None:
            return False, "Value is required", "Provide a numeric value"

        if not isinstance(value, (int, float)):
            return False, f"Value must be numeric: {value}", "Provide a number"

        if not (min_val <= value <= max_val):
            return (
                False,
                f"Value {value} not in range [{min_val}, {max_val}]",
                f"Value should be between {min_val} and {max_val}",
            )

        return True, "", None

    def _validate_length(
        self, value: Optional[str], min_len: int = 0, max_len: int = 1000
    ) -> tuple[bool, str, Optional[str]]:
        """Validate string length."""
        if value is None:
            return min_len == 0, "Value is required", "Provide a non-empty value"

        length = len(str(value))
        if length < min_len:
            return (
                False,
                f"Value too short: {length} < {min_len}",
                f"Provide at least {min_len} characters",
            )

        if length > max_len:
            return (
                False,
                f"Value too long: {length} > {max_len}",
                f"Limit to {max_len} characters",
            )

        return True, "", None

    def _validate_list_length(
        self, value: Optional[List], min_len: int = 0, max_len: int = 1000
    ) -> tuple[bool, str, Optional[str]]:
        """Validate list length."""
        if value is None:
            return min_len == 0, "List is required", "Provide a non-empty list"

        if not isinstance(value, list):
            return False, f"Value must be a list: {type(value)}", "Provide a list"

        length = len(value)
        if length < min_len:
            return (
                False,
                f"List too short: {length} < {min_len}",
                f"Provide at least {min_len} items",
            )

        if length > max_len:
            return (
                False,
                f"List too long: {length} > {max_len}",
                f"Limit to {max_len} items",
            )

        return True, "", None


# Convenience functions for common validation operations


def validate_gene_data(
    genes: List[Dict[str, Any]], level: ValidationLevel = ValidationLevel.STANDARD
) -> List[ValidationResult]:
    """Validate a list of gene entities."""
    validator = DataQualityValidator(level)
    return validator.validate_batch("gene", genes)


def validate_variant_data(
    variants: List[Dict[str, Any]], level: ValidationLevel = ValidationLevel.STANDARD
) -> List[ValidationResult]:
    """Validate a list of variant entities."""
    validator = DataQualityValidator(level)
    return validator.validate_batch("variant", variants)


def validate_phenotype_data(
    phenotypes: List[Dict[str, Any]], level: ValidationLevel = ValidationLevel.STANDARD
) -> List[ValidationResult]:
    """Validate a list of phenotype entities."""
    validator = DataQualityValidator(level)
    return validator.validate_batch("phenotype", phenotypes)


def validate_publication_data(
    publications: List[Dict[str, Any]],
    level: ValidationLevel = ValidationLevel.STANDARD,
) -> List[ValidationResult]:
    """Validate a list of publication entities."""
    validator = DataQualityValidator(level)
    return validator.validate_batch("publication", publications)
