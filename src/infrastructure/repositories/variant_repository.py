from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.domain.entities.variant import Variant
from src.infrastructure.mappers.variant_mapper import VariantMapper
from src.repositories.variant_repository import VariantRepository
from src.models.database.variant import ClinicalSignificance


class SqlAlchemyVariantRepository:
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
        self, significance: ClinicalSignificance, limit: Optional[int] = None
    ) -> List[Variant]:
        models = self._repository.find_by_clinical_significance(significance, limit)
        return VariantMapper.to_domain_sequence(models)

    def find_pathogenic_variants(self, limit: Optional[int] = None) -> List[Variant]:
        models = self._repository.find_pathogenic_variants(limit)
        return VariantMapper.to_domain_sequence(models)

    def find_with_evidence(self, variant_id: int) -> Optional[Variant]:
        model = self._repository.find_with_evidence(variant_id)
        return VariantMapper.to_domain(model) if model else None

    def update(self, variant_id: int, updates: Dict[str, object]) -> Variant:
        model = self._repository.update(variant_id, updates)
        return VariantMapper.to_domain(model)

    def delete(self, variant_id: int) -> bool:
        return self._repository.delete(variant_id)

    def get_variant_statistics(self) -> Dict[str, object]:
        return self._repository.get_variant_statistics()

    def count(self) -> int:
        return self._repository.count()


__all__ = ["SqlAlchemyVariantRepository"]
