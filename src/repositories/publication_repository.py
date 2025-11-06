"""
Publication repository for MED13 Resource Library.
Data access layer for scientific publication entities with citation queries.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, or_, select

from src.models.database import PublicationModel, PublicationType

from .base import BaseRepository, NotFoundError


class PublicationRepository(BaseRepository[PublicationModel, int]):
    """
    Repository for Publication entities with specialized publication-specific queries.

    Provides data access operations for scientific publications including
    PubMed lookups, citation searches, and relevance filtering.
    """

    @property
    def model_class(self) -> type[PublicationModel]:
        return PublicationModel

    def find_by_pubmed_id(self, pubmed_id: str) -> PublicationModel | None:
        """
        Find a publication by its PubMed ID.

        Args:
            pubmed_id: PubMed identifier

        Returns:
            PublicationModel instance or None if not found
        """
        stmt = select(PublicationModel).where(PublicationModel.pubmed_id == pubmed_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def find_by_pmc_id(self, pmc_id: str) -> PublicationModel | None:
        """
        Find a publication by its PMC ID.

        Args:
            pmc_id: PMC identifier

        Returns:
            PublicationModel instance or None if not found
        """
        stmt = select(PublicationModel).where(PublicationModel.pmc_id == pmc_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def find_by_doi(self, doi: str) -> PublicationModel | None:
        """
        Find a publication by its DOI.

        Args:
            doi: Digital Object Identifier

        Returns:
            PublicationModel instance or None if not found
        """
        stmt = select(PublicationModel).where(PublicationModel.doi == doi)
        return self.session.execute(stmt).scalar_one_or_none()

    def find_by_pmid(self, pmid: str) -> PublicationModel | None:
        """
        Alias for find_by_pubmed_id to align with domain terminology.

        Args:
            pmid: PubMed identifier

        Returns:
            PublicationModel instance or None if not found
        """
        return self.find_by_pubmed_id(pmid)

    def find_by_external_id(self, external_id: str) -> PublicationModel | None:
        """
        Find a publication by any external identifier (PubMed, PMC, DOI).

        Args:
            external_id: External identifier to search for

        Returns:
            PublicationModel instance or None if not found
        """
        stmt = select(PublicationModel).where(
            or_(
                PublicationModel.pubmed_id == external_id,
                PublicationModel.pmc_id == external_id,
                PublicationModel.doi == external_id,
            ),
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def find_by_year(
        self,
        year: int,
        limit: int | None = None,
    ) -> list[PublicationModel]:
        """
        Find publications from a specific year.

        Args:
            year: Publication year
            limit: Maximum number of publications to return

        Returns:
            List of PublicationModel instances from the specified year
        """
        stmt = select(PublicationModel).where(PublicationModel.publication_year == year)
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def find_by_year_range(
        self,
        start_year: int,
        end_year: int,
    ) -> list[PublicationModel]:
        """
        Find publications between two publication years (inclusive).

        Args:
            start_year: Minimum publication year
            end_year: Maximum publication year

        Returns:
            List of PublicationModel instances within the range
        """
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
        return list(self.session.execute(stmt).scalars())

    def find_by_author(
        self,
        author_name: str,
        limit: int | None = None,
    ) -> list[PublicationModel]:
        """
        Find publications by author name (partial match).

        Args:
            author_name: Author name to search for
            limit: Maximum number of publications to return

        Returns:
            List of PublicationModel instances by the author
        """
        search_pattern = f"%{author_name}%"
        stmt = select(PublicationModel).where(
            PublicationModel.authors.ilike(search_pattern),
        )
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def find_by_journal(
        self,
        journal_name: str,
        limit: int | None = None,
    ) -> list[PublicationModel]:
        """
        Find publications in a specific journal.

        Args:
            journal_name: Journal name to search for
            limit: Maximum number of publications to return

        Returns:
            List of PublicationModel instances in the journal
        """
        stmt = select(PublicationModel).where(
            PublicationModel.journal.ilike(f"%{journal_name}%"),
        )
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def find_by_type(
        self,
        pub_type: PublicationType,
        limit: int | None = None,
    ) -> list[PublicationModel]:
        """
        Find publications of a specific type.

        Args:
            pub_type: Publication type
            limit: Maximum number of publications to return

        Returns:
            List of PublicationModel instances of the specified type
        """
        stmt = select(PublicationModel).where(
            PublicationModel.publication_type == pub_type,
        )
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def find_open_access(self, limit: int | None = None) -> list[PublicationModel]:
        """
        Find open access publications.

        Args:
            limit: Maximum number of publications to return

        Returns:
            List of open access PublicationModel instances
        """
        stmt = select(PublicationModel).where(PublicationModel.open_access)
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def search_publications(
        self,
        query: str,
        limit: int = 20,
    ) -> list[PublicationModel]:
        """
        Search publications by title, authors, or abstract.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of matching PublicationModel instances
        """
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
        return list(self.session.execute(stmt).scalars())

    def find_high_impact(
        self,
        min_citations: int = 50,
        limit: int | None = None,
    ) -> list[PublicationModel]:
        """
        Find high-impact publications based on citation count.

        Args:
            min_citations: Minimum citation count
            limit: Maximum number of publications to return

        Returns:
            List of high-impact PublicationModel instances
        """
        stmt = select(PublicationModel).where(
            PublicationModel.citation_count >= min_citations,
        )
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def find_med13_relevant(
        self,
        min_relevance: int = 3,
        limit: int | None = None,
    ) -> list[PublicationModel]:
        """
        Find publications relevant to MED13 research.

        Args:
            min_relevance: Minimum relevance score (1-5)
            limit: Maximum number of publications to return

        Returns:
            List of MED13-relevant PublicationModel instances
        """
        stmt = select(PublicationModel).where(
            and_(
                PublicationModel.relevance_score >= min_relevance,
                PublicationModel.relevance_score.isnot(None),
            ),
        )
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def get_publication_statistics(self) -> dict[str, Any]:
        """
        Get statistics about publications in the database.

        Returns:
            Dictionary with publication statistics
        """
        total_publications = self.count()
        open_access = len(self.find_open_access())

        return {
            "total_publications": total_publications,
            "open_access_publications": open_access,
            "med13_relevant_publications": len(self.find_med13_relevant()),
        }

    def find_recent_publications(
        self,
        days: int = 30,
        limit: int | None = None,
    ) -> list[PublicationModel]:
        """
        Find publications created within the last N days.

        Args:
            days: Number of days to look back from current time
            limit: Optional limit of publications

        Returns:
            List of recently created PublicationModel instances
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(PublicationModel)
            .where(PublicationModel.created_at >= cutoff)
            .order_by(PublicationModel.created_at.desc())
        )
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def find_by_pubmed_id_or_fail(self, pubmed_id: str) -> PublicationModel:
        """
        Find a publication by PubMed ID, raising NotFoundError if not found.

        Args:
            pubmed_id: PubMed identifier to search for

        Returns:
            PublicationModel instance

        Raises:
            NotFoundError: If publication is not found
        """
        publication = self.find_by_pubmed_id(pubmed_id)
        if publication is None:
            message = f"Publication with PubMed ID '{pubmed_id}' not found"
            raise NotFoundError(message)
        return publication
