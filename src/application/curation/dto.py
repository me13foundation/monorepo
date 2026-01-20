"""
Typed data transfer objects for the curator-facing detail workflow.

These lightweight dataclasses keep the curation presentation layer decoupled
from SQLAlchemy models and domain entities while retaining rich typing for
back-end orchestration.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.type_definitions.common import JSONObject, JSONValue
from src.type_definitions.json_utils import to_json_value

if TYPE_CHECKING:
    from datetime import datetime

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
    Aggregate payload consumed by the curation interface.

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

        def _serialize_object(value: object) -> JSONObject:
            serialized = to_json_value(value)
            if not isinstance(serialized, dict):
                message = "Serializable DTOs must produce JSON objects"
                raise TypeError(message)
            return serialized

        def _serialize_iter(items: Iterable[object]) -> list[JSONValue]:
            json_items: list[JSONValue] = []
            for item in items:
                json_object = _serialize_object(item)
                json_items.append(json_object)
            return json_items

        variant_payload = _serialize_object(self.variant)
        payload: JSONObject = {
            "variant": variant_payload,
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
            payload["audit"] = _serialize_object(self.audit)

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
