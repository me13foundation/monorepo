"""
FastAPI routes for Data Discovery operations.

Provides REST endpoints for data discovery session management, source catalog access,
query testing, and integration with data sources.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.application.curation.repositories.audit_repository import (
    SqlAlchemyAuditRepository,
)
from src.application.services.audit_service import AuditTrailService
from src.application.services.data_discovery_service import (
    AddSourceToSpaceRequest,
    CreateDataDiscoverySessionRequest,
    DataDiscoveryService,
    ExecuteQueryTestRequest,
    UpdateSessionParametersRequest,
)
from src.database.session import get_session
from src.domain.entities.data_discovery_session import (
    DataDiscoverySession,
    QueryParameters,
    QueryParameterType,
    QueryTestResult,
    SourceCatalogEntry,
    TestResultStatus,
)
from src.domain.entities.user import User, UserRole
from src.infrastructure.dependency_injection.container import (
    get_data_discovery_service_dependency,
)
from src.infrastructure.repositories.research_space_repository import (
    SqlAlchemyResearchSpaceRepository,
)
from src.routes.auth import get_current_active_user
from src.type_definitions.common import JSONObject

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-discovery", tags=["data-discovery"])

_audit_trail_service = AuditTrailService(SqlAlchemyAuditRepository())


def _audit_service() -> AuditTrailService:
    return _audit_trail_service


# Pydantic models for API requests/responses


class QueryParametersModel(BaseModel):
    """API model for query parameters."""

    gene_symbol: str | None = Field(None, description="Gene symbol to query")
    search_term: str | None = Field(None, description="Phenotype or search term")


class CreateSessionRequest(BaseModel):
    """Request model for creating a workbench session."""

    name: str = Field("Untitled Session", description="Session name")
    research_space_id: UUID | None = Field(None, description="Research space ID")
    initial_parameters: QueryParametersModel = Field(
        default_factory=lambda: QueryParametersModel(
            gene_symbol=None,
            search_term=None,
        ),
        description="Initial query parameters",
    )


class UpdateParametersRequest(BaseModel):
    """Request model for updating session parameters."""

    parameters: QueryParametersModel = Field(..., description="New query parameters")


class ExecuteTestRequest(BaseModel):
    """Request model for executing a query test."""

    catalog_entry_id: str = Field(..., description="Catalog entry ID to test")
    timeout_seconds: int = Field(30, ge=5, le=120, description="Timeout in seconds")


class AddToSpaceRequest(BaseModel):
    """Request model for adding a source to a research space."""

    catalog_entry_id: str = Field(..., description="Catalog entry ID")
    research_space_id: UUID = Field(..., description="Target research space ID")
    source_config: JSONObject = Field(
        default_factory=dict,
        description="Source configuration",
    )


class SourceCatalogResponse(BaseModel):
    """Response model for source catalog entries."""

    id: str
    name: str
    category: str
    subcategory: str | None
    description: str
    param_type: QueryParameterType
    is_active: bool
    requires_auth: bool
    usage_count: int
    success_rate: float
    tags: list[str]


class DataDiscoverySessionResponse(BaseModel):
    """Response model for data discovery sessions."""

    id: UUID
    owner_id: UUID
    research_space_id: UUID | None
    name: str
    current_parameters: QueryParametersModel
    selected_sources: list[str]
    tested_sources: list[str]
    total_tests_run: int
    successful_tests: int
    is_active: bool
    created_at: str
    updated_at: str
    last_activity_at: str


class QueryTestResultResponse(BaseModel):
    """Response model for query test results."""

    id: UUID
    catalog_entry_id: str
    session_id: UUID
    parameters: QueryParametersModel
    status: TestResultStatus
    response_data: JSONObject | None
    response_url: str | None
    error_message: str | None
    execution_time_ms: int | None
    data_quality_score: float | None
    started_at: str
    completed_at: str | None


class UpdateSelectionRequest(BaseModel):
    """Request model for bulk selection updates."""

    source_ids: list[str] = Field(
        default_factory=list,
        description="List of catalog entry IDs that should remain selected",
    )


def _owner_filter_for_user(current_user: User) -> UUID | None:
    """Return the owner filter to apply based on the current user's role."""
    return None if current_user.role == UserRole.ADMIN else current_user.id


