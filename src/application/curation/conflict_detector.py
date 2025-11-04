"""
Conflict detection utilities tailored for the curator workflow.

Wraps existing domain services to produce structured summaries that the
front-end can render without embedding business logic in Dash callbacks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from src.application.curation.dto import ConflictSummaryDTO
from src.domain.entities.evidence import Evidence
from src.domain.entities.variant import Variant
from src.domain.services.evidence_domain_service import EvidenceDomainService
from src.domain.services.variant_domain_service import VariantDomainService


@dataclass
class ConflictDetector:
    """
    High-level conflict detector orchestrating domain services.

    Generates structured summaries for the curation interface.
    """

    variant_domain_service: VariantDomainService
    evidence_domain_service: EvidenceDomainService

    def summarize_conflicts(
        self, variant: Variant, evidence: Sequence[Evidence]
    ) -> List[ConflictSummaryDTO]:
        """
        Produce conflict summaries for a variant and its evidence set.

        Args:
            variant: Domain variant entity under review
            evidence: Evidence records associated with the variant

        Returns:
            List of structured conflict summaries
        """
        if not evidence:
            return []

        summaries: list[ConflictSummaryDTO] = []

        # Variant-level heuristics (string descriptions) → normalize
        variant_conflicts = self.variant_domain_service.detect_evidence_conflicts(
            variant, list(evidence)
        )
        summaries.extend(
            ConflictSummaryDTO(
                kind="variant_clinical_conflict",
                severity="high" if "pathogenic" in message.lower() else "medium",
                message=message,
            )
            for message in variant_conflicts
        )

        # Evidence-level structured conflicts
        evidence_conflicts = self.evidence_domain_service.detect_evidence_conflicts(
            list(evidence)
        )
        for conflict in evidence_conflicts:
            conflict_type = conflict.get("type", "evidence_conflict")
            description = conflict.get("description", "Conflict detected")
            severity = conflict.get("severity", "medium")

            evidence_ids: Iterable[int] = (
                conflict.get("evidence_ids", []) if conflict else []
            )

            summaries.append(
                ConflictSummaryDTO(
                    kind=str(conflict_type),
                    severity=str(severity),
                    message=str(description),
                    evidence_ids=tuple(
                        int(eid) for eid in evidence_ids if eid is not None
                    ),
                )
            )

        # De-duplicate identical conflicts while preserving severity ordering
        deduped: dict[str, ConflictSummaryDTO] = {}
        severity_rank = {"high": 3, "medium": 2, "low": 1}

        for summary in summaries:
            key = f"{summary.kind}:{summary.message}"
            existing = deduped.get(key)
            if existing is None:
                deduped[key] = summary
                continue

            # Keep the higher severity entry and merge evidence IDs
            existing_rank = severity_rank.get(existing.severity, 0)
            incoming_rank = severity_rank.get(summary.severity, 0)
            if incoming_rank > existing_rank:
                deduped[key] = ConflictSummaryDTO(
                    kind=summary.kind,
                    severity=summary.severity,
                    message=summary.message,
                    evidence_ids=tuple(
                        sorted(set(existing.evidence_ids + summary.evidence_ids))
                    ),
                )
            else:
                deduped[key] = ConflictSummaryDTO(
                    kind=existing.kind,
                    severity=existing.severity,
                    message=existing.message,
                    evidence_ids=tuple(
                        sorted(set(existing.evidence_ids + summary.evidence_ids))
                    ),
                )

        return list(deduped.values())


__all__ = ["ConflictDetector"]
