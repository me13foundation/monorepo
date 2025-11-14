"""
Typed data transfer objects for the curator-facing detail workflow.

These lightweight dataclasses keep the Dash presentation layer decoupled
from SQLAlchemy models and domain entities while retaining rich typing for
back-end orchestration.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import cast

from src.type_definitions.common import JSONObject, JSONValue

SerializableMapping = Mapping[str, JSONValue]


@dataclass(frozen=True)
class VariantDetailDTO:
    """Clinical context for a variant under review."""

    id: int | None
    variant_id: str
    clinvar_id: str | None
    gene_symbol: str | None
    chromosome: str
    position: int
    clinical_significance: str
    variant_type: str
    allele_frequency: float | None
    gnomad_af: float | None
    hgvs: Mapping[str, str | None] = field(default_factory=dict)
    condition: str | None = None
    review_status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class PhenotypeSnapshotDTO:
    """Simplified phenotype representation for curator context."""

    id: int | None
    hpo_id: str
    name: str
    category: str | None
    definition: str | None
    synonyms: tuple[str, ...] = ()
    frequency: str | None = None


@dataclass(frozen=True)
class EvidenceSnapshotDTO:
    """Structured evidence excerpt surfaced to curators."""

    id: int | None
    evidence_level: str
    evidence_type: str
    description: str
    confidence_score: float | None
    clinical_significance: str | None
    source: str | None = None
    summary: str | None = None
    publication_id: int | None = None
    phenotype_id: int | None = None
    variant_id: int | None = None
    reviewed: bool = False
    reviewer_notes: str | None = None


@dataclass(frozen=True)
class ConflictSummaryDTO:
    """Conflict metadata highlighted in the curation interface."""

    kind: str
    severity: str
    message: str
    evidence_ids: tuple[int, ...] = ()
    suggested_action: str | None = None


@dataclass(frozen=True)
class ProvenanceDTO:
    """High-level provenance summary (optional for initial rollout)."""

    sources: tuple[SerializableMapping, ...] = ()


@dataclass(frozen=True)
class AuditInfoDTO:
    """Audit context for curator actions."""

    last_updated_by: str | None = None
    last_updated_at: datetime | None = None
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
    provenance: ProvenanceDTO | None = None
    audit: AuditInfoDTO | None = None

    def to_serializable(self) -> JSONObject:
        """Convert the DTO to a plain mapping suitable for JSON responses."""

        def _serialize_iter(items: Iterable[object]) -> list[JSONValue]:
            return [
                cast(
                    "JSONValue",
                    (
                        dict(item.__dict__)
                        if hasattr(item, "__dict__")
                        else item  # pragma: no cover - defensive branch
                    ),
                )
                for item in items
            ]

        variant_payload = dict(self.variant.__dict__)

        if isinstance(self.variant.created_at, datetime):
            variant_payload["created_at"] = self.variant.created_at.isoformat()
        if isinstance(self.variant.updated_at, datetime):
            variant_payload["updated_at"] = self.variant.updated_at.isoformat()

        payload: JSONObject = {
            "variant": cast("JSONObject", variant_payload),
            "phenotypes": _serialize_iter(self.phenotypes),
            "evidence": _serialize_iter(self.evidence),
            "conflicts": _serialize_iter(self.conflicts),
        }

        if self.provenance is not None:
            payload["provenance"] = {
                "sources": [
                    dict(source) if isinstance(source, Mapping) else source
                    for source in self.provenance.sources
                ],
            }

        if self.audit is not None:
            audit_dict = self.audit.__dict__.copy()
            if isinstance(self.audit.last_updated_at, datetime):
                audit_dict["last_updated_at"] = self.audit.last_updated_at.isoformat()
            payload["audit"] = cast("JSONObject", audit_dict)

        return payload


__all__ = [
    "AuditInfoDTO",
    "ConflictSummaryDTO",
    "CuratedRecordDetailDTO",
    "EvidenceSnapshotDTO",
    "PhenotypeSnapshotDTO",
    "ProvenanceDTO",
    "VariantDetailDTO",
]
