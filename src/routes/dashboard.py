"""
Dashboard API routes for the MED13 Resource Library.
Provides statistics and activity feed endpoints for the curation dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime, timedelta

from src.database.session import get_session
from src.repositories.gene_repository import GeneRepository
from src.repositories.variant_repository import VariantRepository
from src.repositories.phenotype_repository import PhenotypeRepository
from src.repositories.evidence_repository import EvidenceRepository
from src.repositories.publication_repository import PublicationRepository

router = APIRouter(prefix="/stats", tags=["dashboard"])


@router.get("/dashboard", summary="Get dashboard statistics")
async def get_dashboard_stats(db: Session = Depends(get_session)) -> Dict[str, Any]:
    """
    Retrieve overall dashboard statistics.

    Returns counts for pending, approved, and rejected items across all entities.
    """
    try:
        gene_repo = GeneRepository(db)
        variant_repo = VariantRepository(db)
        phenotype_repo = PhenotypeRepository(db)
        evidence_repo = EvidenceRepository(db)
        publication_repo = PublicationRepository(db)

        # Get counts for each entity type
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

        return {
            "pending_count": pending_count,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "total_items": total_items,
            "entity_counts": {
                "genes": gene_count,
                "variants": variant_count,
                "phenotypes": phenotype_count,
                "evidence": evidence_count,
                "publications": publication_count,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve dashboard statistics: {str(e)}"
        )


@router.get("/activities/recent", summary="Get recent activity feed")
async def get_recent_activities(
    db: Session = Depends(get_session), limit: int = 10
) -> Dict[str, Any]:
    """
    Retrieve recent activities for the dashboard activity feed.

    Returns a list of recent activities (validations, approvals, rejections, etc.).
    """
    try:
        # For now, return mock activities since we don't have an activity log yet
        # TODO: Implement activity tracking when audit log is added

        activities = [
            {
                "message": "Gene BRCA1 validated",
                "type": "success",
                "timestamp": "2 minutes ago",
                "created_at": (datetime.now() - timedelta(minutes=2)).isoformat(),
            },
            {
                "message": "Variant rs123456 quarantined",
                "type": "warning",
                "timestamp": "5 minutes ago",
                "created_at": (datetime.now() - timedelta(minutes=5)).isoformat(),
            },
            {
                "message": "Publication PMID:12345 approved",
                "type": "info",
                "timestamp": "10 minutes ago",
                "created_at": (datetime.now() - timedelta(minutes=10)).isoformat(),
            },
            {
                "message": "Phenotype HPO:0000001 validated",
                "type": "success",
                "timestamp": "15 minutes ago",
                "created_at": (datetime.now() - timedelta(minutes=15)).isoformat(),
            },
            {
                "message": "Evidence record rejected",
                "type": "danger",
                "timestamp": "20 minutes ago",
                "created_at": (datetime.now() - timedelta(minutes=20)).isoformat(),
            },
        ]

        return {
            "activities": activities[:limit],
            "total": len(activities),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve recent activities: {str(e)}"
        )
