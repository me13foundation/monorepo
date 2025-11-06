from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, TypedDict

from src.models.database.review import ReviewRecord

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@dataclass(frozen=True)
class ReviewFilter:
    entity_type: str | None = None
    status: str | None = None
    priority: str | None = None


class ReviewRecordLike(TypedDict, total=False):
    id: int
    entity_type: str
    entity_id: str
    status: str
    priority: str
    quality_score: float | None
    issues: int
    last_updated: object | None


class ReviewRepository(Protocol):
    def list_records(
        self,
        db: Session,
        flt: ReviewFilter,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ReviewRecordLike]:
        ...

    def bulk_update_status(
        self,
        db: Session,
        ids: tuple[int, ...] | list[int],
        status: str,
    ) -> int:
        ...

    def add(self, db: Session, record: object) -> ReviewRecordLike:
        ...

    def find_by_entity(
        self,
        db: Session,
        entity_type: str,
        entity_id: str,
    ) -> ReviewRecordLike | None:
        ...


class SqlAlchemyReviewRepository:
    def list_records(
        self,
        db: Session,
        flt: ReviewFilter,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ReviewRecordLike]:
        query = db.query(ReviewRecord)
        if flt.entity_type:
            query = query.filter(ReviewRecord.entity_type == flt.entity_type)
        if flt.status:
            query = query.filter(ReviewRecord.status == flt.status)
        if flt.priority:
            query = query.filter(ReviewRecord.priority == flt.priority)
        orm_records = list(query.offset(offset).limit(limit).all())
        return [
            {
                "id": r.id,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "status": r.status,
                "priority": r.priority,
                "quality_score": r.quality_score,
                "issues": r.issues,
                "last_updated": r.last_updated,
            }
            for r in orm_records
        ]

    def bulk_update_status(
        self,
        db: Session,
        ids: tuple[int, ...] | list[int],
        status: str,
    ) -> int:
        updated = (
            db.query(ReviewRecord)
            .filter(ReviewRecord.id.in_(list(ids)))
            .update({ReviewRecord.status: status}, synchronize_session=False)
        )
        db.commit()
        return int(updated)

    def add(self, db: Session, record: object) -> ReviewRecordLike:
        db.add(record)
        db.commit()
        db.refresh(record)
        # Build a dict view of the saved record
        return {
            "id": record.id,  # type: ignore[attr-defined]
            "entity_type": record.entity_type,  # type: ignore[attr-defined]
            "entity_id": record.entity_id,  # type: ignore[attr-defined]
            "status": record.status,  # type: ignore[attr-defined]
            "priority": record.priority,  # type: ignore[attr-defined]
            "quality_score": getattr(record, "quality_score", None),
            "issues": getattr(record, "issues", 0),
            "last_updated": getattr(record, "last_updated", None),
        }

    def find_by_entity(
        self,
        db: Session,
        entity_type: str,
        entity_id: str,
    ) -> ReviewRecordLike | None:
        orm = (
            db.query(ReviewRecord)
            .filter(
                ReviewRecord.entity_type == entity_type,
                ReviewRecord.entity_id == entity_id,
            )
            .order_by(ReviewRecord.last_updated.desc())
            .first()
        )
        if orm is None:
            return None
        return {
            "id": orm.id,
            "entity_type": orm.entity_type,
            "entity_id": orm.entity_id,
            "status": orm.status,
            "priority": orm.priority,
            "quality_score": orm.quality_score,
            "issues": orm.issues,
            "last_updated": orm.last_updated,
        }


__all__ = [
    "ReviewFilter",
    "ReviewRepository",
    "SqlAlchemyReviewRepository",
]
