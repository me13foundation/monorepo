from __future__ import annotations

from typing import Any, Dict, List, Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database.session import get_session
from src.infrastructure.dependency_injection import DependencyContainer
from src.application.curation.repositories.review_repository import (
    SqlAlchemyReviewRepository,
)
from src.application.curation.repositories.audit_repository import (
    SqlAlchemyAuditRepository,
)
from src.application.curation.services.review_service import ReviewService, ReviewQuery
from src.application.curation.services.approval_service import ApprovalService
from src.application.curation.services.comment_service import CommentService
from src.application.curation.services.detail_service import CurationDetailService
from src.models.database.review import ReviewRecord


router = APIRouter(prefix="/curation", tags=["curation"])


class QueueQuery(BaseModel):
    entity_type: str | None = Field(default=None)
    status: str | None = Field(default=None)
    priority: str | None = Field(default=None)
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class SubmitRequest(BaseModel):
    entity_type: str
    entity_id: str
    priority: str = Field(default="medium")


class BulkRequest(BaseModel):
    ids: Sequence[int]
    action: str = Field(pattern="^(approve|reject|quarantine)$")


class CommentRequest(BaseModel):
    entity_type: str
    entity_id: str
    comment: str
    user: str | None = None


def _review_service() -> ReviewService:
    return ReviewService(SqlAlchemyReviewRepository())


def _approval_service() -> ApprovalService:
    return ApprovalService(SqlAlchemyReviewRepository())


def _comment_service() -> CommentService:
    return CommentService(SqlAlchemyAuditRepository())


def _curation_detail_service(
    db: Session = Depends(get_session),
) -> CurationDetailService:
    container = DependencyContainer(db)
    return container.create_curation_detail_service()


@router.get("/queue", response_model=list[Dict[str, Any]])
def list_queue(
    entity_type: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_session),
) -> List[Dict[str, Any]]:
    service = _review_service()
    results: List[ReviewRecord] = service.list_queue(
        db,
        ReviewQuery(
            entity_type=entity_type,
            status=status,
            priority=priority,
            limit=limit,
            offset=offset,
        ),
    )
    # Minimal JSON response until dedicated API models are defined
    return [
        {
            "id": r.id,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "status": r.status,
            "priority": r.priority,
            "quality_score": r.quality_score,
            "issues": r.issues,
            "last_updated": r.last_updated.isoformat() if r.last_updated else None,
        }
        for r in results
    ]


@router.post("/submit", status_code=status.HTTP_201_CREATED)
def submit(req: SubmitRequest, db: Session = Depends(get_session)) -> Dict[str, int]:
    service = _review_service()
    created = service.submit(db, req.entity_type, req.entity_id, req.priority)
    return {"id": created.id}


@router.post("/bulk")
def bulk(req: BulkRequest, db: Session = Depends(get_session)) -> Dict[str, int]:
    service = _approval_service()
    if req.action == "approve":
        count = service.approve(db, req.ids)
    elif req.action == "reject":
        count = service.reject(db, req.ids)
    elif req.action == "quarantine":
        count = service.quarantine(db, req.ids)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    return {"updated": count}


@router.post("/comment", status_code=status.HTTP_201_CREATED)
def comment(req: CommentRequest, db: Session = Depends(get_session)) -> Dict[str, int]:
    service = _comment_service()
    comment_id = service.add_comment(
        db, req.entity_type, req.entity_id, req.comment, req.user
    )
    return {"id": comment_id}


@router.get("/{entity_type}/{entity_id}", response_model=Dict[str, Any])
def get_curated_detail(
    entity_type: str,
    entity_id: str,
    service: CurationDetailService = Depends(_curation_detail_service),
) -> Dict[str, Any]:
    """
    Retrieve enriched detail payload for a queued entity.

    Currently supports variant entities and returns a structure compatible
    with the Dash curation interface.
    """
    try:
        detail = service.get_detail(entity_type, entity_id)
        return dict(detail.to_serializable())
    except ValueError as exc:
        message = str(exc)
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in message.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=message) from exc
