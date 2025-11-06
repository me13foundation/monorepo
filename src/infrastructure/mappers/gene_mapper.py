from __future__ import annotations

from typing import TYPE_CHECKING

from src.domain.entities.gene import Gene, GeneType
from src.domain.entities.variant import VariantSummary
from src.domain.value_objects.identifiers import GeneIdentifier
from src.models.database.gene import GeneModel

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Sequence

    from src.models.database.variant import VariantModel


class GeneMapper:
    """Maps between SQLAlchemy GeneModel and domain Gene entity."""

    @staticmethod
    def to_domain(model: GeneModel) -> Gene:
        identifier = GeneIdentifier(
            gene_id=model.gene_id,
            symbol=model.symbol,
            ensembl_id=model.ensembl_id,
            ncbi_gene_id=model.ncbi_gene_id,
            uniprot_id=model.uniprot_id,
        )

        gene = Gene(
            identifier=identifier,
            gene_type=model.gene_type or GeneType.UNKNOWN,
            name=model.name,
            description=model.description,
            chromosome=model.chromosome,
            start_position=model.start_position,
            end_position=model.end_position,
            created_at=model.created_at,
            updated_at=model.updated_at,
            id=model.id,
        )

        if hasattr(model, "variants") and model.variants:
            gene.variants = [
                GeneMapper._serialize_variant(variant) for variant in model.variants
            ]

        return gene

    @staticmethod
    def to_model(entity: Gene, model: GeneModel | None = None) -> GeneModel:
        target = model or GeneModel()
        target.gene_id = entity.gene_id
        target.symbol = entity.symbol
        target.name = entity.name
        target.description = entity.description
        target.gene_type = entity.gene_type
        target.chromosome = entity.chromosome
        target.start_position = entity.start_position
        target.end_position = entity.end_position
        target.ensembl_id = entity.ensembl_id
        target.ncbi_gene_id = entity.ncbi_gene_id
        target.uniprot_id = entity.uniprot_id
        if entity.created_at:
            target.created_at = entity.created_at
        if entity.updated_at:
            target.updated_at = entity.updated_at
        return target

    @staticmethod
    def to_domain_sequence(models: Sequence[GeneModel]) -> list[Gene]:
        return [GeneMapper.to_domain(model) for model in models]

    @staticmethod
    def _serialize_variant(variant: VariantModel) -> VariantSummary:
        return VariantSummary(
            variant_id=variant.variant_id,
            clinvar_id=variant.clinvar_id,
            chromosome=variant.chromosome,
            position=variant.position,
            clinical_significance=variant.clinical_significance,
        )


__all__ = ["GeneMapper"]
