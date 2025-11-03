from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, cast

from sqlalchemy.orm import Session

from src.domain.entities.variant import (
    ClinicalSignificance,
    Variant,
    VariantSummary,
)
from src.domain.repositories.variant_repository import (
    VariantRepository as VariantRepositoryInterface,
)
from src.domain.repositories.base import QuerySpecification
from src.infrastructure.mappers.variant_mapper import VariantMapper
from src.repositories.variant_repository import VariantRepository
from src.models.database.variant import ClinicalSignificance as DbClinicalSignificance


class SqlAlchemyVariantRepository(VariantRepositoryInterface):
    """Domain-facing repository adapter for variants backed by SQLAlchemy."""

    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session
        self._repository = VariantRepository(session)

    def create(self, variant: Variant) -> Variant:
        model = VariantMapper.to_model(variant)
        persisted = self._repository.create(model)
        return VariantMapper.to_domain(persisted)

    def get_by_id(self, variant_id: int) -> Optional[Variant]:
        model = self._repository.get_by_id(variant_id)
        return VariantMapper.to_domain(model) if model else None

    def get_by_id_or_fail(self, variant_id: int) -> Variant:
        model = self._repository.get_by_id_or_fail(variant_id)
        return VariantMapper.to_domain(model)

    def find_by_variant_id(self, variant_id: str) -> Optional[Variant]:
        model = self._repository.find_by_variant_id(variant_id)
        return VariantMapper.to_domain(model) if model else None

    def find_by_clinvar_id(self, clinvar_id: str) -> Optional[Variant]:
        model = self._repository.find_by_clinvar_id(clinvar_id)
        return VariantMapper.to_domain(model) if model else None

    def find_by_gene(self, gene_id: int, limit: Optional[int] = None) -> List[Variant]:
        models = self._repository.find_by_gene(gene_id, limit=limit)
        return VariantMapper.to_domain_sequence(models)

    def find_by_genomic_location(
        self, chromosome: str, start_pos: int, end_pos: int
    ) -> List[Variant]:
        models = self._repository.find_by_genomic_location(
            chromosome, start_pos, end_pos
        )
        return VariantMapper.to_domain_sequence(models)

    def find_by_clinical_significance(
        self, significance: str, limit: Optional[int] = None
    ) -> List[Variant]:
        normalized = ClinicalSignificance.validate(significance)
        db_significance = cast(DbClinicalSignificance, normalized)
        models = self._repository.find_by_clinical_significance(db_significance, limit)
        return VariantMapper.to_domain_sequence(models)

    def find_pathogenic_variants(self, limit: Optional[int] = None) -> List[Variant]:
        models = self._repository.find_pathogenic_variants(limit)
        return VariantMapper.to_domain_sequence(models)

    def find_with_evidence(self, variant_id: int) -> Optional[Variant]:
        model = self._repository.find_with_evidence(variant_id)
        return VariantMapper.to_domain(model) if model else None

    def update(self, variant_id: int, updates: Dict[str, Any]) -> Variant:
        model = self._repository.update(variant_id, updates)
        return VariantMapper.to_domain(model)

    def delete(self, variant_id: int) -> bool:
        return self._repository.delete(variant_id)

    def get_variant_statistics(self) -> Dict[str, int | float | bool | str | None]:
        raw_stats = self._repository.get_variant_statistics()
        typed_stats: Dict[str, int | float | bool | str | None] = {}
        for key, value in raw_stats.items():
            if isinstance(value, (int, float, bool, str)) or value is None:
                typed_stats[key] = value
        return typed_stats

    def count(self) -> int:
        return self._repository.count()

    # Required interface implementations
    def exists(self, variant_id: int) -> bool:
        return self._repository.exists(variant_id)

    def find_all(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Variant]:
        models = self._repository.find_all(limit=limit, offset=offset)
        return VariantMapper.to_domain_sequence(models)

    def find_by_chromosome_position(
        self, chromosome: str, position: int
    ) -> List[Variant]:
        models = self._repository.find_by_genomic_location(
            chromosome, position, position
        )
        return VariantMapper.to_domain_sequence(models)

    def find_by_criteria(self, spec: QuerySpecification) -> List[Variant]:
        # Simplified implementation - would need more complex query building
        models = self._repository.find_all(limit=spec.limit, offset=spec.offset)
        return VariantMapper.to_domain_sequence(models)

    def find_by_gene_symbol(self, gene_symbol: str) -> List[Variant]:
        models = self._repository.find_by_gene_symbol(gene_symbol)
        return VariantMapper.to_domain_sequence(models)

    def get_variant_summaries_by_gene(self, gene_id: int) -> List[VariantSummary]:
        models = self._repository.find_by_gene(gene_id)
        summaries: List[VariantSummary] = []
        for model in models:
            summaries.append(
                VariantSummary(
                    variant_id=model.variant_id,
                    clinvar_id=model.clinvar_id,
                    chromosome=model.chromosome,
                    position=model.position,
                    clinical_significance=model.clinical_significance,
                )
            )
        return summaries

    def paginate_variants(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Variant], int]:
        # Simplified implementation
        offset = (page - 1) * per_page
        models = self._repository.find_all(limit=per_page, offset=offset)
        total = self._repository.count()
        return VariantMapper.to_domain_sequence(models), total

    def search_variants(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Variant]:
        # Simplified implementation
        models = self._repository.find_all(limit=limit)
        return VariantMapper.to_domain_sequence(models)


__all__ = ["SqlAlchemyVariantRepository"]
