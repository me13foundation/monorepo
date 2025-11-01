"""
Advanced validation rules for gene entities.

Implements business logic validation for genes including:
- HGNC nomenclature compliance
- Cross-reference consistency
- Genomic coordinate validation
- Functional annotation verification
"""

import re
from typing import Dict, List, Any
from dataclasses import dataclass

from .base_rules import ValidationRule, ValidationSeverity


@dataclass
class GeneValidationRules:
    """
    Comprehensive validation rules for gene entities.

    Validates gene symbols, identifiers, genomic coordinates, and functional annotations
    against HGNC standards and biological knowledge.
    """

    # HGNC-approved gene symbol patterns
    HGNC_SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9_-]*$")
    HGNC_ID_PATTERN = re.compile(r"^HGNC:\d+$")

    # Known problematic gene names/symbols
    PROBLEMATIC_SYMBOLS = {
        "UNKNOWN",
        "UNDEFINED",
        "TEST",
        "DUMMY",
        "FAKE",
        "NULL",
        "N/A",
        "NA",
        "NONE",
        "MISSING",
    }

    # Valid chromosome names
    VALID_CHROMOSOMES = set(str(i) for i in range(1, 23)) | {"X", "Y", "M", "MT"}

    @staticmethod
    def validate_hgnc_nomenclature(symbol: str) -> ValidationRule:
        """Validate HGNC gene nomenclature compliance."""

        def rule(value):
            if not value or not isinstance(value, str):
                return (
                    False,
                    "Gene symbol is required",
                    "Provide a valid HGNC gene symbol",
                )

            symbol_str = value.strip()

            # Check for problematic symbols
            if symbol_str.upper() in GeneValidationRules.PROBLEMATIC_SYMBOLS:
                return (
                    False,
                    f"Problematic gene symbol: {symbol_str}",
                    "Use a valid HGNC-approved gene symbol",
                )

            # Check format
            if not GeneValidationRules.HGNC_SYMBOL_PATTERN.match(symbol_str):
                return (
                    False,
                    f"Invalid gene symbol format: {symbol_str}",
                    "Gene symbols should start with a letter and contain only letters, numbers, underscores, and hyphens",
                )

            # Check length
            if len(symbol_str) < 2 or len(symbol_str) > 20:
                return (
                    False,
                    f"Gene symbol length {len(symbol_str)} is invalid",
                    "Gene symbols should be 2-20 characters long",
                )

            # Check for all caps (most HGNC symbols are uppercase)
            if symbol_str != symbol_str.upper():
                return (
                    False,
                    f"Gene symbol should be uppercase: {symbol_str}",
                    f"Use {symbol_str.upper()} instead",
                )

            return True, "", None

        return ValidationRule(
            field="symbol",
            rule="hgnc_nomenclature",
            validator=rule,
            severity=ValidationSeverity.ERROR,
            level="STANDARD",
        )

    @staticmethod
    def validate_hgnc_id_format(hgnc_id: str) -> ValidationRule:
        """Validate HGNC ID format."""

        def rule(value):
            if not value:
                return True, "", None  # Optional field

            if not isinstance(value, str):
                return (
                    False,
                    f"HGNC ID must be string: {type(value)}",
                    "Provide HGNC ID as string",
                )

            if not GeneValidationRules.HGNC_ID_PATTERN.match(value):
                return (
                    False,
                    f"Invalid HGNC ID format: {value}",
                    "HGNC IDs should be in format HGNC:NNNNNN",
                )

            # Check numeric part
            try:
                numeric_part = int(value.split(":")[1])
                if numeric_part <= 0:
                    return (
                        False,
                        f"Invalid HGNC ID number: {numeric_part}",
                        "HGNC ID numbers should be positive",
                    )
            except (IndexError, ValueError):
                return (
                    False,
                    f"Cannot parse HGNC ID number from: {value}",
                    "Ensure HGNC ID format is correct",
                )

            return True, "", None

        return ValidationRule(
            field="hgnc_id",
            rule="hgnc_id_format",
            validator=rule,
            severity=ValidationSeverity.WARNING,
            level="STANDARD",
        )

    @staticmethod
    def validate_cross_reference_consistency(
        cross_refs: Dict[str, List[str]],
    ) -> ValidationRule:
        """Validate consistency between different gene identifiers."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None  # Optional field

            issues = []

            # Check for HGNC symbol/ID consistency
            hgnc_symbols = value.get("SYMBOL", [])
            hgnc_ids = value.get("HGNC", [])

            if hgnc_symbols and hgnc_ids:
                # If we have both symbols and IDs, they should be consistent
                # This is a simplified check - in practice would need HGNC database lookup
                symbol_count = len(hgnc_symbols)
                id_count = len(hgnc_ids)

                if symbol_count != id_count and symbol_count != 1 and id_count != 1:
                    issues.append(
                        f"Mismatch between HGNC symbols ({symbol_count}) and IDs ({id_count})"
                    )

            # Check for empty cross-references
            for ref_type, ref_ids in value.items():
                if isinstance(ref_ids, list) and len(ref_ids) == 0:
                    issues.append(f"Empty cross-reference list for {ref_type}")

            if issues:
                return (
                    False,
                    "Cross-reference consistency issues: " + "; ".join(issues),
                    "Review and correct cross-references",
                )

            return True, "", None

        return ValidationRule(
            field="cross_references",
            rule="cross_reference_consistency",
            validator=rule,
            severity=ValidationSeverity.WARNING,
            level="STANDARD",
        )

    @staticmethod
    def validate_genomic_coordinates(
        chromosome: str, start_pos: int, end_pos: int
    ) -> ValidationRule:
        """Validate genomic coordinates for biological plausibility."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None  # Optional genomic data

            chrom = value.get("chromosome")
            start = value.get("start_position")
            end = value.get("end_position")

            if not chrom:
                return True, "", None  # No chromosome specified

            # Validate chromosome
            if chrom not in GeneValidationRules.VALID_CHROMOSOMES:
                return (
                    False,
                    f"Invalid chromosome: {chrom}",
                    f"Valid chromosomes: {', '.join(sorted(GeneValidationRules.VALID_CHROMOSOMES))}",
                )

            # Validate positions if provided
            if start is not None and end is not None:
                if not isinstance(start, int) or not isinstance(end, int):
                    return (
                        False,
                        "Genomic positions must be integers",
                        "Provide integer coordinates",
                    )

                if start < 0 or end < 0:
                    return (
                        False,
                        f"Negative genomic positions not allowed: start={start}, end={end}",
                        "Genomic positions must be positive",
                    )

                if start >= end:
                    return (
                        False,
                        f"Start position ({start}) must be less than end position ({end})",
                        "Ensure start < end",
                    )

                # Check for biologically implausible gene sizes
                gene_size = end - start
                if gene_size < 10:  # Too small for a gene
                    return (
                        False,
                        f"Gene too small ({gene_size} bp)",
                        "Genes are typically >10 bp",
                    )

                if gene_size > 2_000_000:  # Too large (2Mb)
                    return (
                        False,
                        f"Gene suspiciously large ({gene_size:,} bp)",
                        "Review gene coordinates",
                    )

                # Check chromosome-specific size limits
                chrom_size_limits = {
                    "M": 20_000,  # Mitochondrial genome
                    "MT": 20_000,
                }

                max_size = chrom_size_limits.get(
                    chrom, 250_000_000
                )  # Default ~250Mb for human chromosomes
                if gene_size > max_size:
                    return (
                        False,
                        f"Gene size ({gene_size:,} bp) exceeds chromosome {chrom} maximum ({max_size:,} bp)",
                        "Check coordinates",
                    )

            return True, "", None

        return ValidationRule(
            field="genomic_coordinates",
            rule="genomic_coordinates",
            validator=rule,
            severity=ValidationSeverity.ERROR,
            level="STANDARD",
        )

    @staticmethod
    def validate_functional_annotations(
        function_info: Dict[str, Any],
    ) -> ValidationRule:
        """Validate functional annotations for biological accuracy."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None  # Optional field

            issues = []

            # Check gene type classification
            gene_type = value.get("gene_type")
            if gene_type:
                valid_types = {
                    "protein_coding",
                    "pseudogene",
                    "rna_gene",
                    "other_gene",
                    "known",
                    "novel",
                    "putative",
                }
                if gene_type.lower() not in valid_types:
                    issues.append(f"Unknown gene type: {gene_type}")

            # Check biotype consistency
            biotype = value.get("biotype")
            if biotype and gene_type:
                # Basic consistency checks
                if gene_type == "protein_coding" and "pseudogene" in biotype.lower():
                    issues.append("Protein-coding gene classified as pseudogene")

            # Validate GO terms if present
            go_terms = value.get("go_terms", [])
            if go_terms:
                go_pattern = re.compile(r"^GO:\d{7}$")
                invalid_go = [term for term in go_terms if not go_pattern.match(term)]
                if invalid_go:
                    issues.append(
                        f"Invalid GO term format: {invalid_go[:3]}"
                    )  # Show first 3

            if issues:
                return (
                    False,
                    "Functional annotation issues: " + "; ".join(issues),
                    "Review and correct functional annotations",
                )

            return True, "", None

        return ValidationRule(
            field="functional_annotations",
            rule="functional_annotations",
            validator=rule,
            severity=ValidationSeverity.WARNING,
            level="STANDARD",
        )

    @staticmethod
    def validate_orthology_data(orthology_info: Dict[str, Any]) -> ValidationRule:
        """Validate orthology and evolutionary conservation data."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None  # Optional field

            issues = []

            # Check species validity
            orthologs = value.get("orthologs", [])
            if orthologs:
                for ortho in orthologs:
                    if isinstance(ortho, dict):
                        species = ortho.get("species")
                        if species:
                            # Basic species name validation
                            if not re.match(r"^[A-Z][a-z]+ [a-z]+$", species):
                                issues.append(
                                    f"Suspicious species name format: {species}"
                                )

            # Check conservation scores
            conservation_score = value.get("conservation_score")
            if conservation_score is not None:
                if not isinstance(conservation_score, (int, float)):
                    issues.append("Conservation score must be numeric")
                elif not (0.0 <= conservation_score <= 1.0):
                    issues.append(
                        f"Conservation score out of range: {conservation_score}"
                    )

            if issues:
                return (
                    False,
                    "Orthology validation issues: " + "; ".join(issues),
                    "Review orthology data",
                )

            return True, "", None

        return ValidationRule(
            field="orthology_data",
            rule="orthology_data",
            validator=rule,
            severity=ValidationSeverity.INFO,
            level="STRICT",
        )

    @classmethod
    def get_all_rules(cls) -> List[ValidationRule]:
        """Get all gene validation rules."""
        return [
            cls.validate_hgnc_nomenclature("symbol"),
            cls.validate_hgnc_id_format("hgnc_id"),
            cls.validate_cross_reference_consistency({}),
            cls.validate_genomic_coordinates("", 0, 0),
            cls.validate_functional_annotations({}),
            cls.validate_orthology_data({}),
        ]

    @classmethod
    def validate_gene_comprehensively(
        cls, gene_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Run comprehensive validation on gene data.

        Returns list of validation issues found.
        """
        issues = []

        for rule in cls.get_all_rules():
            field_value = gene_data.get(rule.field)

            # Apply rule-specific validation logic
            if rule.field == "symbol":
                is_valid, message, suggestion = rule.validator(field_value)
            elif rule.field == "hgnc_id":
                is_valid, message, suggestion = rule.validator(field_value)
            elif rule.field == "cross_references":
                is_valid, message, suggestion = rule.validator(field_value)
            elif rule.field == "genomic_coordinates":
                # For coordinate validation, pass the whole coordinate dict
                is_valid, message, suggestion = rule.validator(field_value or {})
            elif rule.field == "functional_annotations":
                is_valid, message, suggestion = rule.validator(field_value or {})
            elif rule.field == "orthology_data":
                is_valid, message, suggestion = rule.validator(field_value or {})
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
