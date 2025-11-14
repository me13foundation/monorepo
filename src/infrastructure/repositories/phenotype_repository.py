"""SQLAlchemy-backed implementation of the domain phenotype repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import asc, func, or_, select

from src.domain.entities.phenotype import PhenotypeCategory
from src.domain.repositories.phenotype_repository import (
    PhenotypeRepository as PhenotypeRepositoryInterface,
)
from src.infrastructure.mappers.phenotype_mapper import PhenotypeMapper
from src.models.database import EvidenceModel, PhenotypeModel, VariantModel

if TYPE_CHECKING:  # pragma: no cover - typing only
    from sqlalchemy.orm import Session

    from src.domain.entities.phenotype import Phenotype
    from src.domain.repositories.base import QuerySpecification
    from src.type_definitions.common import PhenotypeUpdate, QueryFilters


class SqlAlchemyPhenotypeRepository(PhenotypeRepositoryInterface):
    """Domain-facing repository adapter for phenotypes backed by SQLAlchemy."""

    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        if self._session is None:
            message = "Session is not configured"
            raise ValueError(message)
        return self._session

    def _to_domain(self, model: PhenotypeModel | None) -> Phenotype | None:
        return PhenotypeMapper.to_domain(model) if model else None

    def _to_domain_sequence(self, models: list[PhenotypeModel]) -> list[Phenotype]:
        return PhenotypeMapper.to_domain_sequence(models)

    def create(self, phenotype: Phenotype) -> Phenotype:
        model = PhenotypeMapper.to_model(phenotype)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return PhenotypeMapper.to_domain(model)

    def find_by_hpo_id(self, hpo_id: str) -> Phenotype | None:
        stmt = select(PhenotypeModel).where(PhenotypeModel.hpo_id == hpo_id)
        return self._to_domain(self.session.execute(stmt).scalar_one_or_none())

    def find_by_hpo_id_or_fail(self, hpo_id: str) -> Phenotype:
        phenotype = self.find_by_hpo_id(hpo_id)
        if phenotype is None:
            message = f"Phenotype with HPO ID '{hpo_id}' not found"
            raise ValueError(message)
        return phenotype

    def find_by_hpo_term(self, hpo_term: str) -> list[Phenotype]:
        stmt = select(PhenotypeModel).where(
            PhenotypeModel.hpo_term.ilike(f"%{hpo_term}%"),
        )
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_category(
        self,
        category: str,
        limit: int | None = None,
    ) -> list[Phenotype]:
        normalized = PhenotypeCategory.validate(category)
        stmt = select(PhenotypeModel).where(PhenotypeModel.category == normalized)
        if limit:
            stmt = stmt.limit(limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_root_terms(self) -> list[Phenotype]:
        stmt = select(PhenotypeModel).where(PhenotypeModel.is_root_term)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_children(self, parent_hpo_id: str) -> list[Phenotype]:
        stmt = select(PhenotypeModel).where(
            PhenotypeModel.parent_hpo_id == parent_hpo_id,
        )
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_with_evidence(self, phenotype_id: int) -> Phenotype | None:
        stmt = select(PhenotypeModel).where(PhenotypeModel.id == phenotype_id)
        return self._to_domain(self.session.execute(stmt).scalar_one_or_none())

    def search_phenotypes(
        self,
        query: str,
        limit: int = 20,
        filters: QueryFilters | None = None,
    ) -> list[Phenotype]:
        if filters:
            _ = dict(filters)
        pattern = f"%{query}%"
        stmt = (
            select(PhenotypeModel)
            .where(
                or_(
                    PhenotypeModel.name.ilike(pattern),
                    PhenotypeModel.definition.ilike(pattern),
                    PhenotypeModel.synonyms.ilike(pattern),
                ),
            )
            .limit(limit)
        )
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def get_phenotype_statistics(self) -> dict[str, int | float | bool | str | None]:
        total = self.count()
        root_terms = len(self.find_root_terms())
        return {
            "total_phenotypes": total,
            "root_terms": root_terms,
            "phenotypes_with_evidence": 0,
        }

    def count(self) -> int:
        stmt = select(func.count()).select_from(PhenotypeModel)
        return int(self.session.execute(stmt).scalar_one())

    def delete(self, phenotype_id: int) -> bool:
        model = self.session.get(PhenotypeModel, phenotype_id)
        if model is None:
            return False
        self.session.delete(model)
        self.session.commit()
        return True

    def exists(self, phenotype_id: int) -> bool:
        stmt = select(func.count()).where(PhenotypeModel.id == phenotype_id)
        return bool(self.session.execute(stmt).scalar_one())

    def find_all(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Phenotype]:
        stmt = select(PhenotypeModel)
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_criteria(self, spec: QuerySpecification) -> list[Phenotype]:
        stmt = select(PhenotypeModel)
        for field, value in spec.filters.items():
            column = getattr(PhenotypeModel, field, None)
            if column is not None and value is not None:
                stmt = stmt.where(column == value)
        if spec.offset:
            stmt = stmt.offset(spec.offset)
        if spec.limit:
            stmt = stmt.limit(spec.limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def get_by_id(self, phenotype_id: int) -> Phenotype | None:
        return self._to_domain(self.session.get(PhenotypeModel, phenotype_id))

    def find_by_gene_associations(self, gene_id: int) -> list[Phenotype]:
        stmt = (
            select(PhenotypeModel)
            .join(EvidenceModel, EvidenceModel.phenotype_id == PhenotypeModel.id)
            .join(VariantModel, VariantModel.id == EvidenceModel.variant_id)
            .where(VariantModel.gene_id == gene_id)
            .order_by(PhenotypeModel.name.asc())
        ).distinct()
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_name(self, name: str, *, fuzzy: bool = False) -> list[Phenotype]:
        if fuzzy:
            return self.search_phenotypes(name, limit=10)
        stmt = select(PhenotypeModel).where(PhenotypeModel.name == name)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_ontology_term(self, term_id: str) -> Phenotype | None:
        return self.find_by_hpo_id(term_id)

    def find_by_variant_associations(self, variant_id: int) -> list[Phenotype]:
        stmt = (
            select(PhenotypeModel)
            .join(EvidenceModel, EvidenceModel.phenotype_id == PhenotypeModel.id)
            .where(EvidenceModel.variant_id == variant_id)
            .order_by(PhenotypeModel.name.asc())
        ).distinct()
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def paginate_phenotypes(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        filters: QueryFilters | None = None,
    ) -> tuple[list[Phenotype], int]:
        stmt = select(PhenotypeModel)
        if filters:
            for field, value in filters.items():
                column = getattr(PhenotypeModel, field, None)
                if column is not None and value is not None:
                    stmt = stmt.where(column == value)
        sortable = {
            "name": PhenotypeModel.name,
            "category": PhenotypeModel.category,
            "hpo_id": PhenotypeModel.hpo_id,
        }
        sort_column = sortable.get(sort_by)
        if sort_column is not None:
            stmt = stmt.order_by(
                asc(sort_column) if sort_order != "desc" else sort_column.desc(),
            )
        offset = max(page - 1, 0) * per_page
        stmt = stmt.offset(offset).limit(per_page)
        models = list(self.session.execute(stmt).scalars())
        total = self.count()
        return self._to_domain_sequence(models), total

    def update(self, phenotype_id: int, updates: PhenotypeUpdate) -> Phenotype:
        model = self.session.get(PhenotypeModel, phenotype_id)
        if model is None:
            message = f"Phenotype with id {phenotype_id} not found"
            raise ValueError(message)
        for field, value in updates.items():
            if hasattr(model, field):
                setattr(model, field, value)
        self.session.commit()
        self.session.refresh(model)
        return PhenotypeMapper.to_domain(model)

    def update_phenotype(
        self,
        phenotype_id: int,
        updates: PhenotypeUpdate,
    ) -> Phenotype:
        return self.update(phenotype_id, updates)


__all__ = ["SqlAlchemyPhenotypeRepository"]