def _require_session_for_user(
    session_id: UUID,
    service: DataDiscoveryService,
    current_user: User,
) -> DataDiscoverySession:
    """Load a session while enforcing ownership constraints."""
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

    # Determine whether the session exists but belongs to someone else
    if service.get_session(session_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this data discovery session",
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Data discovery session not found",
    )


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
    audit_service: AuditTrailService = Depends(_audit_service),
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

        create_request = CreateDataDiscoverySessionRequest(
            owner_id=current_user.id,
            name=request.name,
            research_space_id=validated_space_id,
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
                "research_space_id": (
                    str(validated_space_id) if validated_space_id else None
                ),
                "name": request.name,
            },
        )
        return _session_to_response(session)

    except Exception as e:
        logger.exception("Failed to create workbench session")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create workbench session",
        ) from e


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
        return [_session_to_response(session) for session in sessions]

    except Exception as e:
        logger.exception("Failed to list workbench sessions")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workbench sessions",
        ) from e


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
        session = _require_session_for_user(session_id, service, current_user)
        return _session_to_response(session)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get workbench session %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workbench session",
        ) from e


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
    audit_service: AuditTrailService = Depends(_audit_service),
) -> DataDiscoverySessionResponse:
    """Update parameters for a workbench session."""
    try:
        _require_session_for_user(session_id, service, current_user)
        owner_filter = _owner_filter_for_user(current_user)

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
        return _session_to_response(updated_session)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to update session parameters for %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session parameters",
        ) from e


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
    audit_service: AuditTrailService = Depends(_audit_service),
) -> DataDiscoverySessionResponse:
    """Toggle source selection in a workbench session."""
    try:
        _require_session_for_user(session_id, service, current_user)
        owner_filter = _owner_filter_for_user(current_user)

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
        audit_service.record_action(
            db,
            action="data_discovery.session.toggle_source",
            target=("data_discovery_session", str(session.id)),
            actor_id=current_user.id,
            details={
                "catalog_entry_id": catalog_entry_id,
                "selected_sources": session.selected_sources,
            },
        )
        return _session_to_response(session)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to toggle source selection for %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update source selection",
        ) from e


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
    audit_service: AuditTrailService = Depends(_audit_service),
) -> DataDiscoverySessionResponse:
    """Set the selected sources for a workbench session."""
    try:
        _require_session_for_user(session_id, service, current_user)
        owner_filter = _owner_filter_for_user(current_user)

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
        audit_service.record_action(
            db,
            action="data_discovery.session.set_sources",
            target=("data_discovery_session", str(session.id)),
            actor_id=current_user.id,
            details={"selected_sources": session.selected_sources},
        )
        return _session_to_response(session)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to update source selections for %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update source selections",
        ) from e


@router.post(
    "/sessions/{session_id}/tests",
    response_model=QueryTestResultResponse,
    summary="Execute query test",
    description="Execute a query test against a data source in the workbench session.",
)
async def execute_query_test(
    session_id: UUID,
    request: ExecuteTestRequest,
    service: DataDiscoveryService = Depends(get_data_discovery_service_dependency),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_session),
    audit_service: AuditTrailService = Depends(_audit_service),
) -> QueryTestResultResponse:
    """Execute a query test."""
    try:
        _require_session_for_user(session_id, service, current_user)
        owner_filter = _owner_filter_for_user(current_user)

        test_request = ExecuteQueryTestRequest(
            session_id=session_id,
            catalog_entry_id=request.catalog_entry_id,
            timeout_seconds=request.timeout_seconds,
        )

        result = await service.execute_query_test(
            test_request,
            owner_id=owner_filter,
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session or catalog entry not found",
            )
        audit_service.record_action(
            db,
            action="data_discovery.session.execute_test",
            target=("data_discovery_session", str(session_id)),
            actor_id=current_user.id,
            details={
                "catalog_entry_id": request.catalog_entry_id,
                "status": result.status.value,
            },
        )
        return _test_result_to_response(result)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to execute query test for session %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute query test",
        ) from e


@router.get(
    "/sessions/{session_id}/tests",
    response_model=list[QueryTestResultResponse],
    summary="Get session test results",
    description="Retrieve all query test results for a workbench session.",
)
async def get_session_test_results(
    session_id: UUID,
    service: DataDiscoveryService = Depends(get_data_discovery_service_dependency),
    current_user: User = Depends(get_current_active_user),
) -> list[QueryTestResultResponse]:
    """Get all test results for a session."""
    try:
        _require_session_for_user(session_id, service, current_user)

        results = service.get_session_test_results(session_id)
        return [_test_result_to_response(result) for result in results]

    except Exception as e:
        logger.exception("Failed to get test results for session %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve test results",
        ) from e


