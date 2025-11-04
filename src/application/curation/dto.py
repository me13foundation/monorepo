"""
Typed data transfer objects for the curator-facing detail workflow.

These lightweight dataclasses keep the Dash presentation layer decoupled
from SQLAlchemy models and domain entities while retaining rich typing for
back-end orchestration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable, Mapping, Optional


@dataclass(frozen=True)
class VariantDetailDTO:
    """Clinical context for a variant under review."""

    id: Optional[int]
    variant_id: str
    clinvar_id: Optional[str]
    gene_symbol: Optional[str]
    chromosome: str
    position: int
    clinical_significance: str
    variant_type: str
    allele_frequency: Optional[float]
    gnomad_af: Optional[float]
    hgvs: Mapping[str, Optional[str]] = field(default_factory=dict)
    condition: Optional[str] = None
    review_status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass(frozen=True)
class PhenotypeSnapshotDTO:
    """Simplified phenotype representation for curator context."""

    id: Optional[int]
    hpo_id: str
    name: str
    category: Optional[str]
    definition: Optional[str]
    synonyms: tuple[str, ...] = ()
    frequency: Optional[str] = None


@dataclass(frozen=True)
class EvidenceSnapshotDTO:
    """Structured evidence excerpt surfaced to curators."""

    id: Optional[int]
    evidence_level: str
    evidence_type: str
    description: str
    confidence_score: Optional[float]
    clinical_significance: Optional[str]
    source: Optional[str] = None
    summary: Optional[str] = None
    publication_id: Optional[int] = None
    phenotype_id: Optional[int] = None
    variant_id: Optional[int] = None
    reviewed: bool = False
    reviewer_notes: Optional[str] = None


@dataclass(frozen=True)
class ConflictSummaryDTO:
    """Conflict metadata highlighted in the curation interface."""

    kind: str
    severity: str
    message: str
    evidence_ids: tuple[int, ...] = ()
    suggested_action: Optional[str] = None


@dataclass(frozen=True)
class ProvenanceDTO:
    """High-level provenance summary (optional for initial rollout)."""

    sources: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class AuditInfoDTO:
    """Audit context for curator actions."""

    last_updated_by: Optional[str] = None
    last_updated_at: Optional[datetime] = None
    pending_actions: tuple[str, ...] = ()
    total_annotations: int = 0


@dataclass(frozen=True)
class CuratedRecordDetailDTO:
    """
    Aggregate payload consumed by the Dash interface.

    The shape mirrors the contract described in docs/curator.md and can be
    serialized directly for the API response.
    """

    variant: VariantDetailDTO
    phenotypes: tuple[PhenotypeSnapshotDTO, ...]
    evidence: tuple[EvidenceSnapshotDTO, ...]
    conflicts: tuple[ConflictSummaryDTO, ...]
    provenance: Optional[ProvenanceDTO] = None
    audit: Optional[AuditInfoDTO] = None

    def to_serializable(self) -> Mapping[str, Any]:
        """Convert the DTO to a plain mapping suitable for JSON responses."""

        def _serialize_iter(items: Iterable[Any]) -> list[Any]:
            return [
                item.__dict__ if hasattr(item, "__dict__") else item for item in items
            ]

        payload: dict[str, Any] = {
            "variant": self.variant.__dict__,
            "phenotypes": _serialize_iter(self.phenotypes),
            "evidence": _serialize_iter(self.evidence),
            "conflicts": _serialize_iter(self.conflicts),
        }

        if self.provenance is not None:
            payload["provenance"] = self.provenance.__dict__

        if self.audit is not None:
            payload["audit"] = self.audit.__dict__

        return payload


__all__ = [
    "VariantDetailDTO",
    "PhenotypeSnapshotDTO",
    "EvidenceSnapshotDTO",
    "ConflictSummaryDTO",
    "ProvenanceDTO",
    "AuditInfoDTO",
    "CuratedRecordDetailDTO",
]
