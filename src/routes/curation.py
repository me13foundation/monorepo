from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.application.curation.repositories.audit_repository import (
    SqlAlchemyAuditRepository,
)
from src.application.curation.repositories.review_repository import (
    SqlAlchemyReviewRepository,
)
from src.application.curation.services.approval_service import ApprovalService
from src.application.curation.services.comment_service import CommentService
from src.application.curation.services.detail_service import CurationDetailService
from src.application.curation.services.review_service import (
    ReviewQuery,
    ReviewQueueItem,
    ReviewService,
)
from src.application.services.audit_service import AuditTrailService
from src.application.services.authorization_service import AuthorizationService
from src.database.session import get_session
from src.domain.entities.user import User
from src.domain.value_objects.permission import Permission
from src.infrastructure.dependency_injection.container import (
    container,
    get_legacy_dependency_container,
)
from src.routes.auth import get_current_active_user
from src.type_definitions.common import JSONObject, JSONValue

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


class ReviewQueueItemResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: str
    status: str
    priority: str
    quality_score: float | None
    issues: int
    last_updated: datetime | None


def _review_service() -> ReviewService:
    return ReviewService(SqlAlchemyReviewRepository())


def _approval_service() -> ApprovalService:
    return ApprovalService(SqlAlchemyReviewRepository())


def _comment_service() -> CommentService:
    return CommentService(SqlAlchemyAuditRepository())


def _curation_detail_service(
    db: Session = Depends(get_session),
) -> CurationDetailService:
    # Get unified container with legacy support

    container = get_legacy_dependency_container()
    return container.create_curation_detail_service(db)


_audit_trail_service = AuditTrailService(SqlAlchemyAuditRepository())


def _audit_service() -> AuditTrailService:
    return _audit_trail_service


async def _require_permission(
    current_user: User,
    permission: Permission,
    authz_service: AuthorizationService,
) -> None:
    await authz_service.require_permission(current_user.id, permission)


@router.get("/queue", response_model=list[ReviewQueueItemResponse])
async def list_queue(
    entity_type: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    authz_service: AuthorizationService = Depends(container.get_authorization_service),
) -> list[ReviewQueueItemResponse]:
    await _require_permission(
        current_user,
        Permission.CURATION_REVIEW,
        authz_service,
    )
    service = _review_service()
    results: list[ReviewQueueItem] = service.list_queue(
        db,
        ReviewQuery(
            entity_type=entity_type,
            status=status,
            priority=priority,
            limit=limit,
            offset=offset,
        ),
    )
    return [
        ReviewQueueItemResponse(
            id=item.id,
            entity_type=item.entity_type,
            entity_id=item.entity_id,
            status=item.status,
            priority=item.priority,
            quality_score=item.quality_score,
            issues=item.issues,
            last_updated=item.last_updated,
        )
        for item in results
    ]


@router.post("/submit", status_code=status.HTTP_201_CREATED)
async def submit(
    req: SubmitRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    authz_service: AuthorizationService = Depends(container.get_authorization_service),
    audit_service: AuditTrailService = Depends(_audit_service),
) -> dict[str, int]:
    await _require_permission(
        current_user,
        Permission.CURATION_REVIEW,
        authz_service,
    )
    service = _review_service()
    created = service.submit(db, req.entity_type, req.entity_id, req.priority)
    audit_service.record_action(
        db,
        action="curation.submit",
        target=(req.entity_type, req.entity_id),
        actor_id=current_user.id,
        details={"priority": req.priority, "review_id": created.id},
    )
    return {"id": created.id}


@router.post("/bulk")
async def bulk(
    req: BulkRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    authz_service: AuthorizationService = Depends(container.get_authorization_service),
    audit_service: AuditTrailService = Depends(_audit_service),
) -> dict[str, int]:
    await _require_permission(
        current_user,
        Permission.CURATION_APPROVE,
        authz_service,
    )
    service = _approval_service()
    ids_list = list(req.ids)
    ids_payload: list[JSONValue] = [int(_id) for _id in ids_list]
    if req.action == "approve":
        count = service.approve(db, ids_list)
    elif req.action == "reject":
        count = service.reject(db, ids_list)
    elif req.action == "quarantine":
        count = service.quarantine(db, ids_list)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    audit_service.record_action(
        db,
        action=f"curation.bulk.{req.action}",
        target=("curation_queue", ",".join(str(_id) for _id in ids_list)),
        actor_id=current_user.id,
        details={"ids": ids_payload, "updated": count},
    )
    return {"updated": count}


@router.post("/comment", status_code=status.HTTP_201_CREATED)
async def comment(
    req: CommentRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    authz_service: AuthorizationService = Depends(container.get_authorization_service),
    audit_service: AuditTrailService = Depends(_audit_service),
) -> dict[str, int]:
    await _require_permission(
        current_user,
        Permission.CURATION_REVIEW,
        authz_service,
    )
    service = _comment_service()
    comment_id = service.add_comment(
        db,
        req.entity_type,
        req.entity_id,
        req.comment,
        req.user,
    )
    audit_service.record_action(
        db,
        action="curation.comment",
        target=(req.entity_type, req.entity_id),
        actor_id=current_user.id,
        details={"comment_id": comment_id, "delegated_user": req.user},
    )
    return {"id": comment_id}


@router.get(
    "/{entity_type}/{entity_id}",
    response_model=JSONObject,
)
async def get_curated_detail(
    entity_type: str,
    entity_id: str,
    service: CurationDetailService = Depends(_curation_detail_service),
    current_user: User = Depends(get_current_active_user),
    authz_service: AuthorizationService = Depends(container.get_authorization_service),
) -> JSONObject:
    """
    Retrieve enriched detail payload for a queued entity.

    Currently supports variant entities and returns a structure compatible
    with the Dash curation interface.
    """
    await _require_permission(
        current_user,
        Permission.CURATION_REVIEW,
        authz_service,
    )
    try:
        detail = service.get_detail(entity_type, entity_id)
        return cast("JSONObject", detail.to_serializable())
    except ValueError as exc:
        message = str(exc)
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in message.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=message) from exc
