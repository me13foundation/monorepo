from __future__ import annotations

from typing import TYPE_CHECKING, cast

from src.domain.entities.phenotype import Phenotype, PhenotypeCategory
from src.domain.repositories.phenotype_repository import (
    PhenotypeRepository as PhenotypeRepositoryInterface,
)
from src.infrastructure.mappers.phenotype_mapper import PhenotypeMapper

if TYPE_CHECKING:  # pragma: no cover - typing only
    from src.models.database import PhenotypeCategory as DbPhenotypeCategory
from src.repositories.phenotype_repository import PhenotypeRepository

if TYPE_CHECKING:
    from src.type_definitions.common import PhenotypeUpdate, QueryFilters

if TYPE_CHECKING:  # pragma: no cover - typing only
    from sqlalchemy.orm import Session

    from src.domain.repositories.base import QuerySpecification


class SqlAlchemyPhenotypeRepository(PhenotypeRepositoryInterface):
    """Domain-facing repository adapter for phenotypes backed by SQLAlchemy."""

    def __init__(self, session: Session | None = None) -> None:
        self._session = session
        self._repository = PhenotypeRepository(session)

    def create(self, phenotype: Phenotype) -> Phenotype:
        model = PhenotypeMapper.to_model(phenotype)
        persisted = self._repository.create(model)
        return PhenotypeMapper.to_domain(persisted)

    def find_by_hpo_id(self, hpo_id: str) -> Phenotype | None:
        model = self._repository.find_by_hpo_id(hpo_id)
        return PhenotypeMapper.to_domain(model) if model else None

    def find_by_hpo_id_or_fail(self, hpo_id: str) -> Phenotype:
        model = self._repository.find_by_hpo_id_or_fail(hpo_id)
        return PhenotypeMapper.to_domain(model)

    def find_by_hpo_term(self, hpo_term: str) -> list[Phenotype]:
        models = self._repository.find_by_hpo_term(hpo_term)
        return PhenotypeMapper.to_domain_sequence(models)

    def find_by_category(
        self,
        category: str,
        limit: int | None = None,
    ) -> list[Phenotype]:
        normalized = PhenotypeCategory.validate(category)
        db_category = cast("DbPhenotypeCategory", normalized)
        models = self._repository.find_by_category(db_category, limit)
        return PhenotypeMapper.to_domain_sequence(models)

    def find_root_terms(self) -> list[Phenotype]:
        models = self._repository.find_root_terms()
        return PhenotypeMapper.to_domain_sequence(models)

    def find_children(self, parent_hpo_id: str) -> list[Phenotype]:
        models = self._repository.find_children(parent_hpo_id)
        return PhenotypeMapper.to_domain_sequence(models)

    def find_with_evidence(self, phenotype_id: int) -> Phenotype | None:
        model = self._repository.find_with_evidence(phenotype_id)
        return PhenotypeMapper.to_domain(model) if model else None

    def search_phenotypes(
        self,
        query: str,
        limit: int = 20,
        filters: QueryFilters | None = None,
    ) -> list[Phenotype]:
        # filters retained for API compatibility
        if filters:
            _ = dict(filters)
        models = self._repository.search_phenotypes(query, limit)
        return PhenotypeMapper.to_domain_sequence(models)

    def get_phenotype_statistics(self) -> dict[str, int | float | bool | str | None]:
        raw_stats = self._repository.get_phenotype_statistics()
        return {
            key: value
            for key, value in raw_stats.items()
            if isinstance(value, (int, float, bool, str)) or value is None
        }

    def count(self) -> int:
        return self._repository.count()

    # Required interface implementations
    def delete(self, phenotype_id: int) -> bool:
        return self._repository.delete(phenotype_id)

    def exists(self, phenotype_id: int) -> bool:
        return self._repository.exists(phenotype_id)

    def find_all(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Phenotype]:
        models = self._repository.find_all(limit=limit, offset=offset)
        return PhenotypeMapper.to_domain_sequence(models)

    def find_by_criteria(self, spec: QuerySpecification) -> list[Phenotype]:
        # Simplified implementation
        return PhenotypeMapper.to_domain_sequence(
            self._repository.find_all(limit=spec.limit, offset=spec.offset),
        )

    def get_by_id(self, phenotype_id: int) -> Phenotype | None:
        model = self._repository.get_by_id(phenotype_id)
        return PhenotypeMapper.to_domain(model) if model else None

    def find_by_gene_associations(self, gene_id: int) -> list[Phenotype]:
        models = self._repository.find_by_gene_associations(gene_id)
        return PhenotypeMapper.to_domain_sequence(models)

    def find_by_name(self, name: str, *, fuzzy: bool = False) -> list[Phenotype]:
        # fuzzy currently unused by underlying repo
        if fuzzy:
            _ = fuzzy
        models = self._repository.search_phenotypes(name, limit=10)
        return PhenotypeMapper.to_domain_sequence(models)

    def find_by_ontology_term(self, term_id: str) -> Phenotype | None:
        return self.find_by_hpo_id(term_id)

    def find_by_variant_associations(self, variant_id: int) -> list[Phenotype]:
        models = self._repository.find_by_variant_associations(variant_id)
        return PhenotypeMapper.to_domain_sequence(models)

    def paginate_phenotypes(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        filters: QueryFilters | None = None,
    ) -> tuple[list[Phenotype], int]:
        # Simplified implementation; sort params retained for compatibility
        if sort_by:
            _ = sort_by
        if sort_order:
            _ = sort_order
        if filters:
            _ = dict(filters)
        offset = (page - 1) * per_page
        models = self._repository.find_all(limit=per_page, offset=offset)
        total = self._repository.count()
        return PhenotypeMapper.to_domain_sequence(models), total

    def update(self, phenotype_id: int, updates: PhenotypeUpdate) -> Phenotype:
        model = self._repository.update(phenotype_id, dict(updates))
        return PhenotypeMapper.to_domain(model)

    def update_phenotype(
        self,
        phenotype_id: int,
        updates: PhenotypeUpdate,
    ) -> Phenotype:
        """Update a phenotype with type-safe update parameters."""
        return self.update(phenotype_id, updates)


__all__ = ["SqlAlchemyPhenotypeRepository"]
