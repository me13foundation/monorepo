from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from sqlalchemy.orm import Session

from src.domain.entities.gene import Gene
from src.infrastructure.mappers.gene_mapper import GeneMapper
from src.repositories.gene_repository import GeneRepository

if TYPE_CHECKING:
    pass


class SqlAlchemyGeneRepository:
    """Domain-facing repository backed by the existing SQLAlchemy repository."""

    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session
        self._repository = GeneRepository(session)

    def create(self, gene: Gene) -> Gene:
        model = GeneMapper.to_model(gene)
        persisted = self._repository.create(model)
        return GeneMapper.to_domain(persisted)

    def paginate_genes(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        search: Optional[str] = None,
    ) -> Tuple[List[Gene], int]:
        models, total = self._repository.paginate_genes(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
        )
        return GeneMapper.to_domain_sequence(models), total

    def find_by_gene_id(self, gene_id: str) -> Optional[Gene]:
        model = self._repository.find_by_gene_id(gene_id)
        return GeneMapper.to_domain(model) if model else None

    def find_by_symbol(self, symbol: str) -> Optional[Gene]:
        model = self._repository.find_by_symbol(symbol)
        return GeneMapper.to_domain(model) if model else None

    def find_by_external_id(self, identifier: str) -> Optional[Gene]:
        model = self._repository.find_by_external_id(identifier)
        return GeneMapper.to_domain(model) if model else None

    def find_by_gene_id_or_fail(self, gene_id: str) -> Gene:
        model = self._repository.find_by_gene_id_or_fail(gene_id)
        return GeneMapper.to_domain(model)

    def find_by_symbol_or_fail(self, symbol: str) -> Gene:
        model = self._repository.find_by_symbol_or_fail(symbol)
        return GeneMapper.to_domain(model)

    def get_by_id(self, gene_id: int) -> Optional[Gene]:
        model = self._repository.get_by_id(gene_id)
        return GeneMapper.to_domain(model) if model else None

    def get_by_id_or_fail(self, gene_id: int) -> Gene:
        model = self._repository.get_by_id_or_fail(gene_id)
        return GeneMapper.to_domain(model)

    def find_all(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Gene]:
        models = self._repository.find_all(limit=limit, offset=offset)
        return GeneMapper.to_domain_sequence(models)

    def update(self, gene_id: int, updates: Dict[str, Any]) -> Gene:
        model = self._repository.update(gene_id, updates)
        return GeneMapper.to_domain(model)

    def delete(self, gene_id: int) -> bool:
        return self._repository.delete(gene_id)

    def exists(self, gene_id: int) -> bool:
        return self._repository.exists(gene_id)

    def get_gene_statistics(self) -> Dict[str, Any]:
        return self._repository.get_gene_statistics()

    def search_by_name_or_symbol(self, query: str, limit: int = 10) -> List[Gene]:
        models = self._repository.search_by_name_or_symbol(query, limit)
        return GeneMapper.to_domain_sequence(models)

    def count(self) -> int:
        return self._repository.count()


__all__ = ["SqlAlchemyGeneRepository"]
