"""
Dashboard API routes for the MED13 Resource Library.
Provides statistics and activity feed endpoints for the admin dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.application.services.dashboard_service import DashboardService
from src.database.session import get_session
from src.infrastructure.dependency_injection.dependencies import (
    get_legacy_dependency_container,
)
from src.models.api import ActivityFeedItem, DashboardSummary

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class RecentActivitiesResponse(BaseModel):
    """Recent activity list response."""

    activities: list[ActivityFeedItem]
    total: int


def _get_dashboard_service(db: Session) -> DashboardService:
    container = get_legacy_dependency_container()
    return container.create_dashboard_service(db)


@router.get(
    "",
    summary="Get dashboard statistics",
    response_model=DashboardSummary,
)
async def get_dashboard_stats(
    db: Session = Depends(get_session),
) -> DashboardSummary:
    """
    Retrieve overall dashboard statistics.

    Returns counts for tracked entities without synthetic status heuristics.
    """
    try:
        service = _get_dashboard_service(db)
        return service.get_summary()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve dashboard statistics: {exc!s}",
        ) from exc


@router.get(
    "/activities",
    summary="Get recent activity feed",
    response_model=RecentActivitiesResponse,
)
async def get_recent_activities(
    db: Session = Depends(get_session),
    limit: int = 10,
) -> RecentActivitiesResponse:
    """
    Retrieve recent activities for the dashboard activity feed.
    """
    try:
        service = _get_dashboard_service(db)
        activities = list(service.get_recent_activities(limit))
        return RecentActivitiesResponse(activities=activities, total=len(activities))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve recent activities: {exc!s}",
        ) from exc
