from __future__ import annotations

from typing import Optional, Sequence

from src.domain.entities.variant import (
    ClinicalSignificance,
    EvidenceSummary,
    Variant,
    VariantType,
)
from src.domain.value_objects.identifiers import GeneIdentifier, VariantIdentifier
from src.models.database.evidence import EvidenceModel
from src.models.database.gene import GeneModel
from src.models.database.variant import VariantModel


class VariantMapper:
    """Maps between SQLAlchemy VariantModel and domain Variant entities."""

    @staticmethod
    def to_domain(model: VariantModel) -> Variant:
        identifier = VariantIdentifier(
            variant_id=model.variant_id,
            clinvar_id=model.clinvar_id,
        )

        gene_identifier = VariantMapper._build_gene_identifier(model.gene)

        variant = Variant(
            identifier=identifier,
            chromosome=model.chromosome,
            position=model.position,
            reference_allele=model.reference_allele,
            alternate_allele=model.alternate_allele,
            variant_type=model.variant_type or VariantType.UNKNOWN,
            clinical_significance=(
                model.clinical_significance or ClinicalSignificance.NOT_PROVIDED
            ),
            gene_identifier=gene_identifier,
            gene_database_id=model.gene_id,
            hgvs_genomic=model.hgvs_genomic,
            hgvs_protein=model.hgvs_protein,
            hgvs_cdna=model.hgvs_cdna,
            condition=model.condition,
            review_status=model.review_status,
            allele_frequency=model.allele_frequency,
            gnomad_af=model.gnomad_af,
            created_at=model.created_at,
            updated_at=model.updated_at,
            id=model.id,
        )

        if hasattr(model, "evidence") and model.evidence:
            variant.evidence = [
                VariantMapper._to_evidence_summary(evidence)
                for evidence in model.evidence
            ]
            variant.evidence_count = len(variant.evidence)
        else:
            variant.evidence_count = 0

        return variant

    @staticmethod
    def to_model(entity: Variant, model: Optional[VariantModel] = None) -> VariantModel:
        target = model or VariantModel()
        if entity.gene_database_id is None:
            raise ValueError("Variant entity requires gene_database_id for persistence")

        target.gene_id = entity.gene_database_id
        target.variant_id = entity.variant_id
        target.clinvar_id = entity.clinvar_id
        target.chromosome = entity.chromosome
        target.position = entity.position
        target.reference_allele = entity.reference_allele
        target.alternate_allele = entity.alternate_allele
        target.variant_type = entity.variant_type
        target.clinical_significance = entity.clinical_significance
        target.hgvs_genomic = entity.hgvs_genomic
        target.hgvs_protein = entity.hgvs_protein
        target.hgvs_cdna = entity.hgvs_cdna
        target.condition = entity.condition
        target.review_status = entity.review_status
        target.allele_frequency = entity.allele_frequency
        target.gnomad_af = entity.gnomad_af
        if entity.created_at:
            target.created_at = entity.created_at
        if entity.updated_at:
            target.updated_at = entity.updated_at
        return target

    @staticmethod
    def to_domain_sequence(models: Sequence[VariantModel]) -> list[Variant]:
        return [VariantMapper.to_domain(model) for model in models]

    @staticmethod
    def _build_gene_identifier(gene: Optional[GeneModel]) -> Optional[GeneIdentifier]:
        if gene is None:
            return None
        return GeneIdentifier(
            gene_id=gene.gene_id,
            symbol=gene.symbol,
            ensembl_id=gene.ensembl_id,
            ncbi_gene_id=gene.ncbi_gene_id,
            uniprot_id=gene.uniprot_id,
        )

    @staticmethod
    def _to_evidence_summary(evidence: EvidenceModel) -> EvidenceSummary:
        return EvidenceSummary(
            evidence_id=evidence.id,
            evidence_level=evidence.evidence_level,
            evidence_type=evidence.evidence_type,
            description=evidence.description,
            reviewed=evidence.reviewed,
        )


__all__ = ["VariantMapper"]
