"""
Dashboard API routes for the MED13 Resource Library.
Provides statistics and activity feed endpoints for the curation dashboard.
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database.session import get_session
from src.infrastructure.repositories import (
    SqlAlchemyEvidenceRepository,
    SqlAlchemyGeneRepository,
    SqlAlchemyPhenotypeRepository,
    SqlAlchemyPublicationRepository,
    SqlAlchemyVariantRepository,
)
from src.models.api import ActivityFeedItem, DashboardSummary
from src.routes.serializers import build_activity_feed_item, build_dashboard_summary

router = APIRouter(prefix="/stats", tags=["dashboard"])


class RecentActivitiesResponse(BaseModel):
    """Recent activity list response."""

    activities: list[ActivityFeedItem]
    total: int


@router.get(
    "/dashboard",
    summary="Get dashboard statistics",
    response_model=DashboardSummary,
)
async def get_dashboard_stats(db: Session = Depends(get_session)) -> DashboardSummary:
    """
    Retrieve overall dashboard statistics.

    Returns counts for pending, approved, and rejected items across all entities.
    """
    try:
        gene_repo = SqlAlchemyGeneRepository(db)
        variant_repo = SqlAlchemyVariantRepository(db)
        phenotype_repo = SqlAlchemyPhenotypeRepository(db)
        evidence_repo = SqlAlchemyEvidenceRepository(db)
        publication_repo = SqlAlchemyPublicationRepository(db)

        # Get counts for each entity type using the shared adapters
        gene_count = gene_repo.count()
        variant_count = variant_repo.count()
        phenotype_count = phenotype_repo.count()
        evidence_count = evidence_repo.count()
        publication_count = publication_repo.count()

        # For now, we'll use a simple heuristic:
        # - Pending: recently added items (last 7 days) or items needing review
        # - Approved: items that have been validated and approved
        # - Rejected: items that have been marked as rejected
        # Since we don't have explicit status fields yet, we'll estimate based on counts

        # TODO: When status/validation fields are added, update this logic
        # For now, return estimated counts based on entity totals
        total_items = (
            gene_count
            + variant_count
            + phenotype_count
            + evidence_count
            + publication_count
        )

        # Mock distribution for now (80% approved, 15% pending, 5% rejected)
        approved_count = int(total_items * 0.8) if total_items > 0 else 0
        pending_count = int(total_items * 0.15) if total_items > 0 else 0
        rejected_count = int(total_items * 0.05) if total_items > 0 else 0

        # If we have no items, return default mock values
        if total_items == 0:
            approved_count = 892
            pending_count = 145
            rejected_count = 67

        entity_counts = {
            "genes": gene_count,
            "variants": variant_count,
            "phenotypes": phenotype_count,
            "evidence": evidence_count,
            "publications": publication_count,
        }

        return build_dashboard_summary(
            entity_counts,
            pending_count=pending_count,
            approved_count=approved_count,
            rejected_count=rejected_count,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve dashboard statistics: {e!s}",
        )


@router.get(
    "/activities/recent",
    summary="Get recent activity feed",
    response_model=RecentActivitiesResponse,
)
async def get_recent_activities(
    db: Session = Depends(get_session),
    limit: int = 10,
) -> RecentActivitiesResponse:
    """
    Retrieve recent activities for the dashboard activity feed.

    Returns a list of recent activities (validations, approvals, rejections, etc.).
    """
    try:
        # For now, return mock activities since we don't have an activity log yet
        # TODO: Implement activity tracking when audit log is added

        now = datetime.now(UTC)
        activities = [
            build_activity_feed_item(
                "Gene BRCA1 validated",
                category="success",
                icon="mdi:check-circle",
                timestamp=now - timedelta(minutes=2),
            ),
            build_activity_feed_item(
                "Variant rs123456 quarantined",
                category="warning",
                icon="mdi:alert",
                timestamp=now - timedelta(minutes=5),
            ),
            build_activity_feed_item(
                "Publication PMID:12345 approved",
                category="info",
                icon="mdi:file-document",
                timestamp=now - timedelta(minutes=10),
            ),
            build_activity_feed_item(
                "Phenotype HPO:0000001 validated",
                category="success",
                icon="mdi:clipboard-check",
                timestamp=now - timedelta(minutes=15),
            ),
            build_activity_feed_item(
                "Evidence record rejected",
                category="danger",
                icon="mdi:close-circle",
                timestamp=now - timedelta(minutes=20),
            ),
        ]

        limited = activities[:limit]
        return RecentActivitiesResponse(activities=limited, total=len(activities))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve recent activities: {e!s}",
        )
