from __future__ import annotations

from typing import TYPE_CHECKING, cast

from src.domain.entities.variant import ClinicalSignificance, VariantSummary
from src.domain.repositories.variant_repository import (
    VariantRepository as VariantRepositoryInterface,
)
from src.infrastructure.mappers.variant_mapper import VariantMapper
from src.repositories.variant_repository import VariantRepository

if TYPE_CHECKING:  # pragma: no cover - typing only
    from sqlalchemy.orm import Session

    from src.domain.entities.variant import Variant
    from src.domain.repositories.base import QuerySpecification
    from src.models.database.variant import (
        ClinicalSignificance as DbClinicalSignificance,
    )
    from src.type_definitions.common import QueryFilters, VariantUpdate


class SqlAlchemyVariantRepository(VariantRepositoryInterface):
    """Domain-facing repository adapter for variants backed by SQLAlchemy."""

    def __init__(self, session: Session | None = None) -> None:
        self._session = session
        self._repository = VariantRepository(session)

    def create(self, variant: Variant) -> Variant:
        model = VariantMapper.to_model(variant)
        persisted = self._repository.create(model)
        return VariantMapper.to_domain(persisted)

    def get_by_id(self, variant_id: int) -> Variant | None:
        model = self._repository.get_by_id(variant_id)
        return VariantMapper.to_domain(model) if model else None

    def get_by_id_or_fail(self, variant_id: int) -> Variant:
        model = self._repository.get_by_id_or_fail(variant_id)
        return VariantMapper.to_domain(model)

    def find_by_variant_id(self, variant_id: str) -> Variant | None:
        model = self._repository.find_by_variant_id(variant_id)
        return VariantMapper.to_domain(model) if model else None

    def find_by_clinvar_id(self, clinvar_id: str) -> Variant | None:
        model = self._repository.find_by_clinvar_id(clinvar_id)
        return VariantMapper.to_domain(model) if model else None

    def find_by_gene(self, gene_id: int, limit: int | None = None) -> list[Variant]:
        models = self._repository.find_by_gene(gene_id, limit=limit)
        return VariantMapper.to_domain_sequence(models)

    def find_by_genomic_location(
        self,
        chromosome: str,
        start_pos: int,
        end_pos: int,
    ) -> list[Variant]:
        models = self._repository.find_by_genomic_location(
            chromosome,
            start_pos,
            end_pos,
        )
        return VariantMapper.to_domain_sequence(models)

    def find_by_clinical_significance(
        self,
        significance: str,
        limit: int | None = None,
    ) -> list[Variant]:
        normalized = ClinicalSignificance.validate(significance)
        db_significance = cast("DbClinicalSignificance", normalized)
        models = self._repository.find_by_clinical_significance(db_significance, limit)
        return VariantMapper.to_domain_sequence(models)

    def find_pathogenic_variants(self, limit: int | None = None) -> list[Variant]:
        models = self._repository.find_pathogenic_variants(limit)
        return VariantMapper.to_domain_sequence(models)

    def find_with_evidence(self, variant_id: int) -> Variant | None:
        model = self._repository.find_with_evidence(variant_id)
        return VariantMapper.to_domain(model) if model else None

    def update(self, variant_id: int, updates: VariantUpdate) -> Variant:
        model = self._repository.update(variant_id, dict(updates))
        return VariantMapper.to_domain(model)

    def delete(self, variant_id: int) -> bool:
        return self._repository.delete(variant_id)

    def get_variant_statistics(self) -> dict[str, int | float | bool | str | None]:
        raw_stats = self._repository.get_variant_statistics()
        return {
            key: value
            for key, value in raw_stats.items()
            if isinstance(value, (int, float, bool, str)) or value is None
        }

    def count(self) -> int:
        return self._repository.count()

    # Required interface implementations
    def exists(self, variant_id: int) -> bool:
        return self._repository.exists(variant_id)

    def find_all(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Variant]:
        models = self._repository.find_all(limit=limit, offset=offset)
        return VariantMapper.to_domain_sequence(models)

    def find_by_chromosome_position(
        self,
        chromosome: str,
        position: int,
    ) -> list[Variant]:
        models = self._repository.find_by_genomic_location(
            chromosome,
            position,
            position,
        )
        return VariantMapper.to_domain_sequence(models)

    def find_by_criteria(self, spec: QuerySpecification) -> list[Variant]:
        # Simplified implementation - would need more complex query building
        models = self._repository.find_all(limit=spec.limit, offset=spec.offset)
        return VariantMapper.to_domain_sequence(models)

    def find_by_gene_symbol(self, gene_symbol: str) -> list[Variant]:
        models = self._repository.find_by_gene_symbol(gene_symbol)
        return VariantMapper.to_domain_sequence(models)

    def get_variant_summaries_by_gene(self, gene_id: int) -> list[VariantSummary]:
        models = self._repository.find_by_gene(gene_id)
        return [
            VariantSummary(
                variant_id=model.variant_id,
                clinvar_id=model.clinvar_id,
                chromosome=model.chromosome,
                position=model.position,
                clinical_significance=model.clinical_significance,
            )
            for model in models
        ]

    def paginate_variants(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        filters: QueryFilters | None = None,
    ) -> tuple[list[Variant], int]:
        # Simplified implementation
        # Parameters retained for API compatibility
        if sort_by:
            _ = sort_by
        if sort_order:
            _ = sort_order
        if filters:
            _ = dict(filters)
        offset = (page - 1) * per_page
        models = self._repository.find_all(limit=per_page, offset=offset)
        total = self._repository.count()
        return VariantMapper.to_domain_sequence(models), total

    def search_variants(
        self,
        query: str,
        limit: int = 10,
        filters: QueryFilters | None = None,
    ) -> list[Variant]:
        # Simplified implementation
        if query:
            _ = query
        if filters:
            _ = dict(filters)
        models = self._repository.find_all(limit=limit)
        return VariantMapper.to_domain_sequence(models)

    def update_variant(self, variant_id: int, updates: VariantUpdate) -> Variant:
        """Update a variant with type-safe update parameters."""
        # Convert TypedDict to Dict[str, Any] for the underlying repository
        updates_dict = dict(updates)
        model = self._repository.update(variant_id, updates_dict)
        return VariantMapper.to_domain(model)


__all__ = ["SqlAlchemyVariantRepository"]
