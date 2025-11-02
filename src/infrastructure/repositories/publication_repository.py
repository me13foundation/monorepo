from __future__ import annotations

from typing import Dict, List, Optional, cast

from sqlalchemy.orm import Session

from src.domain.entities.publication import Publication
from src.infrastructure.mappers.publication_mapper import PublicationMapper
from src.models.database import PublicationType as DbPublicationType
from src.repositories.publication_repository import PublicationRepository


class SqlAlchemyPublicationRepository:
    """Domain-facing repository adapter for publications backed by SQLAlchemy."""

    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session
        self._repository = PublicationRepository(session)

    def create(self, publication: Publication) -> Publication:
        model = PublicationMapper.to_model(publication)
        persisted = self._repository.create(model)
        return PublicationMapper.to_domain(persisted)

    def get_by_id(self, publication_id: int) -> Optional[Publication]:
        model = self._repository.get_by_id(publication_id)
        return PublicationMapper.to_domain(model) if model else None

    def get_by_id_or_fail(self, publication_id: int) -> Publication:
        model = self._repository.get_by_id_or_fail(publication_id)
        return PublicationMapper.to_domain(model)

    def find_by_pubmed_id(self, pubmed_id: str) -> Optional[Publication]:
        model = self._repository.find_by_pubmed_id(pubmed_id)
        return PublicationMapper.to_domain(model) if model else None

    def find_by_pmc_id(self, pmc_id: str) -> Optional[Publication]:
        model = self._repository.find_by_pmc_id(pmc_id)
        return PublicationMapper.to_domain(model) if model else None

    def find_by_doi(self, doi: str) -> Optional[Publication]:
        model = self._repository.find_by_doi(doi)
        return PublicationMapper.to_domain(model) if model else None

    def find_by_year(self, year: int, limit: Optional[int] = None) -> List[Publication]:
        models = self._repository.find_by_year(year, limit)
        return PublicationMapper.to_domain_sequence(models)

    def find_by_author(
        self, author_name: str, limit: Optional[int] = None
    ) -> List[Publication]:
        models = self._repository.find_by_author(author_name, limit)
        return PublicationMapper.to_domain_sequence(models)

    def find_by_journal(
        self, journal_name: str, limit: Optional[int] = None
    ) -> List[Publication]:
        models = self._repository.find_by_journal(journal_name, limit)
        return PublicationMapper.to_domain_sequence(models)

    def find_by_type(
        self, publication_type: str, limit: Optional[int] = None
    ) -> List[Publication]:
        db_type = cast(DbPublicationType, publication_type)
        models = self._repository.find_by_type(db_type, limit)
        return PublicationMapper.to_domain_sequence(models)

    def find_open_access(self, limit: Optional[int] = None) -> List[Publication]:
        models = self._repository.find_open_access(limit)
        return PublicationMapper.to_domain_sequence(models)

    def find_high_impact(
        self, min_citations: int = 50, limit: Optional[int] = None
    ) -> List[Publication]:
        models = self._repository.find_high_impact(min_citations, limit)
        return PublicationMapper.to_domain_sequence(models)

    def search_publications(self, query: str, limit: int = 20) -> List[Publication]:
        models = self._repository.search_publications(query, limit)
        return PublicationMapper.to_domain_sequence(models)

    def find_med13_relevant(
        self, min_relevance: int = 3, limit: Optional[int] = None
    ) -> List[Publication]:
        models = self._repository.find_med13_relevant(min_relevance, limit)
        return PublicationMapper.to_domain_sequence(models)

    def get_publication_statistics(self) -> Dict[str, object]:
        return self._repository.get_publication_statistics()

    def count(self) -> int:
        return self._repository.count()


__all__ = ["SqlAlchemyPublicationRepository"]
