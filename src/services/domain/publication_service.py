"""
Publication service for MED13 Resource Library.
Business logic for scientific publication operations.
"""

from sqlalchemy.orm import Session

from src.domain.entities.publication import Publication
from src.infrastructure.repositories import (
    SqlAlchemyEvidenceRepository,
    SqlAlchemyPublicationRepository,
)
from src.services.domain.base_service import BaseService

PublicationStatisticsValue = int | float | bool | str | None


class PublicationService(BaseService[SqlAlchemyPublicationRepository]):
    """
    Service for publication business logic and operations.

    Provides high-level operations for publication management including
    citation analysis and relevance assessment.
    """

    def __init__(
        self,
        session: Session | None = None,
        publication_repository: SqlAlchemyPublicationRepository | None = None,
    ):
        super().__init__(session)
        self.publication_repo = (
            publication_repository
            if publication_repository
            else SqlAlchemyPublicationRepository(session)
        )
        self.evidence_repo = SqlAlchemyEvidenceRepository(session)

    @property
    def repository(self) -> SqlAlchemyPublicationRepository:
        return self.publication_repo

    def find_med13_relevant_publications(
        self,
        min_relevance: int = 3,
        limit: int | None = None,
    ) -> list[Publication]:
        """
        Find publications relevant to MED13 research.

        Args:
            min_relevance: Minimum relevance score (1-5)
            limit: Maximum number of publications to return

        Returns:
            List of MED13-relevant Publication entities
        """
        return self.publication_repo.find_med13_relevant(min_relevance, limit)

    def search_publications(self, query: str, limit: int = 20) -> list[Publication]:
        """
        Search publications by title, authors, or abstract.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching Publication entities
        """
        return self.publication_repo.search_publications(query, limit)

    def get_publication_with_evidence(
        self,
        publication_id: int,
    ) -> Publication | None:
        """
        Get a publication with its associated evidence loaded.

        Args:
            publication_id: Publication ID to retrieve

        Returns:
            Publication with evidence relationship loaded
        """
        publication = self.publication_repo.get_by_id(publication_id)
        if publication:
            evidence = self.evidence_repo.find_by_publication(publication_id)
            for record in evidence:
                publication.add_evidence(record)
        return publication

    def get_publication_statistics(self) -> dict[str, PublicationStatisticsValue]:
        raw_stats: dict[
            str,
            PublicationStatisticsValue,
        ] = self.publication_repo.get_publication_statistics()
        return dict(raw_stats)
