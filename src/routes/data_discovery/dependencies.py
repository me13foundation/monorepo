"""Shared dependencies and helper functions for data discovery routes."""

from uuid import UUID

from fastapi import HTTPException, status

from src.application.curation.repositories.audit_repository import (
    SqlAlchemyAuditRepository,
)
from src.application.services.audit_service import AuditTrailService
from src.application.services.data_discovery_service import DataDiscoveryService
from src.domain.entities.data_discovery_session import DataDiscoverySession
from src.domain.entities.user import User, UserRole
from src.infrastructure.observability.request_context import get_audit_context

_audit_trail_service = AuditTrailService(SqlAlchemyAuditRepository())


def get_audit_trail_service() -> AuditTrailService:
    """Provide a singleton audit service instance for route handlers."""
    return _audit_trail_service


get_audit_context_dependency = get_audit_context


def owner_filter_for_user(current_user: User) -> UUID | None:
    """Return the appropriate owner filter based on the current user's role."""
    return None if current_user.role == UserRole.ADMIN else current_user.id


def require_session_for_user(
    session_id: UUID,
    service: DataDiscoveryService,
    current_user: User,
) -> DataDiscoverySession:
    """Fetch a session while ensuring the requesting user has access."""
    if current_user.role == UserRole.ADMIN:
        session = service.get_session(session_id)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data discovery session not found",
            )
        return session

    session = service.get_session_for_owner(session_id, current_user.id)
    if session is not None:
        return session

    if service.get_session(session_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this data discovery session",
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Data discovery session not found",
    )


__all__ = [
    "get_audit_context_dependency",
    "get_audit_trail_service",
    "get_audit_context",
    "owner_filter_for_user",
    "require_session_for_user",
]
