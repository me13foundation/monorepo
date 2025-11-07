"""
Admin API routes for MED13 Resource Library.

These endpoints provide administrative functionality for managing users,
data sources, system monitoring, and audit logging.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.application.services.data_source_authorization_service import (
    DataSourceAuthorizationService,
)
from src.application.services.source_management_service import (
    CreateSourceRequest,
    SourceManagementService,
    UpdateSourceRequest,
)
from src.application.services.template_management_service import (
    TemplateManagementService,
)
from src.database.session import get_session
from src.domain.entities.user_data_source import (
    IngestionSchedule,
    SourceConfiguration,
    SourceStatus,
)
from src.domain.entities.user_data_source import (
    SourceType as DomainSourceType,
)
from src.infrastructure.repositories.user_data_source_repository import (
    SqlAlchemyUserDataSourceRepository,
)

# Create router
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        500: {"description": "Internal Server Error"},
    },
)

# Database session setup (simplified for now)
# TODO: Use proper dependency injection from container
engine = create_engine("sqlite:///med13.db")  # TODO: Get from config
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Session:
    """Get database session."""
    return SessionLocal()


# Dependency injection functions
def get_source_service() -> SourceManagementService:
    """Get source management service instance."""
    session = get_db_session()
    user_repo = SqlAlchemyUserDataSourceRepository(session)
    # TODO: Create template repository when needed
    # For now, pass None - this will need to be fixed when template functionality is implemented
    return SourceManagementService(user_repo, None)  # type: ignore[arg-type]


def get_template_service() -> TemplateManagementService:
    """Get template management service instance."""
    # TODO: Implement proper template service
    message = "Template service not yet implemented"
    raise NotImplementedError(message)


async def get_auth_service() -> DataSourceAuthorizationService:
    """Get authorization service instance."""
    return DataSourceAuthorizationService()


# Request/Response Models
class CreateDataSourceRequest(BaseModel):
    """Request model for creating a data source."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    source_type: str = Field(..., pattern="^(api|file|database)$")
    template_id: UUID | None = None
    config: dict[str, Any] = Field(..., description="Data source configuration")
    ingestion_schedule: dict[str, Any] | None = Field(
        None,
        description="Ingestion schedule configuration",
    )


