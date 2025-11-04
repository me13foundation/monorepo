from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol, Sequence

from sqlalchemy.orm import Session

from src.models.database.review import ReviewRecord


@dataclass(frozen=True)
class ReviewFilter:
    entity_type: str | None = None
    status: str | None = None
    priority: str | None = None


class ReviewRepository(Protocol):
    def list(
        self, db: Session, flt: ReviewFilter, limit: int = 100, offset: int = 0
    ) -> List[ReviewRecord]:
        ...

    def bulk_update_status(self, db: Session, ids: Sequence[int], status: str) -> int:
        ...

    def add(self, db: Session, record: ReviewRecord) -> ReviewRecord:
        ...

    def find_by_entity(
        self, db: Session, entity_type: str, entity_id: str
    ) -> Optional[ReviewRecord]:
        ...


class SqlAlchemyReviewRepository:
    def list(
        self, db: Session, flt: ReviewFilter, limit: int = 100, offset: int = 0
    ) -> List[ReviewRecord]:
        query = db.query(ReviewRecord)
        if flt.entity_type:
            query = query.filter(ReviewRecord.entity_type == flt.entity_type)
        if flt.status:
            query = query.filter(ReviewRecord.status == flt.status)
        if flt.priority:
            query = query.filter(ReviewRecord.priority == flt.priority)
        return list(query.offset(offset).limit(limit).all())

    def bulk_update_status(self, db: Session, ids: Sequence[int], status: str) -> int:
        updated = (
            db.query(ReviewRecord)
            .filter(ReviewRecord.id.in_(list(ids)))
            .update({ReviewRecord.status: status}, synchronize_session=False)
        )
        db.commit()
        return int(updated)

    def add(self, db: Session, record: ReviewRecord) -> ReviewRecord:
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def find_by_entity(
        self, db: Session, entity_type: str, entity_id: str
    ) -> Optional[ReviewRecord]:
        return (
            db.query(ReviewRecord)
            .filter(
                ReviewRecord.entity_type == entity_type,
                ReviewRecord.entity_id == entity_id,
            )
            .order_by(ReviewRecord.last_updated.desc())
            .first()
        )


__all__ = [
    "ReviewFilter",
    "ReviewRepository",
    "SqlAlchemyReviewRepository",
]
