"""
Evidence repository for MED13 Resource Library.
Data access layer for evidence entities linking variants and phenotypes.
"""

from typing import Any

from sqlalchemy import and_, or_, select

from src.models.database import (
    EvidenceLevel,
    EvidenceModel,
    EvidenceType,
    VariantModel,
)

from .base import BaseRepository


class EvidenceRepository(BaseRepository[EvidenceModel, int]):
    """
    Repository for Evidence entities with specialized evidence-specific queries.

    Provides data access operations for evidence linking variants and phenotypes
    including confidence filtering, type queries, and relationship traversals.
    """

    @property
    def model_class(self) -> type[EvidenceModel]:
        return EvidenceModel

    def find_by_variant(
        self,
        variant_id: int,
        limit: int | None = None,
    ) -> list[EvidenceModel]:
        """
        Find all evidence for a specific variant.

        Args:
            variant_id: Variant ID to find evidence for
            limit: Maximum number of evidence records to return

        Returns:
            List of EvidenceModel instances for the variant
        """
        stmt = select(EvidenceModel).where(EvidenceModel.variant_id == variant_id)
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def find_by_phenotype(
        self,
        phenotype_id: int,
        limit: int | None = None,
    ) -> list[EvidenceModel]:
        """
        Find all evidence for a specific phenotype.

        Args:
            phenotype_id: Phenotype ID to find evidence for
            limit: Maximum number of evidence records to return

        Returns:
            List of EvidenceModel instances for the phenotype
        """
        stmt = select(EvidenceModel).where(EvidenceModel.phenotype_id == phenotype_id)
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def find_by_variant_and_phenotype(
        self,
        variant_id: int,
        phenotype_id: int,
    ) -> list[EvidenceModel]:
        """
        Find evidence linking a specific variant and phenotype.

        Args:
            variant_id: Variant ID
            phenotype_id: Phenotype ID

        Returns:
            List of EvidenceModel instances linking the variant and phenotype
        """
        stmt = select(EvidenceModel).where(
            and_(
                EvidenceModel.variant_id == variant_id,
                EvidenceModel.phenotype_id == phenotype_id,
            ),
        )
        return list(self.session.execute(stmt).scalars())

    def find_by_publication(
        self,
        publication_id: int,
        limit: int | None = None,
    ) -> list[EvidenceModel]:
        """
        Find all evidence from a specific publication.

        Args:
            publication_id: Publication ID to find evidence for
            limit: Maximum number of evidence records to return

        Returns:
            List of EvidenceModel instances from the publication
        """
        stmt = select(EvidenceModel).where(
            EvidenceModel.publication_id == publication_id,
        )
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def find_by_gene(self, gene_id: int) -> list[EvidenceModel]:
        """
        Find evidence associated with variants belonging to a specific gene.

        Args:
            gene_id: Gene ID to filter variants by

        Returns:
            List of EvidenceModel instances linked to the gene
        """
        stmt = (
            select(EvidenceModel)
            .join(EvidenceModel.variant)
            .where(VariantModel.gene_id == gene_id)
        )
        return list(self.session.execute(stmt).scalars())

    def find_by_evidence_level(
        self,
        level: EvidenceLevel,
        limit: int | None = None,
    ) -> list[EvidenceModel]:
        """
        Find evidence with specific confidence level.

        Args:
            level: Evidence confidence level
            limit: Maximum number of evidence records to return

        Returns:
            List of EvidenceModel instances with the specified level
        """
        stmt = select(EvidenceModel).where(EvidenceModel.evidence_level == level)
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def find_by_evidence_type(
        self,
        evidence_type: EvidenceType,
        limit: int | None = None,
    ) -> list[EvidenceModel]:
        """
        Find evidence of specific type.

        Args:
            evidence_type: Type of evidence
            limit: Maximum number of evidence records to return

        Returns:
            List of EvidenceModel instances of the specified type
        """
        stmt = select(EvidenceModel).where(EvidenceModel.evidence_type == evidence_type)
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def find_by_confidence_score(
        self,
        min_score: float,
        max_score: float,
    ) -> list[EvidenceModel]:
        """
        Find evidence within a confidence score range.

        Args:
            min_score: Minimum confidence score (inclusive)
            max_score: Maximum confidence score (inclusive)

        Returns:
            List of EvidenceModel instances whose confidence scores fall within the range
        """
        stmt = select(EvidenceModel).where(
            EvidenceModel.confidence_score >= min_score,
            EvidenceModel.confidence_score <= max_score,
        )
        return list(self.session.execute(stmt).scalars())

    def find_high_confidence_evidence(
        self,
        limit: int | None = None,
    ) -> list[EvidenceModel]:
        """
        Find evidence with high confidence (Definitive or Strong).

        Args:
            limit: Maximum number of evidence records to return

        Returns:
            List of high-confidence EvidenceModel instances
        """
        stmt = select(EvidenceModel).where(
            or_(
                EvidenceModel.evidence_level == EvidenceLevel.DEFINITIVE,
                EvidenceModel.evidence_level == EvidenceLevel.STRONG,
            ),
        )
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def find_peer_reviewed_evidence(
        self,
        limit: int | None = None,
    ) -> list[EvidenceModel]:
        """
        Find evidence from peer-reviewed sources.

        Args:
            limit: Maximum number of evidence records to return

        Returns:
            List of peer-reviewed EvidenceModel instances
        """
        stmt = select(EvidenceModel).where(
            EvidenceModel.peer_reviewed,  # type: ignore[attr-defined]
        )
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def get_evidence_statistics(self) -> dict[str, Any]:
        """
        Get statistics about evidence in the database.

        Returns:
            Dictionary with evidence statistics
        """
        total_evidence = self.count()
        high_confidence = len(self.find_high_confidence_evidence())
        peer_reviewed = len(self.find_peer_reviewed_evidence())

        return {
            "total_evidence": total_evidence,
            "high_confidence_evidence": high_confidence,
            "peer_reviewed_evidence": peer_reviewed,
        }

    def find_by_source(self, source: str) -> list[EvidenceModel]:
        """
        Placeholder for evidence source lookup.

        Evidence source metadata is not currently stored, so this returns an empty list.
        """
        _ = source  # Prevent unused variable warning
        return []

    def find_relationship_evidence(
        self,
        variant_id: int,
        phenotype_id: int,
        min_confidence: float = 0.0,
    ) -> list[EvidenceModel]:
        """
        Find evidence supporting the relationship between a variant and phenotype.

        Args:
            variant_id: Variant ID
            phenotype_id: Phenotype ID
            min_confidence: Minimum confidence score (0.0-1.0)

        Returns:
            List of EvidenceModel instances supporting the relationship
        """
        stmt = select(EvidenceModel).where(
            and_(
                EvidenceModel.variant_id == variant_id,
                EvidenceModel.phenotype_id == phenotype_id,
                EvidenceModel.confidence_score >= min_confidence,
            ),
        )
        return list(self.session.execute(stmt).scalars())
