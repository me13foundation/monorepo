from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from sqlalchemy.orm import Session

from src.application.curation.repositories.review_repository import (
    ReviewRepository,
    ReviewFilter,
)
from src.models.database.review import ReviewRecord


@dataclass(frozen=True)
class ReviewQuery:
    entity_type: str | None = None
    status: str | None = None
    priority: str | None = None
    limit: int = 100
    offset: int = 0


class ReviewService:
    def __init__(self, repository: ReviewRepository) -> None:
        self._repository = repository

    def list_queue(self, db: Session, query: ReviewQuery) -> List[ReviewRecord]:
        return self._repository.list(
            db,
            ReviewFilter(
                entity_type=query.entity_type,
                status=query.status,
                priority=query.priority,
            ),
            limit=query.limit,
            offset=query.offset,
        )

    def submit(
        self, db: Session, entity_type: str, entity_id: str, priority: str = "medium"
    ) -> ReviewRecord:
        record = ReviewRecord(
            entity_type=entity_type,
            entity_id=entity_id,
            status="pending",
            priority=priority,
        )
        return self._repository.add(db, record)

    def bulk_update_status(self, db: Session, ids: Sequence[int], status: str) -> int:
        return self._repository.bulk_update_status(db, ids, status)


__all__ = ["ReviewService", "ReviewQuery"]
