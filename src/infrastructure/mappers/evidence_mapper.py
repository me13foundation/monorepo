from __future__ import annotations

from datetime import date
from typing import Optional, Sequence, cast

from src.domain.entities.evidence import Evidence, EvidenceType
from src.domain.entities.variant import VariantSummary
from src.domain.value_objects.confidence import Confidence, EvidenceLevel
from src.domain.value_objects.identifiers import (
    PhenotypeIdentifier,
    PublicationIdentifier,
    VariantIdentifier,
)
from src.models.database.evidence import EvidenceModel
from src.models.database.phenotype import PhenotypeModel
from src.models.database.publication import PublicationModel
from src.models.database.variant import VariantModel


class EvidenceMapper:
    """Maps between SQLAlchemy EvidenceModel and domain Evidence entities."""

    @staticmethod
    def to_domain(model: EvidenceModel) -> Evidence:
        confidence = Confidence.from_score(
            model.confidence_score,
            sample_size=model.sample_size,
            study_count=None,
            peer_reviewed=model.reviewed,
        )
        evidence_level = EvidenceLevel(model.evidence_level)
        confidence = confidence.update_level(evidence_level)

        evidence = Evidence(
            variant_id=model.variant_id,
            phenotype_id=model.phenotype_id,
            description=model.description,
            summary=model.summary,
            evidence_level=evidence_level,
            evidence_type=model.evidence_type or EvidenceType.LITERATURE_REVIEW,
            confidence=confidence,
            publication_id=model.publication_id,
            quality_score=model.quality_score,
            sample_size=model.sample_size,
            study_type=model.study_type,
            statistical_significance=model.statistical_significance,
            reviewed=model.reviewed,
            review_date=cast(Optional[date], model.review_date),
            reviewer_notes=model.reviewer_notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
            id=model.id,
        )

        if hasattr(model, "variant") and isinstance(model.variant, VariantModel):
            evidence.variant_identifier = EvidenceMapper._variant_identifier(
                model.variant
            )
            evidence.variant_summary = VariantSummary(
                variant_id=model.variant.variant_id,
                clinvar_id=model.variant.clinvar_id,
                chromosome=model.variant.chromosome,
                position=model.variant.position,
                clinical_significance=model.variant.clinical_significance,
            )

        if hasattr(model, "phenotype") and isinstance(model.phenotype, PhenotypeModel):
            evidence.phenotype_identifier = PhenotypeIdentifier(
                hpo_id=model.phenotype.hpo_id,
                hpo_term=model.phenotype.hpo_term,
            )

        if hasattr(model, "publication") and isinstance(
            model.publication, PublicationModel
        ):
            evidence.publication_identifier = PublicationIdentifier(
                pubmed_id=model.publication.pubmed_id,
                pmc_id=model.publication.pmc_id,
                doi=model.publication.doi,
            )

        return evidence

    @staticmethod
    def to_model(
        entity: Evidence, model: Optional[EvidenceModel] = None
    ) -> EvidenceModel:
        target = model or EvidenceModel()
        target.variant_id = entity.variant_id
        target.phenotype_id = entity.phenotype_id
        target.publication_id = entity.publication_id
        target.evidence_level = entity.evidence_level.value
        target.evidence_type = entity.evidence_type
        target.description = entity.description
        target.summary = entity.summary
        target.confidence_score = entity.confidence.score
        target.quality_score = entity.quality_score
        target.sample_size = entity.sample_size
        target.study_type = entity.study_type
        target.statistical_significance = entity.statistical_significance
        target.reviewed = entity.reviewed
        setattr(target, "review_date", entity.review_date)
        target.reviewer_notes = entity.reviewer_notes
        if entity.created_at:
            target.created_at = entity.created_at
        if entity.updated_at:
            target.updated_at = entity.updated_at
        return target

    @staticmethod
    def to_domain_sequence(models: Sequence[EvidenceModel]) -> list[Evidence]:
        return [EvidenceMapper.to_domain(model) for model in models]

    @staticmethod
    def _variant_identifier(variant: VariantModel) -> VariantIdentifier:
        return VariantIdentifier(
            variant_id=variant.variant_id,
            clinvar_id=variant.clinvar_id,
        )


__all__ = ["EvidenceMapper"]