class UpdateDataSourceRequest(BaseModel):
    """Request model for updating a data source."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    status: SourceStatus | None = None
    config: dict[str, Any] | None = Field(
        None,
        description="Updated data source configuration",
    )
    ingestion_schedule: dict[str, Any] | None = Field(
        None,
        description="Updated ingestion schedule",
    )


class DataSourceResponse(BaseModel):
    """Response model for data source information."""

    id: UUID
    owner_id: UUID
    name: str
    description: str | None
    source_type: str
    status: SourceStatus
    config: dict[str, Any]
    template_id: UUID | None
    ingestion_schedule: dict[str, Any] | None
    quality_metrics: dict[str, Any] | None
    last_ingested_at: str | None
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class DataSourceListResponse(BaseModel):
    """Response model for data source listing."""

    data_sources: list[DataSourceResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class SystemStatsResponse(BaseModel):
    """Response model for system statistics."""

    total_data_sources: int
    active_data_sources: int
    total_records: int
    system_health: str
    last_updated: str


class DataSourceStats(BaseModel):
    """Statistics for data sources."""

    total_sources: int
    active_sources: int
    error_sources: int
    sources_by_type: dict[str, int]


# Routes


@router.get(
    "/data-sources",
    response_model=DataSourceListResponse,
    summary="List data sources",
    description="Retrieve a paginated list of all data sources with optional filtering.",
)
async def list_data_sources(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: SourceStatus | None = Query(None, description="Filter by status"),
    source_type: str | None = Query(None, description="Filter by source type"),
    research_space_id: UUID
    | None = Query(
        None,
        description="Filter by research space ID",
    ),
    service: SourceManagementService = Depends(get_source_service),
    session: Session = Depends(get_session),
) -> DataSourceListResponse:
    """List data sources with pagination and filtering."""
    try:
        source_repo = SqlAlchemyUserDataSourceRepository(session)

        # If research_space_id is provided, filter by space
        if research_space_id:
            skip = (page - 1) * limit
            data_sources = source_repo.find_by_research_space(
                research_space_id,
                skip=skip,
                limit=limit,
            )
            # TODO: Add count method to repository for accurate total
            total = len(data_sources)
        else:
            # Get all data sources (simplified for now - in real implementation would include filtering)
            all_sources = service.get_active_sources(0, 1000)  # Get a large batch

            # Apply filters (placeholder)
            data_sources = all_sources
            if status:
                data_sources = [ds for ds in data_sources if ds.status == status]
            if source_type:
                type_enum = DomainSourceType(source_type)
                data_sources = [
                    ds for ds in data_sources if ds.source_type == type_enum
                ]

            # Pagination
            total = len(data_sources)
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            data_sources = data_sources[start_idx:end_idx]

        return DataSourceListResponse(
            data_sources=[DataSourceResponse.model_validate(ds) for ds in data_sources],
            total=total,
            page=page,
            limit=limit,
            has_next=(page * limit) < total,
            has_prev=page > 1,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list data sources: {e!s}",
        )


@router.post(
    "/data-sources",
    response_model=DataSourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create data source",
    description="Create a new data source configuration.",
)
async def create_data_source(
    request: CreateDataSourceRequest,
    service: SourceManagementService = Depends(get_source_service),
    auth_service: DataSourceAuthorizationService = Depends(get_auth_service),
) -> DataSourceResponse:
    """Create a new data source."""
    try:
        # TODO: Get current user from authentication context
        owner_id = UUID("00000000-0000-0000-0000-000000000001")  # Placeholder

        # Create the data source request
        source_type_enum = DomainSourceType(request.source_type)

        config_obj = SourceConfiguration(**request.config)

        create_request = CreateSourceRequest(
            owner_id=owner_id,
            name=request.name,
            source_type=source_type_enum,
            description=request.description or "",
            configuration=config_obj,
            template_id=request.template_id,
        )

        # Create the data source
        data_source = service.create_source(create_request)

        return DataSourceResponse.model_validate(data_source)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create data source: {e!s}",
        )


@router.get(
    "/data-sources/{source_id}",
    response_model=DataSourceResponse,
    summary="Get data source",
    description="Retrieve detailed information about a specific data source.",
)
async def get_data_source(
    source_id: UUID,
    service: SourceManagementService = Depends(get_source_service),
) -> DataSourceResponse:
    """Get a specific data source by ID."""
    try:
        data_source = service.get_source(source_id)
        if not data_source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data source not found",
            )
        return DataSourceResponse.model_validate(data_source)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data source: {e!s}",
        )


@router.put(
    "/data-sources/{source_id}",
    response_model=DataSourceResponse,
    summary="Update data source",
    description="Update an existing data source configuration.",
)
async def update_data_source(
    source_id: UUID,
    request: UpdateDataSourceRequest,
    service: SourceManagementService = Depends(get_source_service),
    auth_service: DataSourceAuthorizationService = Depends(get_auth_service),
) -> DataSourceResponse:
    """Update an existing data source."""
    try:
        # TODO: Get current user from authentication context
        user_id = UUID("00000000-0000-0000-0000-000000000001")  # Placeholder

        # Create update request
        update_request = UpdateSourceRequest(
            name=request.name,
            description=request.description,
            configuration=(
                SourceConfiguration(**request.config) if request.config else None
            ),
            ingestion_schedule=(
                IngestionSchedule(**request.ingestion_schedule)
                if request.ingestion_schedule
                else None
            ),
        )

        # Update the data source
        data_source = service.update_source(source_id, update_request, user_id)

        if not data_source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data source not found",
            )

        return DataSourceResponse.model_validate(data_source)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update data source: {e!s}",
        )


@router.delete(
    "/data-sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete data source",
    description="Delete an existing data source.",
)
async def delete_data_source(
    source_id: UUID,
    service: SourceManagementService = Depends(get_source_service),
    auth_service: DataSourceAuthorizationService = Depends(get_auth_service),
) -> None:
    """Delete a data source."""
    try:
        # TODO: Get current user from authentication context
        user_id = UUID("00000000-0000-0000-0000-000000000001")  # Placeholder

        success = service.delete_source(source_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data source not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete data source: {e!s}",
        )


@router.get(
    "/stats",
    response_model=SystemStatsResponse,
    summary="Get system statistics",
    description="Retrieve overall system statistics for the admin dashboard.",
)
async def get_system_stats(
    service: SourceManagementService = Depends(get_source_service),
) -> SystemStatsResponse:
    """Get system-wide statistics."""
    try:
        # Get data source statistics
        stats = service.get_statistics()
        data_sources = service.get_active_sources(0, 1000)
        active_sources = len(
            [ds for ds in data_sources if ds.status == SourceStatus.ACTIVE],
        )

        return SystemStatsResponse(
            total_data_sources=stats.get("total_sources", 0),
            active_data_sources=active_sources,
            total_records=0,  # TODO: Implement record counting
            system_health="healthy",
            last_updated="2024-01-01T00:00:00Z",  # TODO: Implement real timestamp
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system stats: {e!s}",
        )


@router.get(
    "/data-sources/stats",
    response_model=DataSourceStats,
    summary="Get data source statistics",
    description="Retrieve statistics about data sources grouped by type and status.",
)
async def get_data_source_stats(
    service: SourceManagementService = Depends(get_source_service),
) -> DataSourceStats:
    """Get data source statistics."""
    try:
        # Get statistics from service
        stats = service.get_statistics()

        # Get all sources to calculate additional stats
        all_sources = service.get_active_sources(0, 1000)
        # TODO: Get sources by status when service supports it
        active_sources = len(
            [ds for ds in all_sources if ds.status == SourceStatus.ACTIVE],
        )
        # For now, assume no error sources (TODO: add error status filtering)
        error_sources = 0

        # Count by type from all sources
        sources_by_type: dict[str, int] = {}
        for ds in all_sources:
            source_type = ds.source_type.value
            sources_by_type[source_type] = sources_by_type.get(source_type, 0) + 1

        total_sources = stats.get("total_sources", len(all_sources))

        return DataSourceStats(
            total_sources=total_sources,
            active_sources=active_sources,
            error_sources=error_sources,
            sources_by_type=sources_by_type,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data source stats: {e!s}",
        )
