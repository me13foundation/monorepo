from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from src.models.database.audit import AuditLog


class AuditRepository(Protocol):
    def record(self, db: Session, log: AuditLog) -> AuditLog: ...


class SqlAlchemyAuditRepository:
    def record(self, db: Session, log: AuditLog) -> AuditLog:
        db.add(log)
        db.commit()
        db.refresh(log)
        return log


__all__ = ["AuditRepository", "SqlAlchemyAuditRepository"]
