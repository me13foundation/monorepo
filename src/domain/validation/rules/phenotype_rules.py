"""
Advanced validation rules for phenotype entities.

Implements business logic validation for phenotypes including:
- HPO term validation and hierarchy checking
- OMIM disease validation
- Clinical feature consistency
- Age of onset validation
- Severity assessment
"""

import re
from typing import Dict, List, Any
from dataclasses import dataclass

from .base_rules import ValidationRule, ValidationSeverity


@dataclass
class PhenotypeValidationRules:
    """
    Comprehensive validation rules for phenotype entities.

    Validates phenotype terms, clinical features, inheritance patterns,
    and relationships for medical accuracy.
    """

    # HPO term patterns
    HPO_TERM_PATTERN = re.compile(r"^HP:\d{7}$")

    # Valid HPO term categories
    HPO_CATEGORIES = {
        "HP:0000118": "Phenotypic abnormality",
        "HP:0000005": "Mode of inheritance",
        "HP:0000001": "All",
        "HP:0032223": "Blood group",
        "HP:0000478": "Abnormality of the eye",
        "HP:0000598": "Abnormality of the ear",
        "HP:0000152": "Abnormality of head or neck",
        "HP:0000234": "Abnormality of the head",
        "HP:0000271": "Abnormality of the face",
        "HP:0000924": "Abnormality of the skeletal system",
        "HP:0000769": "Abnormality of the breast",
        "HP:0000811": "Abnormality of the endocrine system",
        "HP:0001197": "Prenatal development or birth",
        "HP:0001507": "Growth abnormality",
        "HP:0001626": "Abnormality of the cardiovascular system",
        "HP:0001871": "Abnormality of blood and blood-forming tissues",
        "HP:0002664": "Neoplasm",
        "HP:0002715": "Abnormality of the immune system",
        "HP:0003537": "Abnormality of the nervous system",
        "HP:0000119": "Abnormality of the genitourinary system",
        "HP:0000479": "Abnormality of the eye",
        "HP:0001939": "Abnormality of metabolism/homeostasis",
        "HP:0001608": "Abnormality of the voice",
        "HP:0001574": "Abnormality of the integument",
    }

    # Age of onset categories
    AGE_OF_ONSET_CATEGORIES = {
        "HP:0003577": "Congenital onset",
        "HP:0003623": "Neonatal onset",
        "HP:0003621": "Juvenile onset",
        "HP:0003581": "Adult onset",
        "HP:0003596": "Middle age onset",
        "HP:0003584": "Late onset",
        "HP:0003593": "Infantile onset",
        "HP:0003627": "Childhood onset",
        "HP:0011463": "Young adult onset",
    }

    # Clinical severity levels
    SEVERITY_LEVELS = {
        "HP:0012824": "Mild",
        "HP:0012825": "Moderate",
        "HP:0012826": "Severe",
        "HP:0012823": "Borderline",
    }

    @staticmethod
    def validate_hpo_term_format(hpo_id: str) -> ValidationRule:
        """Validate HPO term ID format and existence."""

        def rule(value):
            if not value:
                return (
                    False,
                    "HPO ID is required for HPO terms",
                    "Provide valid HPO identifier",
                )

            if not isinstance(value, str):
                return (
                    False,
                    f"HPO ID must be string: {type(value)}",
                    "Provide HPO ID as string",
                )

            # Check format
            if not PhenotypeValidationRules.HPO_TERM_PATTERN.match(value):
                return (
                    False,
                    f"Invalid HPO ID format: {value}",
                    "HPO IDs should be in format HP:NNNNNNN (7 digits)",
                )

            # Check if it's a known root term or category
            if value in PhenotypeValidationRules.HPO_CATEGORIES:
                return True, "", None  # Valid root term

            # For other terms, we can't validate existence without database lookup
            # But we can check the numeric range (HPO terms start from ~0000001)
            try:
                term_number = int(value.split(":")[1])
                if term_number <= 0:
                    return (
                        False,
                        f"Invalid HPO term number: {term_number}",
                        "HPO term numbers should be positive",
                    )
                if term_number > 9999999:
                    return (
                        False,
                        f"Suspiciously high HPO term number: {term_number}",
                        "Check HPO ID",
                    )
            except (IndexError, ValueError):
                return (
                    False,
                    f"Cannot parse HPO term number from: {value}",
                    "Ensure HPO ID format is HP:NNNNNNN",
                )

            return True, "", None

        return ValidationRule(
            field="hpo_id",
            rule="hpo_term_format",
            validator=rule,
            severity=ValidationSeverity.ERROR,
            level="STANDARD",
        )

    @staticmethod
    def validate_phenotype_name_consistency(name: str, hpo_id: str) -> ValidationRule:
        """Validate consistency between phenotype name and HPO ID."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None

            name = value.get("name", "").strip()
            hpo_id = value.get("hpo_id", "")

            if not name or not hpo_id:
                return True, "", None  # Cannot validate without both

            name_lower = name.lower()

            # Check for obvious mismatches with known terms
            if hpo_id == "HP:0001249" and "intellectual" not in name_lower:
                return (
                    False,
                    "HPO:0001249 should be 'Intellectual disability'",
                    "Check phenotype name for HP:0001249",
                )

            if hpo_id == "HP:0000729" and "autism" not in name_lower:
                return (
                    False,
                    "HPO:0000729 should be 'Autism'",
                    "Check phenotype name for HP:0000729",
                )

            # Check for generic/problematic names
            problematic_names = [
                "phenotypic abnormality",
                "other",
                "unknown",
                "not specified",
            ]
            if name_lower in problematic_names:
                return (
                    False,
                    f"Too generic phenotype name: {name}",
                    "Use specific HPO term name",
                )

            # Check capitalization (should start with capital letter)
            if name and not name[0].isupper():
                return (
                    False,
                    f"Phenotype name should start with capital letter: {name}",
                    f"Use {name[0].upper() + name[1:]} instead",
                )

            return True, "", None

        return ValidationRule(
            field="name_consistency",
            rule="name_consistency",
            validator=rule,
            severity=ValidationSeverity.WARNING,
            level="STANDARD",
        )

    @staticmethod
    def validate_hpo_hierarchy_consistency(
        parent_terms: List[str], child_terms: List[str]
    ) -> ValidationRule:
        """Validate HPO hierarchy consistency."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None

            parents = value.get("parent_terms", [])
            children = value.get("child_terms", [])

            if not parents and not children:
                return True, "", None

            issues = []

            # Check for circular relationships (simplified)
            all_terms = set(parents + children)
            if len(all_terms) != len(parents) + len(children):
                issues.append(
                    "Possible circular or duplicate relationships in hierarchy"
                )

            # Check for root term issues
            root_term = "HP:0000001"  # All term
            if root_term in children:
                issues.append("Root term HP:0000001 should not appear as a child")

            # Validate term format in relationships
            for term_list, term_type in [(parents, "parent"), (children, "child")]:
                for term in term_list:
                    if not PhenotypeValidationRules.HPO_TERM_PATTERN.match(term):
                        issues.append(f"Invalid {term_type} term format: {term}")

            if issues:
                return (
                    False,
                    "Hierarchy issues: " + "; ".join(issues),
                    "Review HPO term relationships",
                )

            return True, "", None

        return ValidationRule(
            field="hpo_hierarchy",
            rule="hpo_hierarchy",
            validator=rule,
            severity=ValidationSeverity.WARNING,
            level="STRICT",
        )

    @staticmethod
    def validate_age_of_onset_consistency(
        age_onset: str, phenotype_name: str
    ) -> ValidationRule:
        """Validate age of onset consistency with phenotype."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None

            age_onset = value.get("age_of_onset", "")
            phenotype = value.get("phenotype_name", "").lower()

            if not age_onset or not phenotype:
                return True, "", None

            age_lower = age_onset.lower()

            # Check for developmental phenotypes with adult onset
            if "developmental" in phenotype or "congenital" in phenotype:
                if "adult" in age_lower:
                    return (
                        False,
                        f"Developmental phenotype '{phenotype}' with adult onset",
                        "Developmental phenotypes typically have childhood onset",
                    )

            # Check for age-related diseases
            if "alzheimer" in phenotype:
                if "childhood" in age_lower or "neonatal" in age_lower:
                    return (
                        False,
                        "Alzheimer's disease with childhood onset",
                        "Alzheimer's typically has adult onset",
                    )

            if "progeria" in phenotype:  # Premature aging
                if "adult" in age_lower:
                    return (
                        False,
                        "Progeria with adult onset",
                        "Progeria typically has childhood onset",
                    )

            return True, "", None

        return ValidationRule(
            field="age_onset_consistency",
            rule="age_onset_consistency",
            validator=rule,
            severity=ValidationSeverity.INFO,
            level="STRICT",
        )

    @staticmethod
    def validate_clinical_severity_assessment(
        severity: str, phenotype_features: List[str]
    ) -> ValidationRule:
        """Validate clinical severity assessment."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None

            severity = value.get("severity", "")
            features = value.get("features", [])

            if not severity:
                return True, "", None

            severity_lower = severity.lower()
            issues = []

            # Check severity consistency with features
            severe_features = [
                "life-threatening",
                "fatal",
                "severe intellectual disability",
                "profound",
            ]
            mild_features = ["mild", "borderline", "minimal", "slight"]

            if severity_lower == "severe" and any(
                mild_feat in " ".join(features).lower() for mild_feat in mild_features
            ):
                issues.append("Severe phenotype with mild features")

            if severity_lower == "mild" and any(
                severe_feat in " ".join(features).lower()
                for severe_feat in severe_features
            ):
                issues.append("Mild phenotype with severe features")

            # Check for contradictory severity terms
            if (
                severity_lower in ["mild", "moderate", "severe"]
                and "variable" in severity_lower
            ):
                issues.append(
                    "Variable severity should be used instead of specific level"
                )

            if issues:
                return (
                    False,
                    "Severity assessment issues: " + "; ".join(issues),
                    "Review severity classification",
                )

            return True, "", None

        return ValidationRule(
            field="clinical_severity",
            rule="clinical_severity",
            validator=rule,
            severity=ValidationSeverity.INFO,
            level="STRICT",
        )

    @staticmethod
    def validate_inheritance_pattern_consistency(
        inheritance: str, phenotype_name: str
    ) -> ValidationRule:
        """Validate inheritance pattern consistency with phenotype."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None

            inheritance = value.get("inheritance", "").lower()
            phenotype = value.get("phenotype_name", "").lower()

            if not inheritance or not phenotype:
                return True, "", None

            # Check for known inheritance-phenotype associations
            if "autosomal dominant" in inheritance:
                # AD conditions that are almost always lethal if homozygous
                lethal_ad = ["achondroplasia", "marfan", "neurofibromatosis"]
                if any(term in phenotype for term in lethal_ad):
                    return (
                        False,
                        f"'{phenotype}' typically shows autosomal dominant inheritance",
                        "Review inheritance pattern",
                    )

            if "x_linked" in inheritance:
                # Check for male predominance in X-linked conditions
                male_specific_terms = ["dystrophin", "fragile x", "duchenne"]
                if any(term in phenotype for term in male_specific_terms):
                    return True, "", None  # Valid
                # Could add more validation here

            if "autosomal recessive" in inheritance:
                # AR conditions often show in consanguineous families
                # This would need more context to validate properly
                pass

            return True, "", None

        return ValidationRule(
            field="inheritance_consistency",
            rule="inheritance_consistency",
            validator=rule,
            severity=ValidationSeverity.INFO,
            level="STRICT",
        )

    @staticmethod
    def validate_cross_references_integrity(
        cross_refs: Dict[str, List[str]],
    ) -> ValidationRule:
        """Validate cross-references between phenotype databases."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None

            issues = []

            # Check OMIM cross-references
            omim_refs = value.get("OMIM", [])
            for omim_id in omim_refs:
                if not re.match(r"^\d{6}$", omim_id):  # OMIM IDs are 6 digits
                    issues.append(f"Invalid OMIM ID format: {omim_id}")

            # Check Orphanet cross-references
            orpha_refs = value.get("Orphanet", [])
            for orpha_id in orpha_refs:
                if not re.match(r"^ORPHA:\d+$", orpha_id):
                    issues.append(f"Invalid Orphanet ID format: {orpha_id}")

            # Check for empty cross-reference lists
            for db, refs in value.items():
                if isinstance(refs, list) and len(refs) == 0:
                    issues.append(f"Empty cross-reference list for {db}")

            # Check for duplicate IDs within same database
            for db, refs in value.items():
                if isinstance(refs, list) and len(refs) != len(set(refs)):
                    issues.append(f"Duplicate IDs in {db} cross-references")

            if issues:
                return (
                    False,
                    "Cross-reference issues: " + "; ".join(issues),
                    "Review and correct cross-references",
                )

            return True, "", None

        return ValidationRule(
            field="cross_references",
            rule="cross_references_integrity",
            validator=rule,
            severity=ValidationSeverity.WARNING,
            level="STANDARD",
        )

    @classmethod
    def get_all_rules(cls) -> List[ValidationRule]:
        """Get all phenotype validation rules."""
        return [
            cls.validate_hpo_term_format(""),
            cls.validate_phenotype_name_consistency({}, ""),
            cls.validate_hpo_hierarchy_consistency([], []),
            cls.validate_age_of_onset_consistency("", ""),
            cls.validate_clinical_severity_assessment("", []),
            cls.validate_inheritance_pattern_consistency("", ""),
            cls.validate_cross_references_integrity({}),
        ]

    @classmethod
    def validate_phenotype_comprehensively(
        cls, phenotype_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Run comprehensive validation on phenotype data.

        Returns list of validation issues found.
        """
        issues = []

        for rule in cls.get_all_rules():
            # Apply rule-specific validation logic
            if rule.rule == "hpo_term_format":
                field_value = phenotype_data.get(rule.field)
                is_valid, message, suggestion = rule.validator(field_value)
            elif rule.rule == "name_consistency":
                combined_data = {
                    "name": phenotype_data.get("name"),
                    "hpo_id": phenotype_data.get("hpo_id"),
                }
                is_valid, message, suggestion = rule.validator(combined_data)
            elif rule.rule == "hpo_hierarchy":
                combined_data = {
                    "parent_terms": phenotype_data.get("parent_terms", []),
                    "child_terms": phenotype_data.get("child_terms", []),
                }
                is_valid, message, suggestion = rule.validator(combined_data)
            elif rule.rule == "age_onset_consistency":
                combined_data = {
                    "age_of_onset": phenotype_data.get("age_of_onset"),
                    "phenotype_name": phenotype_data.get("name", ""),
                }
                is_valid, message, suggestion = rule.validator(combined_data)
            elif rule.rule == "clinical_severity":
                combined_data = {
                    "severity": phenotype_data.get("severity"),
                    "features": phenotype_data.get("features", []),
                }
                is_valid, message, suggestion = rule.validator(combined_data)
            elif rule.rule == "inheritance_consistency":
                combined_data = {
                    "inheritance": phenotype_data.get("inheritance_pattern"),
                    "phenotype_name": phenotype_data.get("name", ""),
                }
                is_valid, message, suggestion = rule.validator(combined_data)
            elif rule.rule == "cross_references_integrity":
                field_value = phenotype_data.get(rule.field)
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
