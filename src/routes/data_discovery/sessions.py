"""Route handlers for data discovery session management."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.application.services.audit_service import AuditTrailService
from src.application.services.data_discovery_service import (
    CreateDataDiscoverySessionRequest,
    DataDiscoveryService,
    UpdateSessionParametersRequest,
)
from src.database.seed import DEFAULT_RESEARCH_SPACE_ID
from src.database.session import get_session
from src.domain.entities.data_discovery_session import QueryParameters
from src.domain.entities.user import User, UserRole
from src.infrastructure.dependency_injection.container import (
    get_data_discovery_service_dependency,
)
from src.infrastructure.repositories.research_space_repository import (
    SqlAlchemyResearchSpaceRepository,
)
from src.routes.auth import get_current_active_user
from src.type_definitions.common import JSONValue

from .dependencies import (
    get_audit_trail_service,
    owner_filter_for_user,
    require_session_for_user,
)
from .mappers import session_to_response
from .schemas import (
    CreateSessionRequest,
    DataDiscoverySessionResponse,
    UpdateParametersRequest,
    UpdateSelectionRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/sessions",
    response_model=DataDiscoverySessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create workbench session",
    description="Create a new workbench session for source discovery and testing.",
)
async def create_session(
    request: CreateSessionRequest,
    service: DataDiscoveryService = Depends(get_data_discovery_service_dependency),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    audit_service: AuditTrailService = Depends(get_audit_trail_service),
) -> DataDiscoverySessionResponse:
    """Create a new workbench session."""
    try:
        validated_space_id = request.research_space_id
        if validated_space_id:
            space_repo = SqlAlchemyResearchSpaceRepository(session=db)
            if not space_repo.exists(validated_space_id):
                logger.warning(
                    "Research space %s not found while creating discovery session; defaulting to None",
                    validated_space_id,
                )
                validated_space_id = None

        enforced_space_id = validated_space_id or DEFAULT_RESEARCH_SPACE_ID
        create_request = CreateDataDiscoverySessionRequest(
            owner_id=current_user.id,
            name=request.name,
            research_space_id=enforced_space_id,
            initial_parameters=QueryParameters(
                gene_symbol=request.initial_parameters.gene_symbol,
                search_term=request.initial_parameters.search_term,
            ),
        )

        try:
            session = service.create_session(create_request)
        except IntegrityError as exc:
            logger.exception(
                "Failed to create workbench session due to integrity error (space_id=%s)",
                validated_space_id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid research space reference",
            ) from exc

        audit_service.record_action(
            db,
            action="data_discovery.session.create",
            target=("data_discovery_session", str(session.id)),
            actor_id=current_user.id,
            details={
                "research_space_id": str(enforced_space_id),
                "name": request.name,
            },
        )
        return session_to_response(session)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to create workbench session")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create workbench session",
        ) from exc


@router.get(
    "/sessions",
    response_model=list[DataDiscoverySessionResponse],
    summary="List user sessions",
    description="Retrieve all workbench sessions for the current user.",
)
async def list_sessions(
    include_inactive: bool = Query(False, description="Include inactive sessions"),
    service: DataDiscoveryService = Depends(get_data_discovery_service_dependency),
    current_user: User = Depends(get_current_active_user),
    owner_id: UUID
    | None = Query(
        None,
        description="Filter sessions by owner (admin only)",
    ),
) -> list[DataDiscoverySessionResponse]:
    """List all workbench sessions for the current user."""
    try:
        effective_owner = owner_id if current_user.role == UserRole.ADMIN else None
        if effective_owner is None:
            effective_owner = current_user.id

        sessions = service.get_user_sessions(
            effective_owner,
            include_inactive=include_inactive,
        )
        return [session_to_response(session) for session in sessions]

    except Exception as exc:
        logger.exception("Failed to list workbench sessions")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workbench sessions",
        ) from exc


@router.get(
    "/sessions/{session_id}",
    response_model=DataDiscoverySessionResponse,
    summary="Get workbench session",
    description="Retrieve detailed information about a specific workbench session.",
)
async def get_session_detail(
    session_id: UUID,
    service: DataDiscoveryService = Depends(get_data_discovery_service_dependency),
    current_user: User = Depends(get_current_active_user),
) -> DataDiscoverySessionResponse:
    """Get a specific workbench session."""
    try:
        session = require_session_for_user(session_id, service, current_user)
        return session_to_response(session)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get workbench session %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workbench session",
        ) from exc


@router.put(
    "/sessions/{session_id}/parameters",
    response_model=DataDiscoverySessionResponse,
    summary="Update session parameters",
    description="Update the query parameters for a workbench session.",
)
async def update_session_parameters(
    session_id: UUID,
    request: UpdateParametersRequest,
    service: DataDiscoveryService = Depends(get_data_discovery_service_dependency),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_session),
    audit_service: AuditTrailService = Depends(get_audit_trail_service),
) -> DataDiscoverySessionResponse:
    """Update parameters for a workbench session."""
    try:
        require_session_for_user(session_id, service, current_user)
        owner_filter = owner_filter_for_user(current_user)

        update_request = UpdateSessionParametersRequest(
            session_id=session_id,
            parameters=QueryParameters(
                gene_symbol=request.parameters.gene_symbol,
                search_term=request.parameters.search_term,
            ),
        )

        updated_session = service.update_session_parameters(
            update_request,
            owner_id=owner_filter,
        )
        if not updated_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data discovery session not found",
            )
        audit_service.record_action(
            db,
            action="data_discovery.session.update_parameters",
            target=("data_discovery_session", str(updated_session.id)),
            actor_id=current_user.id,
            details=update_request.parameters.model_dump(),
        )
        return session_to_response(updated_session)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to update session parameters for %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session parameters",
        ) from exc


@router.put(
    "/sessions/{session_id}/sources/{catalog_entry_id}/toggle",
    response_model=DataDiscoverySessionResponse,
    summary="Toggle source selection",
    description="Toggle the selection state of a source in the workbench session.",
)
async def toggle_source_selection(
    session_id: UUID,
    catalog_entry_id: str,
    service: DataDiscoveryService = Depends(get_data_discovery_service_dependency),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_session),
    audit_service: AuditTrailService = Depends(get_audit_trail_service),
) -> DataDiscoverySessionResponse:
    """Toggle source selection in a workbench session."""
    try:
        require_session_for_user(session_id, service, current_user)
        owner_filter = owner_filter_for_user(current_user)

        session = service.toggle_source_selection(
            session_id,
            catalog_entry_id,
            owner_id=owner_filter,
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data discovery session not found",
            )
        selected_sources_payload: list[JSONValue] = list(session.selected_sources)
        audit_service.record_action(
            db,
            action="data_discovery.session.toggle_source",
            target=("data_discovery_session", str(session.id)),
            actor_id=current_user.id,
            details={
                "catalog_entry_id": catalog_entry_id,
                "selected_sources": selected_sources_payload,
            },
        )
        return session_to_response(session)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to toggle source selection for %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update source selection",
        ) from exc


@router.put(
    "/sessions/{session_id}/selections",
    response_model=DataDiscoverySessionResponse,
    summary="Set session source selections",
    description="Replace the selected sources for a data discovery session.",
)
async def update_source_selection(
    session_id: UUID,
    request: UpdateSelectionRequest,
    service: DataDiscoveryService = Depends(get_data_discovery_service_dependency),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_session),
    audit_service: AuditTrailService = Depends(get_audit_trail_service),
) -> DataDiscoverySessionResponse:
    """Set the selected sources for a workbench session."""
    try:
        require_session_for_user(session_id, service, current_user)
        owner_filter = owner_filter_for_user(current_user)

        session = service.set_source_selection(
            session_id,
            request.source_ids,
            owner_id=owner_filter,
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data discovery session not found",
            )
        selected_sources_payload: list[JSONValue] = list(session.selected_sources)
        audit_service.record_action(
            db,
            action="data_discovery.session.set_sources",
            target=("data_discovery_session", str(session.id)),
            actor_id=current_user.id,
            details={"selected_sources": selected_sources_payload},
        )
        return session_to_response(session)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to update source selections for %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update source selections",
        ) from exc


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete workbench session",
    description="Delete a workbench session and all its associated test results.",
)
async def delete_session(
    session_id: UUID,
    service: DataDiscoveryService = Depends(get_data_discovery_service_dependency),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_session),
    audit_service: AuditTrailService = Depends(get_audit_trail_service),
) -> None:
    """Delete a workbench session."""
    try:
        require_session_for_user(session_id, service, current_user)
        owner_filter = owner_filter_for_user(current_user)

        success = service.delete_session(session_id, owner_id=owner_filter)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data discovery session not found",
            )
        audit_service.record_action(
            db,
            action="data_discovery.session.delete",
            target=("data_discovery_session", str(session_id)),
            actor_id=current_user.id,
            details={},
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to delete workbench session %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete workbench session",
        ) from exc


__all__ = ["router"]
