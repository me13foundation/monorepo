"""
Typed structures shared by Dash presentation modules.

These mirror the API contracts exposed by the FastAPI backend so that
callbacks and components can rely on precise typing instead of raw dicts.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import NotRequired, SupportsFloat, SupportsInt

from typing_extensions import TypedDict


class SettingsState(TypedDict):
    """Configuration persisted inside the Dash settings store."""

    api_endpoint: str
    api_key: str
    refresh_interval: int
    page_size: int
    theme: str
    language: str


class ReviewQueueItem(TypedDict, total=False):
    """Item displayed in the curator queue."""

    id: int
    entity_type: str
    entity_id: str
    status: str
    priority: str
    quality_score: float | None
    issues: int
    last_updated: str | None
    confidence_score: NotRequired[float | None]
    phenotype_badges: NotRequired[Sequence[str]]
    summary: NotRequired[str]


class HGVSInfo(TypedDict, total=False):
    genomic: str | None
    protein: str | None
    cdna: str | None


class VariantDetail(TypedDict, total=False):
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
    hgvs: HGVSInfo
    condition: str | None
    review_status: str | None
    created_at: str | None
    updated_at: str | None


class PhenotypeSnapshot(TypedDict, total=False):
    id: int | None
    hpo_id: str
    name: str
    category: str | None
    definition: str | None
    synonyms: Sequence[str]
    frequency: str | None


class EvidenceSnapshot(TypedDict, total=False):
    id: int | None
    evidence_level: str
    evidence_type: str
    description: str
    confidence_score: float | None
    clinical_significance: str | None
    source: str | None
    summary: str | None
    publication_id: int | None
    phenotype_id: int | None
    variant_id: int | None
    reviewed: bool
    reviewer_notes: str | None


class ConflictSummary(TypedDict, total=False):
    kind: str
    severity: str
    message: str
    evidence_ids: Sequence[int]
    suggested_action: str | None


class ProvenanceInfo(TypedDict, total=False):
    sources: Sequence[Mapping[str, object]]


class AuditInfo(TypedDict, total=False):
    last_updated_by: str | None
    last_updated_at: str | None
    pending_actions: Sequence[str]
    total_annotations: int


class CuratedRecordDetail(TypedDict, total=False):
    variant: VariantDetail
    phenotypes: Sequence[PhenotypeSnapshot]
    evidence: Sequence[EvidenceSnapshot]
    conflicts: Sequence[ConflictSummary]
    provenance: ProvenanceInfo | None
    audit: AuditInfo | None


def coerce_queue_items[TQueueMapping: Mapping[str, object]](
    raw_items: Iterable[TQueueMapping],
) -> list[ReviewQueueItem]:
    """
    Convert raw queue payloads into typed queue items.

    Raises:
        ValueError: if required keys are missing or types mismatch.
    """
    items: list[ReviewQueueItem] = []
    for raw in raw_items:
        try:
            item = ReviewQueueItem(
                id=_require_int(raw.get("id"), "id"),
                entity_type=str(raw.get("entity_type", "unknown")),
                entity_id=str(raw.get("entity_id", "unknown")),
                status=str(raw.get("status", "pending")),
                priority=str(raw.get("priority", "medium")),
                quality_score=_maybe_float(raw.get("quality_score")),
                issues=_require_int(raw.get("issues", 0), "issues"),
                last_updated=_maybe_str(raw.get("last_updated")),
            )
        except (KeyError, TypeError, ValueError) as exc:  # pragma: no cover - defensive
            raise ValueError(f"Invalid queue item payload: {raw}") from exc
        items.append(item)
    return items


def coerce_curated_detail[TDetailMapping: Mapping[str, object]](
    payload: TDetailMapping,
) -> CuratedRecordDetail:
    """
    Validate and cast a curated detail response into a typed mapping.

    Raises:
        ValueError: if variant block is missing or malformed.
    """
    if "variant" not in payload:
        raise ValueError("Curated detail payload missing variant data")

    variant_value = payload["variant"]
    if not isinstance(variant_value, Mapping):
        raise ValueError("Curated detail payload must include variant mapping")

    variant_raw = dict(variant_value)
    variant = VariantDetail(
        variant_id=str(variant_raw["variant_id"]),
        chromosome=str(variant_raw["chromosome"]),
        position=int(variant_raw["position"]),
        clinical_significance=str(variant_raw["clinical_significance"]),
        variant_type=str(variant_raw["variant_type"]),
        id=_maybe_int(variant_raw.get("id")),
        clinvar_id=_maybe_str(variant_raw.get("clinvar_id")),
        gene_symbol=_maybe_str(variant_raw.get("gene_symbol")),
        allele_frequency=_maybe_float(variant_raw.get("allele_frequency")),
        gnomad_af=_maybe_float(variant_raw.get("gnomad_af")),
        hgvs=_coerce_hgvs(variant_raw.get("hgvs", {})),
        condition=_maybe_str(variant_raw.get("condition")),
        review_status=_maybe_str(variant_raw.get("review_status")),
        created_at=_maybe_str(variant_raw.get("created_at")),
        updated_at=_maybe_str(variant_raw.get("updated_at")),
    )

    phenotypes_source = _mapping_sequence(payload.get("phenotypes"))
    phenotypes = [
        PhenotypeSnapshot(
            id=_maybe_int(item.get("id")),
            hpo_id=str(item["hpo_id"]),
            name=str(item["name"]),
            category=_maybe_str(item.get("category")),
            definition=_maybe_str(item.get("definition")),
            synonyms=_string_sequence(item.get("synonyms")),
            frequency=_maybe_str(item.get("frequency")),
        )
        for item in phenotypes_source
    ]

    evidence_source = _mapping_sequence(payload.get("evidence"))
    evidence = [
        EvidenceSnapshot(
            id=_maybe_int(item.get("id")),
            evidence_level=str(item["evidence_level"]),
            evidence_type=str(item["evidence_type"]),
            description=str(item["description"]),
            confidence_score=_maybe_float(item.get("confidence_score")),
            clinical_significance=_maybe_str(item.get("clinical_significance")),
            source=_maybe_str(item.get("source")),
            summary=_maybe_str(item.get("summary")),
            publication_id=_maybe_int(item.get("publication_id")),
            phenotype_id=_maybe_int(item.get("phenotype_id")),
            variant_id=_maybe_int(item.get("variant_id")),
            reviewed=bool(item.get("reviewed", False)),
            reviewer_notes=_maybe_str(item.get("reviewer_notes")),
        )
        for item in evidence_source
    ]

    conflicts_source = _mapping_sequence(payload.get("conflicts"))
    conflicts = [
        ConflictSummary(
            kind=str(item.get("kind", "conflict")),
            severity=str(item.get("severity", "medium")),
            message=str(item.get("message", "Conflict detected")),
            evidence_ids=_coerce_int_sequence(item.get("evidence_ids")),
            suggested_action=_maybe_str(item.get("suggested_action")),
        )
        for item in conflicts_source
    ]

    provenance = payload.get("provenance")
    provenance_info = (
        ProvenanceInfo(sources=_mapping_sequence(provenance.get("sources")))
        if isinstance(provenance, Mapping)
        else None
    )

    audit = payload.get("audit")
    audit_info = (
        AuditInfo(
            last_updated_by=_maybe_str(audit.get("last_updated_by")),
            last_updated_at=_maybe_str(audit.get("last_updated_at")),
            pending_actions=_string_sequence(audit.get("pending_actions")),
            total_annotations=_maybe_int(audit.get("total_annotations", 0)) or 0,
        )
        if isinstance(audit, Mapping)
        else None
    )

    return CuratedRecordDetail(
        variant=variant,
        phenotypes=tuple(phenotypes),
        evidence=tuple(evidence),
        conflicts=tuple(conflicts),
        provenance=provenance_info,
        audit=audit_info,
    )


def _maybe_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    if isinstance(value, SupportsFloat):
        try:
            return float(value.__float__())
        except (TypeError, ValueError):
            return None
    return None


def _maybe_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    if isinstance(value, SupportsInt):
        try:
            return int(value.__int__())
        except (TypeError, ValueError):
            return None
    return None


def _maybe_str(value: object) -> str | None:
    return str(value) if value is not None else None


def _coerce_hgvs(value: object) -> HGVSInfo:
    if isinstance(value, Mapping):
        return HGVSInfo(
            genomic=_maybe_str(value.get("genomic")),
            protein=_maybe_str(value.get("protein")),
            cdna=_maybe_str(value.get("cdna")),
        )
    return HGVSInfo()


def _mapping_sequence(value: object) -> Sequence[Mapping[str, object]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        mappings: list[Mapping[str, object]] = []
        for item in value:
            if isinstance(item, Mapping):
                mappings.append(item)
        return tuple(mappings)
    return ()


def _string_sequence(value: object) -> Sequence[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(str(element) for element in value)
    return ()


def _coerce_int_sequence(value: object) -> Sequence[int]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return ()
    integers: list[int] = []
    for candidate in value:
        maybe = _maybe_int(candidate)
        if maybe is not None:
            integers.append(maybe)
    return tuple(integers)


def _require_int(value: object, field: str) -> int:
    maybe = _maybe_int(value)
    if maybe is None:
        raise ValueError(f"Invalid integer for {field}: {value!r}")
    return maybe
