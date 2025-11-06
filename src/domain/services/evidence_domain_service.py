"""
Evidence domain service - pure business logic for evidence entities.

Encapsulates evidence-specific business rules, conflict detection,
and confidence scoring logic without infrastructure dependencies.
"""

from collections import Counter
from typing import Any

from src.domain.entities.evidence import Evidence
from src.domain.services.base import DomainService
from src.domain.value_objects.confidence import Confidence, EvidenceLevel
from src.type_definitions.domain import EvidenceDerivedProperties


class EvidenceDomainService(DomainService):
    """
    Domain service for Evidence business logic.

    Contains pure business rules for evidence validation, conflict detection,
    confidence scoring, and evidence aggregation.
    """

    def validate_business_rules(
        self,
        entity: Evidence,
        _operation: str,
        _context: dict[str, Any] | None = None,
    ) -> list[str]:
        """
        Validate evidence business rules.

        Args:
            entity: Evidence entity to validate
            operation: Operation being performed
            context: Additional validation context

        Returns:
            List of validation error messages
        """
        errors = []

        # Confidence score validation
        if entity.confidence.score is not None and not (
            0.0 <= entity.confidence.score <= 1.0
        ):
            errors.append("Confidence score must be between 0.0 and 1.0")

        # Evidence level validation
        if not self._is_valid_evidence_level(entity.evidence_level):
            errors.append(f"Invalid evidence level: {entity.evidence_level.value}")

        # Required fields based on evidence type
        if not entity.evidence_type:
            errors.append("Evidence type is required")

        if not entity.description:
            errors.append("Evidence description is required")

        return errors

    def apply_business_logic(self, entity: Evidence, operation: str) -> Evidence:
        """
        Apply evidence business logic transformations.

        Args:
            entity: Evidence entity to transform
            operation: Operation being performed

        Returns:
            Transformed evidence entity
        """
        # Auto-calculate confidence score if not provided
        if operation in ("create", "update"):
            entity.update_confidence(
                Confidence.from_score(self._calculate_default_confidence_score(entity)),
            )

        # Normalize evidence level
        entity.evidence_level = self._normalize_evidence_level(entity.evidence_level)

        return entity

    def calculate_derived_properties(self, entity: Evidence) -> dict[str, Any]:
        """
        Calculate derived properties for evidence.

        Args:
            entity: Evidence entity

        Returns:
            Dictionary of derived properties
        """
        # Determine confidence category
        confidence_score = entity.confidence.score
        high_threshold = 0.8
        medium_threshold = 0.6
        if confidence_score >= high_threshold:
            confidence_category = "high"
        elif confidence_score >= medium_threshold:
            confidence_category = "medium"
        else:
            confidence_category = "low"

        # Determine evidence strength based on level
        evidence_level = entity.evidence_level
        if evidence_level == EvidenceLevel.DEFINITIVE:
            evidence_strength = "definitive"
        elif evidence_level == EvidenceLevel.STRONG:
            evidence_strength = "strong"
        elif evidence_level == EvidenceLevel.MODERATE:
            evidence_strength = "moderate"
        else:
            evidence_strength = "supporting"

        # Check for publication reference (simplified - would need relationship)
        has_publication = False

        # Check for functional data based on evidence type
        has_functional_data = entity.evidence_type in [
            "functional_study",
            "biochemical",
            "animal_model",
        ]

        # Calculate data completeness score
        required_fields = [
            entity.variant_id,
            entity.phenotype_id,
            entity.evidence_level,
        ]
        optional_fields = [entity.description]
        required_present = sum(1 for field in required_fields if field is not None)
        optional_present = sum(1 for field in optional_fields if field is not None)
        data_completeness_score = (required_present + optional_present * 0.5) / (
            len(required_fields) + len(optional_fields) * 0.5
        )

        # Calculate reliability score based on evidence level and confidence
        reliability_score = confidence_score * (
            1.0
            if evidence_level in [EvidenceLevel.DEFINITIVE, EvidenceLevel.STRONG]
            else 0.8
        )

        # Create typed result for internal type safety
        result = EvidenceDerivedProperties(
            confidence_category=confidence_category,
            evidence_strength=evidence_strength,
            has_publication=has_publication,
            has_functional_data=has_functional_data,
            data_completeness_score=data_completeness_score,
            reliability_score=reliability_score,
        )

        # Return as dict for base class compatibility
        return result.__dict__

    def detect_evidence_conflicts(
        self,
        evidence_list: list[Evidence],
    ) -> list[dict[str, Any]]:
        """
        Detect conflicts between evidence records.

        Args:
            evidence_list: List of evidence records to analyze

        Returns:
            List of conflict descriptions with details
        """
        conflicts: list[dict[str, Any]] = []

        min_for_conflict = 2
        if len(evidence_list) < min_for_conflict:
            return conflicts

        # Check for clinical significance conflicts
        significance_conflicts = self._detect_significance_conflicts(evidence_list)
        conflicts.extend(significance_conflicts)

        # Check for frequency conflicts
        frequency_conflicts = self._detect_frequency_conflicts(evidence_list)
        conflicts.extend(frequency_conflicts)

        # Check for functional study conflicts
        functional_conflicts = self._detect_functional_study_conflicts(evidence_list)
        conflicts.extend(functional_conflicts)

        return conflicts

    def calculate_evidence_consensus(
        self,
        evidence_list: list[Evidence],
    ) -> dict[str, Any]:
        """
        Calculate consensus from multiple evidence records.

        Args:
            evidence_list: List of evidence records

        Returns:
            Consensus information
        """
        if not evidence_list:
            return {
                "consensus_significance": None,
                "confidence": 0.0,
                "agreement_score": 0.0,
            }

        # Extract clinical significances
        significances = [
            ev.clinical_significance
            for ev in evidence_list
            if hasattr(ev, "clinical_significance") and ev.clinical_significance
        ]

        if not significances:
            return {
                "consensus_significance": None,
                "confidence": 0.0,
                "agreement_score": 0.0,
            }

        # Find most common significance
        most_common_sig, count = Counter(significances).most_common(1)[0]

        agreement_score = count / len(significances)
        confidence = self._calculate_consensus_confidence(
            evidence_list,
            agreement_score,
        )

        return {
            "consensus_significance": most_common_sig,
            "confidence": confidence,
            "agreement_score": agreement_score,
            "total_evidence": len(evidence_list),
            "evidence_levels": list(
                {ev.evidence_level for ev in evidence_list if ev.evidence_level},
            ),
        }

    def score_evidence_quality(self, evidence: Evidence) -> float:
        """
        Score the quality of an evidence record.

        Args:
            evidence: Evidence record to score

        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.5  # Base score

        # Evidence level factor
        level_scores = {
            "definitive": 1.0,
            "strong": 0.8,
            "supporting": 0.6,
            "limited": 0.4,
            "conflicting": 0.2,
        }
        level_score = level_scores.get(
            evidence.evidence_level.lower() if evidence.evidence_level else "",
            0.3,
        )
        score = (score + level_score) / 2

        # Confidence score factor
        if evidence.confidence.score is not None:
            score = (score + evidence.confidence.score) / 2

        # Recency factor (simplified)
        if hasattr(evidence, "publication_date") and evidence.publication_date:
            # Would calculate based on publication date
            pass

        return score

    def _calculate_default_confidence_score(self, evidence: Evidence) -> float:
        """Calculate default confidence score based on evidence characteristics."""
        base_score = 0.5

        # Adjust based on evidence level
        level_multipliers = {
            "definitive": 1.0,
            "strong": 0.9,
            "supporting": 0.7,
            "limited": 0.5,
            "conflicting": 0.3,
        }

        level = evidence.evidence_level.value.lower()
        multiplier = level_multipliers.get(level, 0.5)

        return base_score * multiplier

    def _normalize_evidence_level(self, level: EvidenceLevel) -> EvidenceLevel:
        """Normalize evidence level to standard terms."""
        level_lower = level.value.lower().strip()

        # Map variations to standard terms
        mappings = {
            "definitive": "definitive",
            "very strong": "strong",
            "strong": "strong",
            "moderate": "supporting",
            "supporting": "supporting",
            "limited": "limited",
            "weak": "limited",
            "conflicting": "conflicting",
            "discordant": "conflicting",
        }

        normalized = mappings.get(level_lower, level_lower)
        return EvidenceLevel(normalized)

    def _is_valid_evidence_level(self, level: EvidenceLevel) -> bool:
        """Validate evidence level."""
        valid_levels = {
            EvidenceLevel.DEFINITIVE,
            EvidenceLevel.STRONG,
            EvidenceLevel.MODERATE,
            EvidenceLevel.SUPPORTING,
            EvidenceLevel.WEAK,
            EvidenceLevel.DISPROVEN,
        }
        return level in valid_levels

    def _calculate_evidence_strength(self, evidence: Evidence) -> float:
        """Calculate evidence strength score."""
        strength = 0.5

        # Evidence level contribution
        level_strengths: dict[EvidenceLevel, float] = {
            EvidenceLevel.DEFINITIVE: 1.0,
            EvidenceLevel.STRONG: 0.8,
            EvidenceLevel.MODERATE: 0.6,
            EvidenceLevel.SUPPORTING: 0.5,
            EvidenceLevel.WEAK: 0.3,
            EvidenceLevel.DISPROVEN: 0.1,
        }

        strength = level_strengths.get(evidence.evidence_level, 0.5)

        # Confidence score contribution
        if evidence.confidence.score is not None:
            strength = (strength + evidence.confidence.score) / 2

        return strength

    def _determine_quality_tier(self, evidence: Evidence) -> str:
        """Determine evidence quality tier."""
        strength = self._calculate_evidence_strength(evidence)

        high = 0.8
        medium = 0.6
        low = 0.4
        if strength >= high:
            return "high"
        if strength >= medium:
            return "medium"
        if strength >= low:
            return "low"
        return "very_low"

    def _is_recent_evidence(self, _evidence: Evidence) -> bool:
        """Determine if evidence is recent (simplified implementation)."""
        # Would check publication date - simplified for now
        return True

    def _detect_significance_conflicts(
        self,
        evidence_list: list[Evidence],
    ) -> list[dict[str, Any]]:
        """Detect clinical significance conflicts."""
        conflicts = []

        significances = [
            (ev.clinical_significance.lower(), ev.id)
            for ev in evidence_list
            if hasattr(ev, "clinical_significance") and ev.clinical_significance
        ]

        # Check for pathogenic vs benign conflicts
        pathogenic = [evid_id for sig, evid_id in significances if "pathogenic" in sig]
        benign = [evid_id for sig, evid_id in significances if "benign" in sig]

        if pathogenic and benign:
            conflicts.append(
                {
                    "type": "significance_conflict",
                    "description": f"Conflicting clinical significance: {len(pathogenic)} pathogenic vs {len(benign)} benign",
                    "severity": "high",
                    "evidence_ids": pathogenic + benign,
                },
            )

        return conflicts

    def _detect_frequency_conflicts(
        self,
        evidence_list: list[Evidence],
    ) -> list[dict[str, Any]]:
        """Detect frequency conflicts."""
        conflicts = []

        frequencies: list[tuple[float, int | None]] = [
            (ev.allele_frequency, ev.id)
            for ev in evidence_list
            if hasattr(ev, "allele_frequency") and ev.allele_frequency is not None
        ]

        if len(frequencies) > 1:
            freq_values = [freq for freq, _ in frequencies]
            freq_range = max(freq_values) - min(freq_values)

            threshold = 0.05
            if freq_range > threshold:
                conflicts.append(
                    {
                        "type": "frequency_conflict",
                        "description": f"Large frequency discrepancy: {freq_range:.4f} across {len(frequencies)} sources",
                        "severity": "medium",
                        "evidence_ids": [evid_id for _, evid_id in frequencies],
                    },
                )

        return conflicts

    def _detect_functional_study_conflicts(
        self,
        _evidence_list: list[Evidence],
    ) -> list[dict[str, Any]]:
        """Detect functional study conflicts (placeholder)."""
        # Would implement logic for functional study conflicts
        return []

    def _calculate_consensus_confidence(
        self,
        evidence_list: list[Evidence],
        agreement_score: float,
    ) -> float:
        """Calculate confidence in consensus."""
        base_confidence = agreement_score

        # Boost confidence based on evidence quality and quantity
        quality_boost = min(len(evidence_list) * 0.1, 0.3)
        high_quality_threshold = 0.7
        high_quality_count = sum(
            1
            for ev in evidence_list
            if self.score_evidence_quality(ev) > high_quality_threshold
        )
        quality_boost += (high_quality_count / len(evidence_list)) * 0.2

        return min(base_confidence + quality_boost, 1.0)


__all__ = ["EvidenceDomainService"]
