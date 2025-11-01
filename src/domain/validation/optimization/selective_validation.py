"""
Selective validation for performance optimization.

Provides intelligent rule selection and validation skipping based on
entity characteristics, data quality profiles, and validation history.
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..rules.base_rules import ValidationRuleEngine, ValidationResult


class SelectionStrategy(Enum):
    """Strategies for selective validation."""

    CONFIDENCE_BASED = "confidence_based"  # Skip based on data confidence
    TYPE_BASED = "type_based"  # Select rules based on entity type
    PROFILE_BASED = "profile_based"  # Use predefined validation profiles
    ADAPTIVE = "adaptive"  # Learn from validation history
    RISK_BASED = "risk_based"  # Focus on high-risk validations


@dataclass
class ValidationProfile:
    """Profile defining which rules to apply under what conditions."""

    name: str
    entity_types: List[str]
    required_rules: List[str]  # Always apply these rules
    conditional_rules: Dict[str, Dict[str, Any]]  # Conditions for rule application
    skip_conditions: List[Dict[str, Any]]  # When to skip validation entirely
    priority_rules: List[str]  # High-priority rules to check first
    quality_threshold: float = 0.8


class SelectiveValidator:
    """
    Intelligent selective validation system.

    Applies validation rules selectively based on data characteristics,
    quality profiles, and validation history to optimize performance.
    """

    def __init__(
        self,
        rule_engine: ValidationRuleEngine,
        strategy: SelectionStrategy = SelectionStrategy.ADAPTIVE,
    ):
        self.rule_engine = rule_engine
        self.strategy = strategy

        # Validation profiles
        self.profiles: Dict[str, ValidationProfile] = {}
        self.active_profile: Optional[str] = None

        # Validation history for adaptive learning
        self.validation_history: Dict[str, List[Dict[str, Any]]] = {}

        # Confidence scores for entities
        self.confidence_scores: Dict[str, float] = {}

        # Performance tracking
        self.stats = {
            "validations_attempted": 0,
            "validations_skipped": 0,
            "rules_applied": 0,
            "rules_skipped": 0,
            "avg_selectivity": 0.0,
        }

    def validate_selectively(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Validate an entity using selective rule application.

        Args:
            entity_type: Type of entity
            entity_data: Entity data
            context: Optional validation context

        Returns:
            ValidationResult with selective validation applied
        """
        self.stats["validations_attempted"] += 1

        # Check if validation should be skipped entirely
        if self._should_skip_validation(entity_type, entity_data, context):
            self.stats["validations_skipped"] += 1
            return ValidationResult(
                is_valid=True,
                issues=[],
                score=1.0,  # Assume valid if skipped
            )

        # Select rules to apply
        rule_selection = self._select_rules(entity_type, entity_data, context)

        if not rule_selection:
            # No rules selected - return neutral result
            return ValidationResult(is_valid=True, issues=[], score=0.5)

        # Apply selected rules
        result = self.rule_engine.validate_entity(
            entity_type, entity_data, rule_selection
        )

        # Update statistics
        total_available_rules = len(
            self.rule_engine.get_available_rules(entity_type).get(entity_type, [])
        )
        self.stats["rules_applied"] += len(rule_selection)
        self.stats["rules_skipped"] += max(
            0, total_available_rules - len(rule_selection)
        )

        # Update selectivity metric
        if total_available_rules > 0:
            selectivity = len(rule_selection) / total_available_rules
            self.stats["avg_selectivity"] = (
                self.stats["avg_selectivity"]
                * (self.stats["validations_attempted"] - 1)
                + selectivity
            ) / self.stats["validations_attempted"]

        # Store validation history for adaptive learning
        self._record_validation_history(
            entity_type, entity_data, rule_selection, result, context
        )

        return result

    def validate_batch_selectively(
        self,
        entity_type: str,
        entities: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ValidationResult]:
        """
        Validate a batch of entities selectively.

        Args:
            entity_type: Type of entities
            entities: List of entity data
            context: Optional validation context

        Returns:
            List of ValidationResult objects
        """
        results = []

        for entity in entities:
            result = self.validate_selectively(entity_type, entity, context)
            results.append(result)

        return results

    def _should_skip_validation(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> bool:
        """Determine if validation should be skipped entirely."""
        # Check active profile skip conditions
        if self.active_profile and self.active_profile in self.profiles:
            profile = self.profiles[self.active_profile]
            for condition in profile.skip_conditions:
                if self._matches_condition(entity_data, condition, context):
                    return True

        # Check confidence-based skipping
        if self.strategy == SelectionStrategy.CONFIDENCE_BASED:
            entity_key = self._get_entity_key(entity_type, entity_data)
            confidence = self.confidence_scores.get(entity_key, 0.5)

            # Skip if confidence is very high
            if confidence > 0.9:
                return True

        # Check data quality indicators
        quality_indicators = self._assess_data_quality(entity_data)

        # Skip validation for obviously poor data (would fail anyway)
        if quality_indicators["completeness"] < 0.1:  # Less than 10% complete
            return True

        return False

    def _select_rules(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Select which validation rules to apply."""
        available_rules = list(
            self.rule_engine.get_available_rules(entity_type)
            .get(entity_type, {})
            .keys()
        )

        if not available_rules:
            return []

        # Apply selection strategy
        if self.strategy == SelectionStrategy.CONFIDENCE_BASED:
            return self._select_confidence_based(
                entity_type, entity_data, available_rules
            )
        elif self.strategy == SelectionStrategy.TYPE_BASED:
            return self._select_type_based(entity_type, entity_data, available_rules)
        elif self.strategy == SelectionStrategy.PROFILE_BASED:
            return self._select_profile_based(
                entity_type, entity_data, available_rules, context
            )
        elif self.strategy == SelectionStrategy.ADAPTIVE:
            return self._select_adaptive(
                entity_type, entity_data, available_rules, context
            )
        elif self.strategy == SelectionStrategy.RISK_BASED:
            return self._select_risk_based(
                entity_type, entity_data, available_rules, context
            )
        else:
            return available_rules  # Apply all rules

    def _select_confidence_based(
        self, entity_type: str, entity_data: Dict[str, Any], available_rules: List[str]
    ) -> List[str]:
        """Select rules based on data confidence."""
        entity_key = self._get_entity_key(entity_type, entity_data)
        confidence = self.confidence_scores.get(entity_key, 0.5)

        if confidence > 0.8:
            # High confidence - apply only critical rules
            return [
                rule
                for rule in available_rules
                if "format" in rule or "required" in rule
            ]
        elif confidence > 0.6:
            # Medium confidence - apply standard rules
            return [
                rule for rule in available_rules if not rule.endswith("_comprehensive")
            ]
        else:
            # Low confidence - apply all rules
            return available_rules

    def _select_type_based(
        self, entity_type: str, entity_data: Dict[str, Any], available_rules: List[str]
    ) -> List[str]:
        """Select rules based on entity type characteristics."""
        # Define rule priorities by entity type
        type_priorities = {
            "gene": [
                "hgnc_nomenclature",
                "cross_reference_consistency",
                "genomic_coordinates",
            ],
            "variant": [
                "hgvs_notation_comprehensive",
                "clinical_significance_comprehensive",
                "population_frequencies",
            ],
            "phenotype": ["hpo_term_format", "name_consistency", "hpo_hierarchy"],
            "publication": [
                "doi_format_accessibility",
                "author_information",
                "citation_consistency",
            ],
        }

        priorities = type_priorities.get(entity_type, [])

        # Always include high-priority rules
        selected = [
            rule for rule in available_rules if any(p in rule for p in priorities)
        ]

        # Add some additional rules if we have capacity
        remaining = [rule for rule in available_rules if rule not in selected]
        if len(selected) < 5 and remaining:
            selected.extend(remaining[:3])  # Add up to 3 more rules

        return selected

    def _select_profile_based(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
        available_rules: List[str],
        context: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Select rules based on active validation profile."""
        if not self.active_profile or self.active_profile not in self.profiles:
            return available_rules

        profile = self.profiles[self.active_profile]

        # Start with required rules
        selected = [rule for rule in profile.required_rules if rule in available_rules]

        # Add conditional rules that match conditions
        for rule_name, conditions in profile.conditional_rules.items():
            if rule_name in available_rules and self._matches_condition(
                entity_data, conditions, context
            ):
                selected.append(rule_name)

        # Prioritize high-priority rules
        priority_rules = [
            rule for rule in profile.priority_rules if rule in available_rules
        ]
        selected = priority_rules + [
            rule for rule in selected if rule not in priority_rules
        ]

        return selected

    def _select_adaptive(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
        available_rules: List[str],
        context: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Select rules adaptively based on validation history."""
        entity_key = self._get_entity_key(entity_type, entity_data)
        history = self.validation_history.get(entity_key, [])

        if not history:
            # No history - use type-based selection
            return self._select_type_based(entity_type, entity_data, available_rules)

        # Analyze history to find most effective rules
        rule_effectiveness = {}
        for entry in history[-10:]:  # Last 10 validations
            applied_rules = entry.get("rules_applied", [])
            issues_found = len(entry.get("issues", []))

            for rule in applied_rules:
                if rule not in rule_effectiveness:
                    rule_effectiveness[rule] = {"applications": 0, "issues_found": 0}

                rule_effectiveness[rule]["applications"] += 1
                rule_effectiveness[rule]["issues_found"] += issues_found

        # Calculate effectiveness scores
        effective_rules = []
        for rule, stats in rule_effectiveness.items():
            if stats["applications"] > 0:
                effectiveness = stats["issues_found"] / stats["applications"]
                if effectiveness > 0.1:  # Rules that frequently find issues
                    effective_rules.append((rule, effectiveness))

        # Sort by effectiveness and select top rules
        effective_rules.sort(key=lambda x: x[1], reverse=True)
        selected = [rule for rule, _ in effective_rules[:5]]  # Top 5 most effective

        # Fill with other rules if needed
        remaining = [rule for rule in available_rules if rule not in selected]
        selected.extend(remaining[:3])  # Add up to 3 more

        return selected

    def _select_risk_based(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
        available_rules: List[str],
        context: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Select rules based on risk assessment."""
        risk_factors = self._assess_risk_factors(entity_type, entity_data, context)

        # High-risk entities get comprehensive validation
        if risk_factors["overall_risk"] > 0.7:
            return available_rules

        # Medium-risk entities get standard validation
        elif risk_factors["overall_risk"] > 0.4:
            return [
                rule for rule in available_rules if not rule.endswith("_comprehensive")
            ]

        # Low-risk entities get minimal validation
        else:
            critical_rules = [
                rule
                for rule in available_rules
                if "format" in rule or "required" in rule
            ]
            return critical_rules[:3] if critical_rules else available_rules[:3]

    def _matches_condition(
        self,
        entity_data: Dict[str, Any],
        condition: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> bool:
        """Check if entity data matches a condition."""
        field = condition.get("field")
        operator = condition.get("operator", "equals")
        value = condition.get("value")

        if field not in entity_data:
            return False

        actual_value = entity_data[field]

        if operator == "equals":
            return actual_value == value
        elif operator == "contains":
            return value in str(actual_value)
        elif operator == "greater_than":
            return actual_value > value
        elif operator == "less_than":
            return actual_value < value
        elif operator == "regex":
            return bool(re.match(value, str(actual_value)))
        else:
            return False

    def _assess_data_quality(self, entity_data: Dict[str, Any]) -> Dict[str, float]:
        """Assess basic data quality indicators."""
        total_fields = len(entity_data)
        if total_fields == 0:
            return {"completeness": 0.0, "consistency": 0.0}

        # Completeness: percentage of non-null fields
        non_null_fields = sum(
            1 for v in entity_data.values() if v is not None and str(v).strip()
        )
        completeness = non_null_fields / total_fields

        # Consistency: check for obviously inconsistent data
        consistency = 1.0
        if "start_position" in entity_data and "end_position" in entity_data:
            start = entity_data.get("start_position")
            end = entity_data.get("end_position")
            if start and end and start >= end:
                consistency -= 0.5

        return {"completeness": completeness, "consistency": consistency}

    def _assess_risk_factors(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Assess risk factors for selective validation."""
        risk_factors = {
            "data_sensitivity": 0.0,
            "validation_history": 0.0,
            "data_complexity": 0.0,
            "external_dependencies": 0.0,
        }

        # Data sensitivity (e.g., pathogenic variants are high risk)
        if entity_type == "variant":
            clinical_sig = entity_data.get("clinical_significance", "").lower()
            if "pathogenic" in clinical_sig:
                risk_factors["data_sensitivity"] = 0.9

        # Validation history risk
        entity_key = self._get_entity_key(entity_type, entity_data)
        history = self.validation_history.get(entity_key, [])
        if history:
            recent_failures = sum(1 for h in history[-5:] if h.get("issues", []))
            risk_factors["validation_history"] = min(1.0, recent_failures / 5)

        # Data complexity
        field_count = len(entity_data)
        nested_objects = sum(
            1 for v in entity_data.values() if isinstance(v, (dict, list))
        )
        risk_factors["data_complexity"] = min(
            1.0, (field_count * 0.1 + nested_objects * 0.2)
        )

        # External dependencies (e.g., cross-references)
        if "cross_references" in entity_data:
            xrefs = entity_data["cross_references"]
            if isinstance(xrefs, dict) and xrefs:
                risk_factors["external_dependencies"] = 0.6

        # Overall risk
        risk_factors["overall_risk"] = (
            risk_factors["data_sensitivity"] * 0.4
            + risk_factors["validation_history"] * 0.3
            + risk_factors["data_complexity"] * 0.2
            + risk_factors["external_dependencies"] * 0.1
        )

        return risk_factors

    def _record_validation_history(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
        rules_applied: List[str],
        result: ValidationResult,
        context: Optional[Dict[str, Any]],
    ):
        """Record validation result in history for adaptive learning."""
        entity_key = self._get_entity_key(entity_type, entity_data)

        if entity_key not in self.validation_history:
            self.validation_history[entity_key] = []

        history_entry = {
            "timestamp": datetime.now(),
            "rules_applied": rules_applied,
            "issues": [dict(issue) for issue in result.issues],
            "score": result.score,
            "context": context,
        }

        self.validation_history[entity_key].append(history_entry)

        # Keep only recent history (last 20 entries per entity)
        if len(self.validation_history[entity_key]) > 20:
            self.validation_history[entity_key] = self.validation_history[entity_key][
                -20:
            ]

    def _get_entity_key(self, entity_type: str, entity_data: Dict[str, Any]) -> str:
        """Generate a unique key for an entity."""
        # Use primary identifier if available
        primary_id = (
            entity_data.get("clinvar_id")
            or entity_data.get("hpo_id")
            or entity_data.get("pubmed_id")
            or entity_data.get("symbol")
            or str(hash(str(sorted(entity_data.items()))))
        )

        return f"{entity_type}:{primary_id}"

    def create_validation_profile(
        self,
        name: str,
        entity_types: List[str],
        required_rules: List[str],
        conditional_rules: Optional[Dict[str, Dict[str, Any]]] = None,
        skip_conditions: Optional[List[Dict[str, Any]]] = None,
    ) -> ValidationProfile:
        """
        Create a custom validation profile.

        Args:
            name: Profile name
            entity_types: Entity types this profile applies to
            required_rules: Rules that must always be applied
            conditional_rules: Rules applied based on conditions
            skip_conditions: Conditions for skipping validation

        Returns:
            ValidationProfile object
        """
        profile = ValidationProfile(
            name=name,
            entity_types=entity_types,
            required_rules=required_rules,
            conditional_rules=conditional_rules or {},
            skip_conditions=skip_conditions or [],
            priority_rules=[],  # Can be extended
            quality_threshold=0.8,
        )

        self.profiles[name] = profile
        return profile

    def set_active_profile(self, profile_name: str):
        """Set the active validation profile."""
        if profile_name in self.profiles:
            self.active_profile = profile_name

    def update_confidence_score(
        self, entity_type: str, entity_data: Dict[str, Any], confidence: float
    ):
        """Update confidence score for an entity."""
        entity_key = self._get_entity_key(entity_type, entity_data)
        self.confidence_scores[entity_key] = confidence

    def get_selectivity_stats(self) -> Dict[str, Any]:
        """Get statistics about selective validation performance."""
        return {
            "validations_attempted": self.stats["validations_attempted"],
            "validations_skipped": self.stats["validations_skipped"],
            "rules_applied": self.stats["rules_applied"],
            "rules_skipped": self.stats["rules_skipped"],
            "avg_selectivity": self.stats["avg_selectivity"],
            "skip_rate": (
                self.stats["validations_skipped"]
                / max(1, self.stats["validations_attempted"])
            ),
            "active_profile": self.active_profile,
            "strategy": self.strategy.value,
        }

    def reset_stats(self):
        """Reset performance statistics."""
        self.stats = {
            "validations_attempted": 0,
            "validations_skipped": 0,
            "rules_applied": 0,
            "rules_skipped": 0,
            "avg_selectivity": 0.0,
        }

    def optimize_selectivity(self, target_selectivity: float = 0.7):
        """
        Optimize selectivity based on performance targets.

        Args:
            target_selectivity: Target selectivity ratio (0-1)
        """
        current_selectivity = self.stats["avg_selectivity"]

        if current_selectivity > target_selectivity:
            # Too many rules being applied - increase selectivity
            if self.strategy == SelectionStrategy.ADAPTIVE:
                # Could adjust adaptive thresholds here
                pass
        elif current_selectivity < target_selectivity:
            # Too few rules being applied - decrease selectivity
            if self.strategy == SelectionStrategy.CONFIDENCE_BASED:
                # Could lower confidence thresholds
                pass
