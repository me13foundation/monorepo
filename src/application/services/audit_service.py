"""
Security audit trail helper.

Provides a thin service wrapper around the audit repository so high-risk routes can
emit append-only audit events without duplicating serialization code.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from src.models.database.audit import AuditLog

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from collections.abc import Mapping
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.application.curation.repositories.audit_repository import AuditRepository


class AuditTrailService:
    """Append-only audit logger for sensitive mutations."""

    def __init__(self, repository: AuditRepository) -> None:
        self._repository = repository

    def record_action(
        self,
        db: Session,
        *,
        action: str,
        target: tuple[str, str],
        actor_id: UUID | str | None,
        details: Mapping[str, Any] | None = None,
    ) -> AuditLog:
        """
        Persist an audit record describing the action that was taken.

        Args:
            db: SQLAlchemy session to use for persistence
            action: Machine-readable action name (e.g. curation.submit)
            target: Tuple of (entity_type, entity_id) describing the affected record
            actor_id: User responsible for the change
            details: Optional structured metadata that will be JSON encoded
        """
        entity_type, entity_id = target
        normalized_actor = str(actor_id) if actor_id else None
        serialized_details = (
            json.dumps(details, separators=(",", ":"), sort_keys=True)
            if details
            else None
        )
        log = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user=normalized_actor,
            details=serialized_details,
        )
        return self._repository.record(db, log)


__all__ = ["AuditTrailService"]
