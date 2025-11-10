from __future__ import annotations

from typing import TYPE_CHECKING, cast

from src.domain.repositories.publication_repository import (
    PublicationRepository as PublicationRepositoryInterface,
)
from src.infrastructure.mappers.publication_mapper import PublicationMapper
from src.repositories.publication_repository import PublicationRepository

if TYPE_CHECKING:  # pragma: no cover - typing only
    from src.models.database import PublicationType as DbPublicationType
    from src.type_definitions.common import PublicationUpdate, QueryFilters

if TYPE_CHECKING:  # pragma: no cover - typing only
    from sqlalchemy.orm import Session

    from src.domain.entities.publication import Publication
    from src.domain.repositories.base import QuerySpecification


class SqlAlchemyPublicationRepository(PublicationRepositoryInterface):
    """Domain-facing repository adapter for publications backed by SQLAlchemy."""

    def __init__(self, session: Session | None = None) -> None:
        self._session = session
        self._repository = PublicationRepository(session)

    def create(self, publication: Publication) -> Publication:
        model = PublicationMapper.to_model(publication)
        persisted = self._repository.create(model)
        return PublicationMapper.to_domain(persisted)

    def get_by_id(self, publication_id: int) -> Publication | None:
        model = self._repository.get_by_id(publication_id)
        return PublicationMapper.to_domain(model) if model else None

    def get_by_id_or_fail(self, publication_id: int) -> Publication:
        model = self._repository.get_by_id_or_fail(publication_id)
        return PublicationMapper.to_domain(model)

    def find_by_pubmed_id(self, pubmed_id: str) -> Publication | None:
        model = self._repository.find_by_pubmed_id(pubmed_id)
        return PublicationMapper.to_domain(model) if model else None

    def find_by_pmc_id(self, pmc_id: str) -> Publication | None:
        model = self._repository.find_by_pmc_id(pmc_id)
        return PublicationMapper.to_domain(model) if model else None

    def find_by_year(self, year: int, limit: int | None = None) -> list[Publication]:
        models = self._repository.find_by_year(year, limit)
        return PublicationMapper.to_domain_sequence(models)

    def find_by_author(
        self,
        author_name: str,
        limit: int | None = None,
    ) -> list[Publication]:
        models = self._repository.find_by_author(author_name, limit)
        return PublicationMapper.to_domain_sequence(models)

    def find_by_journal(
        self,
        journal_name: str,
        limit: int | None = None,
    ) -> list[Publication]:
        models = self._repository.find_by_journal(journal_name, limit)
        return PublicationMapper.to_domain_sequence(models)

    def find_by_type(
        self,
        publication_type: str,
        limit: int | None = None,
    ) -> list[Publication]:
        db_type = cast("DbPublicationType", publication_type)
        models = self._repository.find_by_type(db_type, limit)
        return PublicationMapper.to_domain_sequence(models)

    def find_open_access(self, limit: int | None = None) -> list[Publication]:
        models = self._repository.find_open_access(limit)
        return PublicationMapper.to_domain_sequence(models)

    def find_high_impact(
        self,
        min_citations: int = 50,
        limit: int | None = None,
    ) -> list[Publication]:
        models = self._repository.find_high_impact(min_citations, limit)
        return PublicationMapper.to_domain_sequence(models)

    def search_publications(
        self,
        query: str,
        limit: int = 20,
        filters: QueryFilters | None = None,
    ) -> list[Publication]:
        # Filters retained for API compatibility
        if filters:
            _ = dict(filters)
        models = self._repository.search_publications(query, limit)
        return PublicationMapper.to_domain_sequence(models)

    def find_med13_relevant(
        self,
        min_relevance: int = 3,
        limit: int | None = None,
    ) -> list[Publication]:
        models = self._repository.find_med13_relevant(min_relevance, limit)
        return PublicationMapper.to_domain_sequence(models)

    def get_publication_statistics(self) -> dict[str, int | float | bool | str | None]:
        raw_stats = self._repository.get_publication_statistics()
        return {
            key: value
            for key, value in raw_stats.items()
            if isinstance(value, (int, float, bool, str)) or value is None
        }

    def count(self) -> int:
        return self._repository.count()

    # Required interface implementations
    def delete(self, publication_id: int) -> bool:
        return self._repository.delete(publication_id)

    def exists(self, publication_id: int) -> bool:
        return self._repository.exists(publication_id)

    def find_all(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Publication]:
        models = self._repository.find_all(limit=limit, offset=offset)
        return PublicationMapper.to_domain_sequence(models)

    def find_by_criteria(self, spec: QuerySpecification) -> list[Publication]:
        # Simplified implementation
        return PublicationMapper.to_domain_sequence(
            self._repository.find_all(limit=spec.limit, offset=spec.offset),
        )

    def find_by_gene_associations(self, gene_id: int) -> list[Publication]:
        # Placeholder implementation until relationships are modeled.
        if gene_id:
            _ = gene_id
        return []

    def find_by_pmid(self, pmid: str) -> Publication | None:
        model = self._repository.find_by_pmid(pmid)
        return PublicationMapper.to_domain(model) if model else None

    def find_by_doi(self, doi: str) -> Publication | None:
        model = self._repository.find_by_doi(doi)
        return PublicationMapper.to_domain(model) if model else None

    def find_by_title(
        self,
        title: str,
        fuzzy: bool = False,  # noqa: FBT001, FBT002
    ) -> list[Publication]:
        if fuzzy:
            _ = fuzzy
        models = self._repository.search_publications(title, limit=10)
        return PublicationMapper.to_domain_sequence(models)

    def find_by_year_range(self, start_year: int, end_year: int) -> list[Publication]:
        models = self._repository.find_by_year_range(start_year, end_year)
        return PublicationMapper.to_domain_sequence(models)

    def find_by_variant_associations(self, variant_id: int) -> list[Publication]:
        # Placeholder implementation
        if variant_id:
            _ = variant_id
        return []

    def paginate_publications(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        filters: QueryFilters | None = None,
    ) -> tuple[list[Publication], int]:
        # Simplified implementation
        if filters:
            _ = dict(filters)
        if sort_by:
            _ = sort_by
        if sort_order:
            _ = sort_order
        offset = (page - 1) * per_page
        models = self._repository.find_all(limit=per_page, offset=offset)
        total = self._repository.count()
        return PublicationMapper.to_domain_sequence(models), total

    def update(self, publication_id: int, updates: PublicationUpdate) -> Publication:
        model = self._repository.update(publication_id, dict(updates))
        return PublicationMapper.to_domain(model)

    def update_publication(
        self,
        publication_id: int,
        updates: PublicationUpdate,
    ) -> Publication:
        """Update a publication with type-safe update parameters."""
        return self.update(publication_id, updates)

    def find_recent_publications(self, days: int = 30) -> list[Publication]:
        models = self._repository.find_recent_publications(days=days)
        return PublicationMapper.to_domain_sequence(models)


__all__ = ["SqlAlchemyPublicationRepository"]
