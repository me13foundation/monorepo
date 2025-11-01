"""
Data quality validation service for transformation pipeline.

Provides comprehensive validation rules and quality checks for all
transformed biomedical data entities and relationships.
"""

import re
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

# Import validation rule classes (to avoid circular imports, these are imported in methods)


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
class ValidationRule:
    """A validation rule with configuration."""

    field: str
    rule: str
    validator: callable
    severity: ValidationSeverity
    level: ValidationLevel


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


class ValidationRuleEngine:
    """
    Dynamic validation rule engine.

    Applies validation rules dynamically based on configuration,
    supporting rule selection, prioritization, and result aggregation.
    """

    def __init__(self, level: ValidationLevel = ValidationLevel.STANDARD):
        self.level = level
        self.rule_registry: Dict[str, Dict[str, ValidationRule]] = {}
        self._load_rule_registry()

    def _load_rule_registry(self):
        """Load all available validation rules into the registry."""
        # Import here to avoid circular imports
        from .gene_rules import GeneValidationRules
        from .variant_rules import VariantValidationRules
        from .phenotype_rules import PhenotypeValidationRules
        from .publication_rules import PublicationValidationRules
        from .relationship_rules import RelationshipValidationRules

        # Gene rules
        gene_rules = GeneValidationRules.get_all_rules()
        self.rule_registry["gene"] = {rule.rule: rule for rule in gene_rules}

        # Variant rules
        variant_rules = VariantValidationRules.get_all_rules()
        self.rule_registry["variant"] = {rule.rule: rule for rule in variant_rules}

        # Phenotype rules
        phenotype_rules = PhenotypeValidationRules.get_all_rules()
        self.rule_registry["phenotype"] = {rule.rule: rule for rule in phenotype_rules}

        # Publication rules
        publication_rules = PublicationValidationRules.get_all_rules()
        self.rule_registry["publication"] = {
            rule.rule: rule for rule in publication_rules
        }

        # Relationship rules
        relationship_rules = RelationshipValidationRules.get_all_rules()
        self.rule_registry["relationship"] = {
            rule.rule: rule for rule in relationship_rules
        }

    def validate_entity(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
        rule_selection: Optional[List[str]] = None,
    ) -> ValidationResult:
        """
        Validate an entity using the rule engine.

        Args:
            entity_type: Type of entity ('gene', 'variant', etc.)
            entity_data: Entity data to validate
            rule_selection: Optional list of specific rules to apply

        Returns:
            ValidationResult with issues and quality score
        """
        if entity_type not in self.rule_registry:
            return ValidationResult(
                is_valid=True,
                issues=[
                    ValidationIssue(
                        field="entity_type",
                        value=entity_type,
                        rule="entity_type_check",
                        message=f"Unknown entity type: {entity_type}",
                        severity=ValidationSeverity.ERROR,
                    )
                ],
                score=0.0,
            )

        rules_to_apply = self._select_rules(entity_type, rule_selection)
        issues = []

        for rule in rules_to_apply:
            # Apply rule-specific validation logic
            # Import here to avoid circular imports
            from .gene_rules import GeneValidationRules
            from .variant_rules import VariantValidationRules
            from .phenotype_rules import PhenotypeValidationRules
            from .publication_rules import PublicationValidationRules
            from .relationship_rules import RelationshipValidationRules

            if entity_type == "gene":
                validation_issues = GeneValidationRules.validate_gene_comprehensively(
                    entity_data
                )
                issues.extend(validation_issues)
            elif entity_type == "variant":
                validation_issues = (
                    VariantValidationRules.validate_variant_comprehensively(entity_data)
                )
                issues.extend(validation_issues)
            elif entity_type == "phenotype":
                validation_issues = (
                    PhenotypeValidationRules.validate_phenotype_comprehensively(
                        entity_data
                    )
                )
                issues.extend(validation_issues)
            elif entity_type == "publication":
                validation_issues = (
                    PublicationValidationRules.validate_publication_comprehensively(
                        entity_data
                    )
                )
                issues.extend(validation_issues)
            elif entity_type == "relationship":
                validation_issues = (
                    RelationshipValidationRules.validate_relationship_comprehensively(
                        entity_data
                    )
                )
                issues.extend(validation_issues)

        # Calculate quality score
        score = self._calculate_quality_score(issues)

        return ValidationResult(
            is_valid=len([i for i in issues if i.get("severity") == "error"]) == 0,
            issues=issues,
            score=score,
        )

    def validate_batch(
        self,
        entity_type: str,
        entities: List[Dict[str, Any]],
        rule_selection: Optional[List[str]] = None,
    ) -> List[ValidationResult]:
        """
        Validate a batch of entities.

        Args:
            entity_type: Type of entities
            entities: List of entity data dictionaries
            rule_selection: Optional list of specific rules to apply

        Returns:
            List of ValidationResult objects
        """
        return [
            self.validate_entity(entity_type, entity, rule_selection)
            for entity in entities
        ]

    def _select_rules(
        self, entity_type: str, rule_selection: Optional[List[str]]
    ) -> List[ValidationRule]:
        """Select which rules to apply based on configuration."""
        available_rules = list(self.rule_registry.get(entity_type, {}).values())

        if not rule_selection:
            # Apply all rules that meet the validation level
            return [
                rule for rule in available_rules if self._rule_applies_at_level(rule)
            ]

        # Apply only selected rules
        selected_rules = []
        for rule_name in rule_selection:
            rule = self.rule_registry.get(entity_type, {}).get(rule_name)
            if rule and self._rule_applies_at_level(rule):
                selected_rules.append(rule)

        return selected_rules

    def _rule_applies_at_level(self, rule: ValidationRule) -> bool:
        """Check if a validation rule applies at the current validation level."""
        rule_level = getattr(rule, "level", ValidationLevel.STANDARD)

        if self.level == ValidationLevel.LAX:
            return rule_level in [ValidationLevel.LAX]
        elif self.level == ValidationLevel.STANDARD:
            return rule_level in [ValidationLevel.LAX, ValidationLevel.STANDARD]
        else:  # STRICT
            return True  # All rules apply in strict mode

    def _calculate_quality_score(self, issues: List[Dict[str, Any]]) -> float:
        """Calculate quality score based on validation issues."""
        if not issues:
            return 1.0

        # Weight issues by severity
        error_weight = 0.5
        warning_weight = 0.25
        info_weight = 0.1

        total_penalty = 0.0

        for issue in issues:
            severity = issue.get("severity", "info")
            if severity == "error":
                total_penalty += error_weight
            elif severity == "warning":
                total_penalty += warning_weight
            else:  # info
                total_penalty += info_weight

        # Cap penalty at 1.0
        return max(0.0, 1.0 - min(1.0, total_penalty))

    def get_available_rules(
        self, entity_type: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Get available validation rules.

        Args:
            entity_type: Optional entity type to filter rules

        Returns:
            Dictionary mapping entity types to lists of rule names
        """
        if entity_type:
            rules = list(self.rule_registry.get(entity_type, {}).keys())
            return {entity_type: rules}

        return {et: list(rules.keys()) for et, rules in self.rule_registry.items()}

    def create_validation_profile(
        self, profile_config: Dict[str, Any]
    ) -> "ValidationProfile":
        """
        Create a validation profile with custom rule configurations.

        Args:
            profile_config: Configuration for the validation profile

        Returns:
            ValidationProfile object
        """
        return ValidationProfile(self, profile_config)


class ValidationProfile:
    """
    Custom validation profile with specific rule configurations.

    Allows users to create tailored validation workflows with
    specific rules, severity levels, and reporting preferences.
    """

    def __init__(self, engine: ValidationRuleEngine, config: Dict[str, Any]):
        self.engine = engine
        self.config = config
        self.name = config.get("name", "custom_profile")
        self.description = config.get("description", "")
        self.level = config.get("level", ValidationLevel.STANDARD)
        self.rule_selections = config.get(
            "rule_selections", {}
        )  # entity_type -> list of rule names
        self.severity_overrides = config.get(
            "severity_overrides", {}
        )  # rule_name -> new_severity

    def validate_entity(
        self, entity_type: str, entity_data: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate an entity using this profile's configuration.

        Args:
            entity_type: Type of entity
            entity_data: Entity data

        Returns:
            ValidationResult with profile-specific validation
        """
        # Get rule selection for this entity type
        rule_selection = self.rule_selections.get(entity_type)

        # Validate using the engine
        result = self.engine.validate_entity(entity_type, entity_data, rule_selection)

        # Apply severity overrides
        for issue in result.issues:
            rule_name = issue.get("rule")
            if rule_name in self.severity_overrides:
                issue["severity"] = self.severity_overrides[rule_name].value

        # Recalculate quality score with new severities
        result.score = self.engine._calculate_quality_score(result.issues)

        return result

    def validate_batch(
        self, entity_type: str, entities: List[Dict[str, Any]]
    ) -> List[ValidationResult]:
        """
        Validate a batch of entities using this profile.

        Args:
            entity_type: Type of entities
            entities: List of entity data

        Returns:
            List of ValidationResult objects
        """
        return [self.validate_entity(entity_type, entity) for entity in entities]

    def get_profile_summary(self) -> Dict[str, Any]:
        """
        Get a summary of this validation profile.

        Returns:
            Dictionary with profile information
        """
        return {
            "name": self.name,
            "description": self.description,
            "level": self.level.value,
            "rule_selections": self.rule_selections,
            "severity_overrides": {
                k: v.value for k, v in self.severity_overrides.items()
            },
            "available_rules": self.engine.get_available_rules(),
        }
