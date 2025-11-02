from __future__ import annotations

from typing import Dict, List, Optional, cast

from sqlalchemy.orm import Session

from src.domain.entities.phenotype import Phenotype
from src.infrastructure.mappers.phenotype_mapper import PhenotypeMapper
from src.models.database import PhenotypeCategory as DbPhenotypeCategory
from src.repositories.phenotype_repository import PhenotypeRepository


class SqlAlchemyPhenotypeRepository:
    """Domain-facing repository adapter for phenotypes backed by SQLAlchemy."""

    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session
        self._repository = PhenotypeRepository(session)

    def create(self, phenotype: Phenotype) -> Phenotype:
        model = PhenotypeMapper.to_model(phenotype)
        persisted = self._repository.create(model)
        return PhenotypeMapper.to_domain(persisted)

    def find_by_hpo_id(self, hpo_id: str) -> Optional[Phenotype]:
        model = self._repository.find_by_hpo_id(hpo_id)
        return PhenotypeMapper.to_domain(model) if model else None

    def find_by_hpo_id_or_fail(self, hpo_id: str) -> Phenotype:
        model = self._repository.find_by_hpo_id_or_fail(hpo_id)
        return PhenotypeMapper.to_domain(model)

    def find_by_hpo_term(self, hpo_term: str) -> List[Phenotype]:
        models = self._repository.find_by_hpo_term(hpo_term)
        return PhenotypeMapper.to_domain_sequence(models)

    def find_by_category(
        self, category: str, limit: Optional[int] = None
    ) -> List[Phenotype]:
        db_category = cast(DbPhenotypeCategory, category)
        models = self._repository.find_by_category(db_category, limit)
        return PhenotypeMapper.to_domain_sequence(models)

    def find_root_terms(self) -> List[Phenotype]:
        models = self._repository.find_root_terms()
        return PhenotypeMapper.to_domain_sequence(models)

    def find_children(self, parent_hpo_id: str) -> List[Phenotype]:
        models = self._repository.find_children(parent_hpo_id)
        return PhenotypeMapper.to_domain_sequence(models)

    def find_with_evidence(self, phenotype_id: int) -> Optional[Phenotype]:
        model = self._repository.find_with_evidence(phenotype_id)
        return PhenotypeMapper.to_domain(model) if model else None

    def search_phenotypes(self, query: str, limit: int = 20) -> List[Phenotype]:
        models = self._repository.search_phenotypes(query, limit)
        return PhenotypeMapper.to_domain_sequence(models)

    def get_phenotype_statistics(self) -> Dict[str, object]:
        return self._repository.get_phenotype_statistics()

    def count(self) -> int:
        return self._repository.count()


__all__ = ["SqlAlchemyPhenotypeRepository"]
