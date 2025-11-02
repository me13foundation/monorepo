"""
Integrity validator for relationship validation.

Validates referential integrity, foreign key relationships,
and consistency between related entities.
"""

from typing import Dict, Any, Set
from dataclasses import dataclass

from ..rules.base_rules import ValidationResult, ValidationIssue, ValidationSeverity


@dataclass
class IntegrityValidator:
    """
    Validator for integrity validation.

    Ensures referential integrity and consistency between
    related entities in the knowledge graph.
    """

    def validate_foreign_keys(
        self,
        entity_data: Dict[str, Any],
        entity_type: str,
        valid_references: Dict[str, Set[str]],
    ) -> ValidationResult:
        """Validate foreign key references exist in related entities."""
        issues = []

        # Define expected foreign key fields by entity type
        fk_fields = {
            "variant": ["gene_references"],
            "evidence": [
                "gene_references",
                "variant_references",
                "phenotype_references",
            ],
            "phenotype": ["gene_references"],
        }

        expected_refs = fk_fields.get(entity_type, [])
        for ref_field in expected_refs:
            if ref_field in entity_data:
                references = entity_data[ref_field]
                if isinstance(references, list):
                    for ref in references:
                        if ref_field.replace("_references", "s") in valid_references:
                            valid_set = valid_references[
                                ref_field.replace("_references", "s")
                            ]
                            if ref not in valid_set:
                                issues.append(
                                    ValidationIssue(
                                        field=ref_field,
                                        value=ref,
                                        rule="foreign_key_integrity",
                                        message=f"Reference '{ref}' not found in {ref_field.replace('_references', 's')}",
                                        severity=ValidationSeverity.ERROR,
                                    )
                                )

        return ValidationResult(is_valid=len(issues) == 0, issues=issues)

    def validate_relationship_consistency(
        self,
        entity_data: Dict[str, Any],
        entity_type: str,
        related_entities: Dict[str, Any],
    ) -> ValidationResult:
        """Validate consistency between bidirectional relationships."""
        issues = []

        if entity_type == "gene":
            # Check that variants reference this gene
            gene_id = entity_data.get("gene_id")
            if gene_id:
                variant_refs = entity_data.get("variant_references", [])
                for variant_id in variant_refs:
                    variant_data = related_entities.get("variants", {}).get(variant_id)
                    if variant_data:
                        gene_refs = variant_data.get("gene_references", [])
                        if gene_id not in gene_refs:
                            issues.append(
                                ValidationIssue(
                                    field="variant_references",
                                    value=variant_id,
                                    rule="bidirectional_relationship",
                                    message=f"Variant {variant_id} does not reference gene {gene_id}",
                                    severity=ValidationSeverity.WARNING,
                                )
                            )

        elif entity_type == "variant":
            # Check that genes reference this variant
            variant_id = entity_data.get("variant_id")
            if variant_id:
                gene_refs = entity_data.get("gene_references", [])
                for gene_id in gene_refs:
                    gene_data = related_entities.get("genes", {}).get(gene_id)
                    if gene_data:
                        variant_refs = gene_data.get("variant_references", [])
                        if variant_id not in variant_refs:
                            issues.append(
                                ValidationIssue(
                                    field="gene_references",
                                    value=gene_id,
                                    rule="bidirectional_relationship",
                                    message=f"Gene {gene_id} does not reference variant {variant_id}",
                                    severity=ValidationSeverity.WARNING,
                                )
                            )

        return ValidationResult(is_valid=len(issues) == 0, issues=issues)

    def validate_no_orphaned_records(
        self,
        entity_data: Dict[str, Any],
        entity_type: str,
        all_entities: Dict[str, Any],
    ) -> ValidationResult:
        """Validate that entity is referenced by at least one other entity."""
        issues = []

        entity_id = entity_data.get(f"{entity_type}_id")
        if not entity_id:
            return ValidationResult(
                is_valid=True, issues=[]
            )  # Can't validate without ID

        # Check if this entity is referenced anywhere
        is_referenced = False

        if entity_type == "gene":
            # Check if gene is referenced by variants or phenotypes
            for variant in all_entities.get("variants", {}).values():
                if entity_id in variant.get("gene_references", []):
                    is_referenced = True
                    break
            if not is_referenced:
                for phenotype in all_entities.get("phenotypes", {}).values():
                    if entity_id in phenotype.get("gene_references", []):
                        is_referenced = True
                        break

        elif entity_type == "variant":
            # Check if variant is referenced by genes or evidence
            for gene in all_entities.get("genes", {}).values():
                if entity_id in gene.get("variant_references", []):
                    is_referenced = True
                    break
            if not is_referenced:
                for evidence in all_entities.get("evidence", {}).values():
                    if entity_id in evidence.get("variant_references", []):
                        is_referenced = True
                        break

        elif entity_type == "phenotype":
            # Check if phenotype is referenced by genes or evidence
            for gene in all_entities.get("genes", {}).values():
                if entity_id in gene.get("phenotype_references", []):
                    is_referenced = True
                    break
            if not is_referenced:
                for evidence in all_entities.get("evidence", {}).values():
                    if entity_id in evidence.get("phenotype_references", []):
                        is_referenced = True
                        break

        if not is_referenced:
            issues.append(
                ValidationIssue(
                    field="references",
                    value=None,
                    rule="no_orphaned_records",
                    message=f"{entity_type.title()} {entity_id} is not referenced by any other entity",
                    severity=ValidationSeverity.WARNING,
                )
            )

        return ValidationResult(is_valid=len(issues) == 0, issues=issues)

    def validate_unique_constraints(
        self,
        entity_data: Dict[str, Any],
        entity_type: str,
        existing_entities: Dict[str, Any],
    ) -> ValidationResult:
        """Validate unique constraints across entities."""
        issues = []

        # Define fields that should be unique by entity type
        unique_fields = {
            "gene": ["symbol", "ensembl_id"],
            "variant": ["clinvar_id"],
            "phenotype": ["hpo_id"],
            "publication": ["doi", "pmcid"],
        }

        entity_id = entity_data.get(f"{entity_type}_id")
        fields_to_check = unique_fields.get(entity_type, [])

        for field in fields_to_check:
            value = entity_data.get(field)
            if value is not None:
                # Check if any other entity has the same value for this field
                for other_id, other_data in existing_entities.get(
                    entity_type, {}
                ).items():
                    if other_id != entity_id and other_data.get(field) == value:
                        issues.append(
                            ValidationIssue(
                                field=field,
                                value=value,
                                rule="unique_constraint",
                                message=f"Duplicate {field} '{value}' found in {entity_type} {other_id}",
                                severity=ValidationSeverity.ERROR,
                            )
                        )
                        break

        return ValidationResult(is_valid=len(issues) == 0, issues=issues)

    def validate_circular_references(
        self,
        entity_data: Dict[str, Any],
        entity_type: str,
        all_entities: Dict[str, Any],
    ) -> ValidationResult:
        """Validate that there are no circular reference chains."""
        issues = []

        # This is a simplified check - full circular reference detection
        # would require graph traversal algorithms
        entity_id = entity_data.get(f"{entity_type}_id")
        if not entity_id:
            return ValidationResult(is_valid=True, issues=[])

        # Basic check: ensure entity doesn't reference itself
        ref_fields = ["gene_references", "variant_references", "phenotype_references"]
        for field in ref_fields:
            refs = entity_data.get(field, [])
            if isinstance(refs, list) and entity_id in refs:
                issues.append(
                    ValidationIssue(
                        field=field,
                        value=refs,
                        rule="circular_reference",
                        message=f"Entity {entity_id} cannot reference itself",
                        severity=ValidationSeverity.ERROR,
                    )
                )

        return ValidationResult(is_valid=len(issues) == 0, issues=issues)


__all__ = ["IntegrityValidator"]
