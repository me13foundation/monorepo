"""
Security audit trail helper.

Provides a thin service wrapper around the audit repository so high-risk routes can
emit append-only audit events without duplicating serialization code.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from src.models.database.audit import AuditLog

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from collections.abc import Mapping
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.application.curation.repositories.audit_repository import AuditRepository
    from src.type_definitions.common import AuditContext, JSONValue


class AuditTrailService:
    """Append-only audit logger for sensitive mutations."""

    def __init__(self, repository: AuditRepository) -> None:
        self._repository = repository

    def record_action(  # noqa: PLR0913 - audit records require many fields
        self,
        db: Session,
        *,
        action: str,
        target: tuple[str, str],
        actor_id: UUID | str | None,
        details: Mapping[str, JSONValue] | None = None,
        context: AuditContext | None = None,
        success: bool | None = True,
    ) -> AuditLog:
        """
        Persist an audit record describing the action that was taken.

        Args:
            db: SQLAlchemy session to use for persistence
            action: Machine-readable action name (e.g. curation.submit)
            target: Tuple of (entity_type, entity_id) describing the affected record
            actor_id: User responsible for the change
            details: Optional structured metadata that will be JSON encoded
            context: Optional request metadata captured for audit logging
            success: Whether the action succeeded (None if unknown)
        """
        entity_type, entity_id = target
        normalized_actor = str(actor_id) if actor_id else None
        audit_details: dict[str, JSONValue] = {}
        if details:
            audit_details.update(details)

        resolved_context: AuditContext = context if context is not None else {}
        request_metadata: dict[str, JSONValue] = {}
        if "method" in resolved_context:
            request_metadata["method"] = resolved_context["method"]
        if "path" in resolved_context:
            request_metadata["path"] = resolved_context["path"]
        if "request_id" in resolved_context:
            request_metadata["request_id"] = resolved_context["request_id"]
        if request_metadata:
            audit_details["request"] = request_metadata

        serialized_details = (
            json.dumps(audit_details, separators=(",", ":"), sort_keys=True)
            if audit_details
            else None
        )
        log = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user=normalized_actor,
            request_id=resolved_context.get("request_id"),
            ip_address=resolved_context.get("ip_address"),
            user_agent=resolved_context.get("user_agent"),
            success=success,
            details=serialized_details,
        )
        return self._repository.record(db, log)


__all__ = ["AuditTrailService"]
