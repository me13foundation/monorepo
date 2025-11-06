"""
Clinical Significance Assessment Domain Service.

Encapsulates business logic for assessing clinical significance from evidence.
"""

from dataclasses import dataclass

from src.domain.entities.evidence import Evidence
from src.domain.entities.variant import ClinicalSignificance
from src.domain.value_objects.confidence import Confidence


@dataclass
class SignificanceAssessment:
    """Result of clinical significance assessment."""

    final_significance: str
    confidence_score: Confidence
    evidence_count: int
    assessment_method: str


class ClinicalSignificanceService:
    """
    Domain service for clinical significance assessment.

    This service encapsulates business logic for determining clinical significance
    from multiple evidence sources.
    """

    @staticmethod
    def assess_significance(evidence_list: list[Evidence]) -> SignificanceAssessment:
        """
        Assess clinical significance from evidence.

        Args:
            evidence_list: List of evidence records

        Returns:
            Significance assessment result
        """
        if not evidence_list:
            return SignificanceAssessment(
                final_significance=ClinicalSignificance.NOT_PROVIDED,
                confidence_score=Confidence.from_score(0.0),
                evidence_count=0,
                assessment_method="no_evidence",
            )

        # Simple majority vote
        significance_counts: dict[str, int] = {}

        for evidence in evidence_list:
            sig_raw = getattr(evidence, "clinical_significance", None)
            if sig_raw is None:
                sig = ClinicalSignificance.NOT_PROVIDED
            else:
                try:
                    sig = ClinicalSignificance.validate(sig_raw)
                except ValueError:
                    sig = ClinicalSignificance.NOT_PROVIDED
            significance_counts[sig] = significance_counts.get(sig, 0) + 1

        # Find most common significance
        most_common_sig, most_common_count = max(
            significance_counts.items(),
            key=lambda x: x[1],
        )

        # Calculate confidence based on consensus
        total_evidence = len(evidence_list)
        consensus_ratio = most_common_count / total_evidence

        return SignificanceAssessment(
            final_significance=most_common_sig,
            confidence_score=Confidence.from_score(consensus_ratio),
            evidence_count=total_evidence,
            assessment_method="majority_vote",
        )
