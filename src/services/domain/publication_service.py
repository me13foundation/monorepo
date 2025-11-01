"""
Publication service for MED13 Resource Library.
Business logic for scientific publication operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from src.repositories import PublicationRepository, EvidenceRepository
from src.models.database import PublicationModel
from src.services.domain.base_service import BaseService


class PublicationService(BaseService[PublicationModel]):
    """
    Service for publication business logic and operations.

    Provides high-level operations for publication management including
    citation analysis and relevance assessment.
    """

    def __init__(self, session: Optional[Session] = None):
        super().__init__(session)
        self.publication_repo = PublicationRepository(session)
        self.evidence_repo = EvidenceRepository(session)

    @property
    def repository(self) -> PublicationRepository:
        return self.publication_repo

    def find_med13_relevant_publications(
        self, min_relevance: int = 3, limit: Optional[int] = None
    ) -> List[PublicationModel]:
        """
        Find publications relevant to MED13 research.

        Args:
            min_relevance: Minimum relevance score (1-5)
            limit: Maximum number of publications to return

        Returns:
            List of MED13-relevant PublicationModel instances
        """
        return self.publication_repo.find_med13_relevant(min_relevance, limit)

    def search_publications(
        self, query: str, limit: int = 20
    ) -> List[PublicationModel]:
        """
        Search publications by title, authors, or abstract.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching PublicationModel instances
        """
        return self.publication_repo.search_publications(query, limit)

    def get_publication_with_evidence(
        self, publication_id: int
    ) -> Optional[PublicationModel]:
        """
        Get a publication with its associated evidence loaded.

        Args:
            publication_id: Publication ID to retrieve

        Returns:
            PublicationModel with evidence relationship loaded
        """
        publication = self.publication_repo.get_by_id(publication_id)
        if publication:
            publication.evidence = self.evidence_repo.find_by_publication(
                publication_id
            )
        return publication
