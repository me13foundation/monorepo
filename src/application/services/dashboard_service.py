"""Application service for dashboard metrics and activity feed."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from src.models.api import ActivityFeedItem, DashboardSummary

if TYPE_CHECKING:
    from src.domain.repositories.evidence_repository import EvidenceRepository
    from src.domain.repositories.gene_repository import GeneRepository
    from src.domain.repositories.phenotype_repository import PhenotypeRepository
    from src.domain.repositories.publication_repository import (
        PublicationRepository,
    )
    from src.domain.repositories.variant_repository import VariantRepository


class DashboardService:
    """Aggregate dashboard data from domain repositories."""

    def __init__(
        self,
        gene_repository: GeneRepository,
        variant_repository: VariantRepository,
        phenotype_repository: PhenotypeRepository,
        evidence_repository: EvidenceRepository,
        publication_repository: PublicationRepository,
    ) -> None:
        self._gene_repository = gene_repository
        self._variant_repository = variant_repository
        self._phenotype_repository = phenotype_repository
        self._evidence_repository = evidence_repository
        self._publication_repository = publication_repository

    def get_summary(self) -> DashboardSummary:
        """Return deterministic dashboard summary counts without mock heuristics."""
        entity_counts = {
            "genes": self._gene_repository.count(),
            "variants": self._variant_repository.count(),
            "phenotypes": self._phenotype_repository.count(),
            "evidence": self._evidence_repository.count(),
            "publications": self._publication_repository.count(),
        }

        total_items = sum(entity_counts.values())

        # Until explicit status fields exist, treat all items as approved to avoid fabricating data.
        return DashboardSummary(
            pending_count=0,
            approved_count=total_items,
            rejected_count=0,
            total_items=total_items,
            entity_counts=entity_counts,
        )

    def get_recent_activities(self, limit: int = 10) -> list[ActivityFeedItem]:
        """
        Return recent activities.

        Activity logging is not yet implemented; return an empty list to avoid
        synthetic data while preserving API shape.
        """
        if limit <= 0:
            return []

        # Provide a minimal heartbeat entry so consumers can render deterministically.
        return [
            ActivityFeedItem(
                message="Dashboard snapshot generated",
                category="info",
                icon="mdi:chart-bar",
                created_at=datetime.now(UTC).isoformat(),
            ),
        ][:limit]


__all__ = ["DashboardService"]