@router.post(
    "/sessions/{session_id}/add-to-space",
    status_code=status.HTTP_201_CREATED,
    summary="Add source to research space",
    description="Add a tested source from the workbench to a research space as a UserDataSource.",
)
async def add_source_to_space(
    session_id: UUID,
    request: AddToSpaceRequest,
    service: DataDiscoveryService = Depends(get_data_discovery_service_dependency),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_session),
    audit_service: AuditTrailService = Depends(_audit_service),
) -> dict[str, str]:
    """Add a tested source to a research space."""
    try:
        _require_session_for_user(session_id, service, current_user)
        owner_filter = _owner_filter_for_user(current_user)

        add_request = AddSourceToSpaceRequest(
            session_id=session_id,
            catalog_entry_id=request.catalog_entry_id,
            research_space_id=request.research_space_id,
            source_config=request.source_config,
        )

        data_source_id = await service.add_source_to_space(
            add_request,
            owner_id=owner_filter,
        )
        if not data_source_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add source to research space",
            )

        audit_service.record_action(
            db,
            action="data_discovery.session.add_to_space",
            target=("data_discovery_session", str(session_id)),
            actor_id=current_user.id,
            details={
                "catalog_entry_id": request.catalog_entry_id,
                "research_space_id": str(request.research_space_id),
                "data_source_id": str(data_source_id),
            },
        )
        return {
            "data_source_id": str(data_source_id),
            "message": "Source added to space successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to add source to space from session %s",
            session_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add source to research space",
        ) from e


@router.get(
    "/catalog",
    response_model=list[SourceCatalogResponse],
    summary="Get source catalog",
    description="Retrieve the source catalog, optionally filtered by category or search query.",
)
async def get_source_catalog(
    category: str | None = Query(None, description="Filter by category"),
    search: str | None = Query(None, description="Search query"),
    research_space_id: UUID
    | None = Query(
        None,
        description="Optional research space context for availability filtering",
    ),
    service: DataDiscoveryService = Depends(get_data_discovery_service_dependency),
) -> list[SourceCatalogResponse]:
    """Get the source catalog with optional filtering."""
    try:
        entries = service.get_source_catalog(
            category,
            search,
            research_space_id=research_space_id,
        )
        return [_catalog_entry_to_response(entry) for entry in entries]

    except Exception as e:
        logger.exception("Failed to retrieve source catalog")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve source catalog",
        ) from e


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
    audit_service: AuditTrailService = Depends(_audit_service),
) -> None:
    """Delete a workbench session."""
    try:
        _require_session_for_user(session_id, service, current_user)
        owner_filter = _owner_filter_for_user(current_user)

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
    except Exception as e:
        logger.exception("Failed to delete workbench session %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete workbench session",
        ) from e


# Helper functions for converting entities to API responses


def _session_to_response(session: DataDiscoverySession) -> DataDiscoverySessionResponse:
    """Convert a DataDiscoverySession entity to API response."""
    return DataDiscoverySessionResponse(
        id=session.id,
        owner_id=session.owner_id,
        research_space_id=session.research_space_id,
        name=session.name,
        current_parameters=QueryParametersModel(
            gene_symbol=session.current_parameters.gene_symbol,
            search_term=session.current_parameters.search_term,
        ),
        selected_sources=session.selected_sources,
        tested_sources=session.tested_sources,
        total_tests_run=session.total_tests_run,
        successful_tests=session.successful_tests,
        is_active=session.is_active,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        last_activity_at=session.last_activity_at.isoformat(),
    )


def _test_result_to_response(result: QueryTestResult) -> QueryTestResultResponse:
    """Convert a QueryTestResult entity to API response."""
    return QueryTestResultResponse(
        id=result.id,
        catalog_entry_id=result.catalog_entry_id,
        session_id=result.session_id,
        parameters=QueryParametersModel(
            gene_symbol=result.parameters.gene_symbol,
            search_term=result.parameters.search_term,
        ),
        status=result.status,
        response_data=result.response_data,
        response_url=result.response_url,
        error_message=result.error_message,
        execution_time_ms=result.execution_time_ms,
        data_quality_score=result.data_quality_score,
        started_at=result.started_at.isoformat(),
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
    )


def _catalog_entry_to_response(entry: SourceCatalogEntry) -> SourceCatalogResponse:
    """Convert a SourceCatalogEntry entity to API response."""
    return SourceCatalogResponse(
        id=entry.id,
        name=entry.name,
        category=entry.category,
        subcategory=entry.subcategory,
        description=entry.description,
        param_type=entry.param_type,
        is_active=entry.is_active,
        requires_auth=entry.requires_auth,
        usage_count=entry.usage_count,
        success_rate=entry.success_rate,
        tags=entry.tags,
    )
