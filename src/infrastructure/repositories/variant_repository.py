"""SQLAlchemy-backed implementation of the domain variant repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import and_, asc, desc, func, or_, select

from src.domain.entities.variant import ClinicalSignificance, VariantSummary
from src.domain.repositories.variant_repository import (
    VariantRepository as VariantRepositoryInterface,
)
from src.infrastructure.mappers.variant_mapper import VariantMapper
from src.models.database import GeneModel, VariantModel

if TYPE_CHECKING:  # pragma: no cover - typing only
    from sqlalchemy.orm import Session

    from src.domain.entities.variant import Variant
    from src.domain.repositories.base import QuerySpecification
    from src.type_definitions.common import QueryFilters, VariantUpdate


class SqlAlchemyVariantRepository(VariantRepositoryInterface):
    """Domain-facing repository adapter for variants backed by SQLAlchemy."""

    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        if self._session is None:
            message = "Session is not configured"
            raise ValueError(message)
        return self._session

    def _to_domain(self, model: VariantModel | None) -> Variant | None:
        return VariantMapper.to_domain(model) if model else None

    def _to_domain_sequence(self, models: list[VariantModel]) -> list[Variant]:
        return VariantMapper.to_domain_sequence(models)

    def create(self, variant: Variant) -> Variant:
        model = VariantMapper.to_model(variant)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return VariantMapper.to_domain(model)

    def get_by_id(self, variant_id: int) -> Variant | None:
        return self._to_domain(self.session.get(VariantModel, variant_id))

    def get_by_id_or_fail(self, variant_id: int) -> Variant:
        model = self.session.get(VariantModel, variant_id)
        if model is None:
            message = f"Variant with id {variant_id} not found"
            raise ValueError(message)
        return VariantMapper.to_domain(model)

    def find_by_variant_id(self, variant_id: str) -> Variant | None:
        stmt = select(VariantModel).where(VariantModel.variant_id == variant_id)
        return self._to_domain(self.session.execute(stmt).scalar_one_or_none())

    def find_by_clinvar_id(self, clinvar_id: str) -> Variant | None:
        stmt = select(VariantModel).where(VariantModel.clinvar_id == clinvar_id)
        return self._to_domain(self.session.execute(stmt).scalar_one_or_none())

    def find_by_gene(self, gene_id: int, limit: int | None = None) -> list[Variant]:
        stmt = select(VariantModel).where(VariantModel.gene_id == gene_id)
        if limit:
            stmt = stmt.limit(limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_genomic_location(
        self,
        chromosome: str,
        start_pos: int,
        end_pos: int,
    ) -> list[Variant]:
        stmt = select(VariantModel).where(
            and_(
                VariantModel.chromosome == chromosome,
                VariantModel.position >= start_pos,
                VariantModel.position <= end_pos,
            ),
        )
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_chromosome_position(
        self,
        chromosome: str,
        position: int,
    ) -> list[Variant]:
        return self.find_by_genomic_location(chromosome, position, position)

    def find_by_clinical_significance(
        self,
        significance: str,
        limit: int | None = None,
    ) -> list[Variant]:
        normalized = ClinicalSignificance.validate(significance)
        stmt = select(VariantModel).where(
            VariantModel.clinical_significance == normalized,
        )
        if limit:
            stmt = stmt.limit(limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_pathogenic_variants(self, limit: int | None = None) -> list[Variant]:
        stmt = select(VariantModel).where(
            or_(
                VariantModel.clinical_significance == ClinicalSignificance.PATHOGENIC,
                VariantModel.clinical_significance
                == ClinicalSignificance.LIKELY_PATHOGENIC,
            ),
        )
        if limit:
            stmt = stmt.limit(limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_with_evidence(self, variant_id: int) -> Variant | None:
        stmt = select(VariantModel).where(VariantModel.id == variant_id)
        return self._to_domain(self.session.execute(stmt).scalar_one_or_none())

    def update(self, variant_id: int, updates: VariantUpdate) -> Variant:
        model = self.session.get(VariantModel, variant_id)
        if model is None:
            message = f"Variant with id {variant_id} not found"
            raise ValueError(message)
        for field, value in updates.items():
            if hasattr(model, field):
                setattr(model, field, value)
        self.session.commit()
        self.session.refresh(model)
        return VariantMapper.to_domain(model)

    def delete(self, variant_id: int) -> bool:
        model = self.session.get(VariantModel, variant_id)
        if model is None:
            return False
        self.session.delete(model)
        self.session.commit()
        return True

    def get_variant_statistics(self) -> dict[str, int | float | bool | str | None]:
        total_variants = self.count()
        pathogenic = len(self.find_pathogenic_variants())
        return {
            "total_variants": total_variants,
            "pathogenic_variants": pathogenic,
            "variants_with_evidence": 0,
        }

    def count(self) -> int:
        stmt = select(func.count()).select_from(VariantModel)
        return int(self.session.execute(stmt).scalar_one())

    def exists(self, variant_id: int) -> bool:
        stmt = select(func.count()).where(VariantModel.id == variant_id)
        return bool(self.session.execute(stmt).scalar_one())

    def find_all(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Variant]:
        stmt = select(VariantModel)
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_criteria(self, spec: QuerySpecification) -> list[Variant]:
        stmt = select(VariantModel)
        for field, value in spec.filters.items():
            column = getattr(VariantModel, field, None)
            if column is not None and value is not None:
                stmt = stmt.where(column == value)
        if spec.offset:
            stmt = stmt.offset(spec.offset)
        if spec.limit:
            stmt = stmt.limit(spec.limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_gene_symbol(self, gene_symbol: str) -> list[Variant]:
        stmt = (
            select(VariantModel)
            .join(VariantModel.gene)
            .where(GeneModel.symbol == gene_symbol.upper())
        )
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def get_variant_summaries_by_gene(self, gene_id: int) -> list[VariantSummary]:
        stmt = select(VariantModel).where(VariantModel.gene_id == gene_id)
        models = list(self.session.execute(stmt).scalars())
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
        stmt = select(VariantModel)
        if filters:
            for field, value in filters.items():
                column = getattr(VariantModel, field, None)
                if column is not None and value is not None:
                    stmt = stmt.where(column == value)
        offset = max(page - 1, 0) * per_page
        if sort_by:
            column = getattr(VariantModel, sort_by, None)
            if column is not None:
                stmt = stmt.order_by(
                    desc(column) if sort_order == "desc" else asc(column),
                )
        stmt = stmt.offset(offset).limit(per_page)
        models = list(self.session.execute(stmt).scalars())
        total = self.count()
        return self._to_domain_sequence(models), total

    def search_variants(
        self,
        query: str,
        limit: int = 10,
        filters: QueryFilters | None = None,
    ) -> list[Variant]:
        stmt = select(VariantModel).limit(limit)
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    VariantModel.variant_id.ilike(pattern),
                    VariantModel.clinvar_id.ilike(pattern),
                    VariantModel.hgvs_genomic.ilike(pattern),
                ),
            )
        if filters:
            for field, value in filters.items():
                column = getattr(VariantModel, field, None)
                if column is not None and value is not None:
                    stmt = stmt.where(column == value)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def update_variant(self, variant_id: int, updates: VariantUpdate) -> Variant:
        return self.update(variant_id, updates)


__all__ = ["SqlAlchemyVariantRepository"]
