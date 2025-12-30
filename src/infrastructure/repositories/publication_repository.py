from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import and_, asc, desc, func, or_, select

from src.domain.repositories.publication_repository import (
    PublicationRepository as PublicationRepositoryInterface,
)
from src.infrastructure.mappers.publication_mapper import PublicationMapper
from src.models.database import PublicationModel

if TYPE_CHECKING:  # pragma: no cover - typing only
    from sqlalchemy.orm import Session

    from src.domain.entities.publication import Publication
    from src.domain.repositories.base import QuerySpecification
    from src.type_definitions.common import PublicationUpdate, QueryFilters


class PublicationQueryMixin:
    """Reusable mixin providing rich publication query helpers."""

    if TYPE_CHECKING:  # pragma: no cover - typing only

        @property
        def session(self) -> Session: ...  # noqa: D401 - documentation inherited

        def _to_domain_sequence(
            self,
            models: list[PublicationModel],
        ) -> list[Publication]: ...

        def _to_domain(self, model: PublicationModel | None) -> Publication | None: ...

        def count(self) -> int: ...

    def find_by_year(self, year: int, limit: int | None = None) -> list[Publication]:
        stmt = select(PublicationModel).where(PublicationModel.publication_year == year)
        if limit:
            stmt = stmt.limit(limit)
        models = list(self.session.execute(stmt).scalars())
        return self._to_domain_sequence(models)

    def find_by_author(
        self,
        author_name: str,
        limit: int | None = None,
    ) -> list[Publication]:
        search_pattern = f"%{author_name}%"
        stmt = select(PublicationModel).where(
            PublicationModel.authors.ilike(search_pattern),
        )
        if limit:
            stmt = stmt.limit(limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_journal(
        self,
        journal_name: str,
        limit: int | None = None,
    ) -> list[Publication]:
        stmt = select(PublicationModel).where(
            PublicationModel.journal.ilike(f"%{journal_name}%"),
        )
        if limit:
            stmt = stmt.limit(limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_type(
        self,
        publication_type: str,
        limit: int | None = None,
    ) -> list[Publication]:
        stmt = select(PublicationModel).where(
            PublicationModel.publication_type == publication_type,
        )
        if limit:
            stmt = stmt.limit(limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_open_access(self, limit: int | None = None) -> list[Publication]:
        stmt = select(PublicationModel).where(PublicationModel.open_access.is_(True))
        if limit:
            stmt = stmt.limit(limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_high_impact(
        self,
        min_citations: int = 50,
        limit: int | None = None,
    ) -> list[Publication]:
        stmt = select(PublicationModel).where(
            PublicationModel.citation_count >= min_citations,
        )
        if limit:
            stmt = stmt.limit(limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def search_publications(
        self,
        query: str,
        limit: int = 20,
        filters: QueryFilters | None = None,
    ) -> list[Publication]:
        if filters:
            _ = dict(filters)
        search_pattern = f"%{query}%"
        stmt = (
            select(PublicationModel)
            .where(
                or_(
                    PublicationModel.title.ilike(search_pattern),
                    PublicationModel.authors.ilike(search_pattern),
                    PublicationModel.abstract.ilike(search_pattern),
                    PublicationModel.keywords.ilike(search_pattern),
                ),
            )
            .limit(limit)
        )
        models = list(self.session.execute(stmt).scalars())
        return self._to_domain_sequence(models)

    def find_med13_relevant(
        self,
        min_relevance: int = 3,
        limit: int | None = None,
    ) -> list[Publication]:
        stmt = select(PublicationModel).where(
            and_(
                PublicationModel.relevance_score >= min_relevance,
                PublicationModel.relevance_score.isnot(None),
            ),
        )
        if limit:
            stmt = stmt.limit(limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def get_publication_statistics(self) -> dict[str, int | float | bool | str | None]:
        total_publications = self.count()
        open_access = len(self.find_open_access())
        med13_relevant = len(self.find_med13_relevant())
        return {
            "total_publications": total_publications,
            "open_access_publications": open_access,
            "med13_relevant_publications": med13_relevant,
        }

    def find_by_criteria(self, spec: QuerySpecification) -> list[Publication]:
        stmt = select(PublicationModel)
        for field, value in spec.filters.items():
            column = getattr(PublicationModel, field, None)
            if column is not None and value is not None:
                stmt = stmt.where(column == value)
        if spec.sort_by:
            column = getattr(PublicationModel, spec.sort_by, None)
            if column is not None:
                sort_clause = desc(column) if spec.sort_order == "desc" else asc(column)
                stmt = stmt.order_by(sort_clause)
        if spec.offset:
            stmt = stmt.offset(spec.offset)
        if spec.limit:
            stmt = stmt.limit(spec.limit)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_gene_associations(self, gene_id: int) -> list[Publication]:
        if gene_id:
            _ = gene_id
        return []

    def find_by_doi(self, doi: str) -> Publication | None:
        stmt = select(PublicationModel).where(PublicationModel.doi == doi)
        return self._to_domain(self.session.execute(stmt).scalar_one_or_none())

    def find_by_title(
        self,
        title: str,
        fuzzy: bool = False,  # noqa: FBT001, FBT002
    ) -> list[Publication]:
        stmt = select(PublicationModel)
        if fuzzy:
            stmt = stmt.where(PublicationModel.title.ilike(f"%{title}%"))
        else:
            stmt = stmt.where(PublicationModel.title == title)
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_year_range(self, start_year: int, end_year: int) -> list[Publication]:
        stmt = (
            select(PublicationModel)
            .where(
                and_(
                    PublicationModel.publication_year >= start_year,
                    PublicationModel.publication_year <= end_year,
                ),
            )
            .order_by(PublicationModel.publication_year.asc())
        )
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))

    def find_by_variant_associations(self, variant_id: int) -> list[Publication]:
        if variant_id:
            _ = variant_id
        return []

    def find_recent_publications(self, days: int = 30) -> list[Publication]:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(PublicationModel)
            .where(PublicationModel.created_at >= cutoff)
            .order_by(PublicationModel.created_at.desc())
        )
        return self._to_domain_sequence(list(self.session.execute(stmt).scalars()))


class SqlAlchemyPublicationRepository(
    PublicationQueryMixin,
    PublicationRepositoryInterface,
):
    """Domain-facing repository adapter for publications backed by SQLAlchemy."""

    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        if self._session is None:
            message = "Session is not configured"
            raise ValueError(message)
        return self._session

    def _to_domain(self, model: PublicationModel | None) -> Publication | None:
        return PublicationMapper.to_domain(model) if model else None

    def _to_domain_sequence(
        self,
        models: list[PublicationModel],
    ) -> list[Publication]:
        return PublicationMapper.to_domain_sequence(models)

    def create(self, publication: Publication) -> Publication:
        model = PublicationMapper.to_model(publication)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return PublicationMapper.to_domain(model)

    def get_by_id(self, publication_id: int) -> Publication | None:
        model = self.session.get(PublicationModel, publication_id)
        return self._to_domain(model)

    def get_by_id_or_fail(self, publication_id: int) -> Publication:
        model = self.session.get(PublicationModel, publication_id)
        if model is None:
            message = f"Publication with id {publication_id} not found"
            raise ValueError(message)
        return PublicationMapper.to_domain(model)

    def find_by_pubmed_id(self, pubmed_id: str) -> Publication | None:
        stmt = select(PublicationModel).where(PublicationModel.pubmed_id == pubmed_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        return self._to_domain(model)

    def find_by_pmid(self, pmid: str) -> Publication | None:
        """Alias for PubMed ID lookups to satisfy domain contract."""
        return self.find_by_pubmed_id(pmid)

    def find_by_pmc_id(self, pmc_id: str) -> Publication | None:
        stmt = select(PublicationModel).where(PublicationModel.pmc_id == pmc_id)
        return self._to_domain(self.session.execute(stmt).scalar_one_or_none())

    def count(self) -> int:
        stmt = select(func.count()).select_from(PublicationModel)
        return int(self.session.execute(stmt).scalar_one())

    def delete(self, publication_id: int) -> bool:
        model = self.session.get(PublicationModel, publication_id)
        if model is None:
            return False
        self.session.delete(model)
        self.session.commit()
        return True

    def exists(self, publication_id: int) -> bool:
        stmt = select(func.count()).where(PublicationModel.id == publication_id)
        return bool(self.session.execute(stmt).scalar_one())

    def find_all(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Publication]:
        stmt = select(PublicationModel)
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        models = list(self.session.execute(stmt).scalars())
        return self._to_domain_sequence(models)

    def paginate_publications(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        filters: QueryFilters | None = None,
    ) -> tuple[list[Publication], int]:
        stmt = select(PublicationModel)
        if filters:
            for field, value in filters.items():
                column = getattr(PublicationModel, field, None)
                if column is not None and value is not None:
                    stmt = stmt.where(column == value)
        sortable_fields = {
            "title": PublicationModel.title,
            "publication_year": PublicationModel.publication_year,
            "citation_count": PublicationModel.citation_count,
            "relevance_score": PublicationModel.relevance_score,
        }
        sort_column = sortable_fields.get(sort_by)
        if sort_column is not None:
            stmt = stmt.order_by(
                desc(sort_column) if sort_order == "desc" else asc(sort_column),
            )
        offset = max(page - 1, 0) * per_page
        stmt = stmt.offset(offset).limit(per_page)
        records = list(self.session.execute(stmt).scalars())
        total = self.count()
        return self._to_domain_sequence(records), total

    def update(self, publication_id: int, updates: PublicationUpdate) -> Publication:
        model = self.session.get(PublicationModel, publication_id)
        if model is None:
            message = f"Publication with id {publication_id} not found"
            raise ValueError(message)
        for field, value in updates.items():
            if hasattr(model, field):
                setattr(model, field, value)
        model.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(model)
        return PublicationMapper.to_domain(model)

    def update_publication(
        self,
        publication_id: int,
        updates: PublicationUpdate,
    ) -> Publication:
        return self.update(publication_id, updates)


__all__ = ["SqlAlchemyPublicationRepository"]
