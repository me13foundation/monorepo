"""Curation-related research space routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.application.curation.services.review_service import ReviewQuery, ReviewService
from src.application.services.membership_management_service import (
    MembershipManagementService,
)
from src.database.session import get_session
from src.domain.entities.user import User
from src.routes.auth import get_current_active_user
from src.routes.research_spaces.dependencies import (
    get_curation_service,
    get_membership_service,
    verify_space_membership,
)
from src.routes.research_spaces.schemas import (
    CurationQueueItemResponse,
    CurationQueueResponse,
    CurationStatsResponse,
)

from .router import (
    HTTP_500_INTERNAL_SERVER_ERROR,
    research_spaces_router,
)


class SpaceCurationQueueParams(BaseModel):
    entity_type: str | None = Field(None, description="Filter by entity type")
    status: str | None = Field(None, description="Filter by status")
    priority: str | None = Field(None, description="Filter by priority")
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=100)

    model_config = {"extra": "ignore"}


@research_spaces_router.get(
    "/{space_id}/curation/stats",
    response_model=CurationStatsResponse,
    summary="Get curation statistics",
    description="Get curation statistics for a research space",
)
def get_space_curation_stats(
    space_id: UUID,
    current_user: User = Depends(get_current_active_user),
    membership_service: MembershipManagementService = Depends(get_membership_service),
    curation_service: ReviewService = Depends(get_curation_service),
    session: Session = Depends(get_session),
) -> CurationStatsResponse:
    """Get curation statistics for a research space."""
    verify_space_membership(
        space_id,
        current_user.id,
        membership_service,
        session,
        current_user.role,
    )

    try:
        stats = curation_service.get_stats(session, str(space_id))
        return CurationStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get curation stats: {e!s}",
        ) from e


@research_spaces_router.get(
    "/{space_id}/curation/queue",
    response_model=CurationQueueResponse,
    summary="List curation queue",
    description="Get curation queue items for a research space",
)
def list_space_curation_queue(
    space_id: UUID,
    params: SpaceCurationQueueParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    membership_service: MembershipManagementService = Depends(get_membership_service),
    curation_service: ReviewService = Depends(get_curation_service),
    session: Session = Depends(get_session),
) -> CurationQueueResponse:
    """List curation queue items for a research space."""
    verify_space_membership(
        space_id,
        current_user.id,
        membership_service,
        session,
        current_user.role,
    )

    try:
        query = ReviewQuery(
            entity_type=params.entity_type,
            status=params.status,
            priority=params.priority,
            research_space_id=str(space_id),
            limit=params.limit,
            offset=params.skip,
        )
        items = curation_service.list_queue(session, query)
        return CurationQueueResponse(
            items=[
                CurationQueueItemResponse(
                    id=item.id,
                    entity_type=item.entity_type,
                    entity_id=item.entity_id,
                    status=item.status,
                    priority=item.priority,
                    quality_score=item.quality_score,
                    issues=item.issues,
                    last_updated=(
                        item.last_updated.isoformat() if item.last_updated else None
                    ),
                )
                for item in items
            ],
            total=len(items),
            skip=params.skip,
            limit=params.limit,
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get curation queue: {e!s}",
        ) from e
