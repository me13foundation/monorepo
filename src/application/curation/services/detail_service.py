"""
Application service that assembles curated record details for reviewers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime as _dt
from typing import TYPE_CHECKING

from sqlalchemy import func, select

from src.application.curation.dto import (
    AuditInfoDTO,
    CuratedRecordDetailDTO,
    EvidenceSnapshotDTO,
    PhenotypeSnapshotDTO,
    ProvenanceDTO,
    VariantDetailDTO,
)
from src.models.database.audit import AuditLog

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.orm import Session

    from src.application.curation import conflict_detector, repositories  # noqa: F401
    from src.application.services import (
        EvidenceApplicationService,
        VariantApplicationService,
    )

if TYPE_CHECKING:
    from src.domain.entities.evidence import Evidence
    from src.domain.entities.phenotype import Phenotype
    from src.domain.entities.variant import Variant
    from src.domain.repositories.phenotype_repository import PhenotypeRepository

    # AuditLog imported at runtime above


@dataclass
class CurationDetailService:
    """
    Aggregate clinical context for curator workflows.

    The service stitches together variant, phenotype, evidence, and conflict
    information into a single DTO that the FastAPI layer can serialize.
    """

    variant_service: VariantApplicationService
    evidence_service: EvidenceApplicationService
    phenotype_repository: PhenotypeRepository
    conflict_detector: conflict_detector.ConflictDetector
    review_repository: repositories.review_repository.ReviewRepository
    db_session: Session

    def get_detail(self, entity_type: str, entity_id: str) -> CuratedRecordDetailDTO:
        """
        Retrieve detailed context for the requested entity.

        Currently supports variant entities. Other entity types will raise
        `ValueError` until implemented.
        """
        normalized_type = entity_type.lower()
        if normalized_type in {"variant", "variants"}:
            return self._build_variant_detail(entity_id)

        message = f"Curation detail not supported for '{entity_type}'"
        raise ValueError(message)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _build_variant_detail(self, entity_id: str) -> CuratedRecordDetailDTO:
        variant, evidence_records = self._load_variant_and_evidence(entity_id)
        if variant is None:
            message = f"Variant '{entity_id}' not found"
            raise ValueError(message)

        variant_detail = self._to_variant_dto(variant)
        evidence_dtos = self._to_evidence_dtos(evidence_records)
        phenotype_dtos = self._load_phenotype_dtos(variant)
        conflict_dtos = tuple(
            self.conflict_detector.summarize_conflicts(variant, evidence_records),
        )

        provenance: ProvenanceDTO | None = None
        audit = self._load_audit_info(
            entity_type="variant",
            entity_identifier=entity_id,
            variant=variant,
        )

        return CuratedRecordDetailDTO(
            variant=variant_detail,
            phenotypes=phenotype_dtos,
            evidence=evidence_dtos,
            conflicts=conflict_dtos,
            provenance=provenance,
            audit=audit,
        )

    def _load_variant_and_evidence(
        self,
        entity_id: str,
    ) -> tuple[Variant | None, Sequence[Evidence]]:
        variant: Variant | None = None
        evidence: Sequence[Evidence] = ()

        variant_db_id: int | None = None

        if entity_id.isdigit():
            variant_db_id = int(entity_id)
            variant = self.variant_service.get_variant_with_evidence(variant_db_id)

        if variant is None:
            # Attempt lookup by public variant identifier (e.g., VCV)
            variant = self.variant_service.get_variant_by_id(entity_id)
            if variant and variant.id:
                variant_db_id = variant.id
                # Reload to ensure evidence summaries are attached
                variant = self.variant_service.get_variant_with_evidence(variant.id)

        if variant_db_id is None and variant is not None and variant.id is not None:
            variant_db_id = variant.id

        if variant_db_id is not None:
            evidence = self.evidence_service.get_evidence_by_variant(variant_db_id)

        return variant, list(evidence)

    @staticmethod
    def _to_variant_dto(variant: Variant) -> VariantDetailDTO:
        return VariantDetailDTO(
            id=variant.id,
            variant_id=variant.variant_id,
            clinvar_id=variant.clinvar_id,
            gene_symbol=variant.gene_symbol,
            chromosome=variant.chromosome,
            position=variant.position,
            clinical_significance=variant.clinical_significance,
            variant_type=variant.variant_type,
            allele_frequency=variant.allele_frequency,
            gnomad_af=variant.gnomad_af,
            hgvs={
                "genomic": variant.hgvs_genomic,
                "protein": variant.hgvs_protein,
                "cdna": variant.hgvs_cdna,
            },
            condition=variant.condition,
            review_status=variant.review_status,
            created_at=variant.created_at,
            updated_at=variant.updated_at,
        )

    def _to_evidence_dtos(
        self,
        evidence_records: Sequence[Evidence],
    ) -> tuple[EvidenceSnapshotDTO, ...]:
        return tuple(
            EvidenceSnapshotDTO(
                id=ev.id,
                evidence_level=ev.evidence_level.value,
                evidence_type=ev.evidence_type,
                description=ev.description,
                confidence_score=ev.confidence.score,
                clinical_significance=getattr(ev, "clinical_significance", None),
                source=getattr(ev, "source", None),
                summary=ev.summary,
                publication_id=ev.publication_id,
                phenotype_id=ev.phenotype_id,
                variant_id=ev.variant_id,
                reviewed=ev.reviewed,
                reviewer_notes=ev.reviewer_notes,
            )
            for ev in evidence_records
        )

    def _load_phenotype_dtos(
        self,
        variant: Variant,
    ) -> tuple[PhenotypeSnapshotDTO, ...]:
        if variant.id is None:
            return ()

        phenotypes: Sequence[Phenotype] = (
            self.phenotype_repository.find_by_variant_associations(variant.id)
        )

        if not phenotypes:
            return ()

        return tuple(self._to_phenotype_dto(phenotype) for phenotype in phenotypes)

    def _to_phenotype_dto(self, phenotype: Phenotype) -> PhenotypeSnapshotDTO:
        identifier = phenotype.identifier
        return PhenotypeSnapshotDTO(
            id=phenotype.id,
            hpo_id=identifier.hpo_id,
            name=phenotype.name,
            category=phenotype.category,
            definition=phenotype.definition,
            synonyms=phenotype.synonyms,
            frequency=phenotype.frequency_in_med13,
        )

    def _load_audit_info(
        self,
        entity_type: str,
        entity_identifier: str,
        variant: Variant | None,
    ) -> AuditInfoDTO | None:
        primary_record = self.review_repository.find_by_entity(
            self.db_session,
            entity_type,
            entity_identifier,
        )

        fallback_identifier = variant.variant_id if variant is not None else None
        if (
            primary_record is None
            and fallback_identifier
            and fallback_identifier != entity_identifier
        ):
            primary_record = self.review_repository.find_by_entity(
                self.db_session,
                entity_type,
                fallback_identifier,
            )
            if primary_record is not None:
                entity_identifier = fallback_identifier

        if primary_record is None:
            return None

        stmt = select(func.count(AuditLog.id)).where(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_identifier,
        )
        annotation_count = int(self.db_session.execute(stmt).scalar_one())

        pr = primary_record  # alias
        pending_actions: tuple[str, ...] = (
            f"Status: {pr.get('status', '')}",
            f"Priority: {pr.get('priority', '')}",
            f"Issues: {pr.get('issues', 0)}",
        )

        last_updated_raw = primary_record.get("last_updated")
        last_updated_typed: _dt | None
        if isinstance(last_updated_raw, _dt):
            last_updated_typed = last_updated_raw
        else:
            last_updated_typed = None

        return AuditInfoDTO(
            last_updated_by=None,
            last_updated_at=last_updated_typed,
            pending_actions=pending_actions,
            total_annotations=annotation_count,
        )


__all__ = ["CurationDetailService"]
