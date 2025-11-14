"""
Data source management endpoints for the admin API.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from src.application.services.data_source_authorization_service import (
    DataSourceAuthorizationService,
)
from src.application.services.source_management_service import (
    CreateSourceRequest,
    SourceManagementService,
    UpdateSourceRequest,
)
from src.database.session import get_session
from src.domain.entities.user_data_source import (
    IngestionSchedule,
    QualityMetrics,
    SourceConfiguration,
    SourceStatus,
)
from src.domain.entities.user_data_source import (
    SourceType as DomainSourceType,
)
from src.infrastructure.repositories.user_data_source_repository import (
    SqlAlchemyUserDataSourceRepository,
)

from .dependencies import DEFAULT_OWNER_ID, get_auth_service, get_source_service

data_sources_router = APIRouter(prefix="/data-sources")


class CreateDataSourceRequest(BaseModel):
    """Request model for creating a data source."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    source_type: DomainSourceType
    template_id: UUID | None = None
    config: SourceConfiguration = Field(
        ...,
        description="Data source configuration",
    )
    ingestion_schedule: IngestionSchedule | None = Field(
        None,
        description="Ingestion schedule configuration",
    )


class UpdateDataSourceRequest(BaseModel):
    """Request model for updating a data source."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    status: SourceStatus | None = None
    config: SourceConfiguration | None = Field(
        None,
        description="Updated data source configuration",
    )
    ingestion_schedule: IngestionSchedule | None = Field(
        None,
        description="Updated ingestion schedule",
    )


class DataSourceResponse(BaseModel):
    """Response model for data source information."""

    id: UUID
    owner_id: UUID
    name: str
    description: str | None
    source_type: DomainSourceType
    status: SourceStatus
    config: SourceConfiguration
    template_id: UUID | None
    ingestion_schedule: IngestionSchedule | None
    quality_metrics: QualityMetrics | None
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


@data_sources_router.get(
    "",
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

        if research_space_id:
            skip = (page - 1) * limit
            data_sources = source_repo.find_by_research_space(
                research_space_id,
                skip=skip,
                limit=limit,
            )
            total = len(data_sources)
        else:
            all_sources = service.get_active_sources(0, 1000)
            data_sources = all_sources
            if status:
                data_sources = [ds for ds in data_sources if ds.status == status]
            if source_type:
                type_enum = DomainSourceType(source_type)
                data_sources = [
                    ds for ds in data_sources if ds.source_type == type_enum
                ]

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
    except Exception as e:  # pragma: no cover - defensive guard
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list data sources: {e!s}",
        )


@data_sources_router.post(
    "",
    response_model=DataSourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create data source",
    description="Create a new data source configuration.",
)
async def create_data_source(
    request: CreateDataSourceRequest,
    service: SourceManagementService = Depends(get_source_service),
    auth_service: DataSourceAuthorizationService = Depends(
        get_auth_service,
    ),  # noqa: ARG001
) -> DataSourceResponse:
    """Create a new data source."""
    try:
        create_request = CreateSourceRequest(
            owner_id=DEFAULT_OWNER_ID,
            name=request.name,
            source_type=request.source_type,
            description=request.description or "",
            configuration=request.config.model_copy(),
            template_id=request.template_id,
        )
        data_source = service.create_source(create_request)
        return DataSourceResponse.model_validate(data_source)
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - defensive guard
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create data source: {e!s}",
        )


@data_sources_router.get(
    "/{source_id}",
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
    except Exception as e:  # pragma: no cover - defensive guard
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data source: {e!s}",
        )


@data_sources_router.put(
    "/{source_id}",
    response_model=DataSourceResponse,
    summary="Update data source",
    description="Update an existing data source configuration.",
)
async def update_data_source(
    source_id: UUID,
    request: UpdateDataSourceRequest,
    service: SourceManagementService = Depends(get_source_service),
    auth_service: DataSourceAuthorizationService = Depends(
        get_auth_service,
    ),  # noqa: ARG001
) -> DataSourceResponse:
    """Update an existing data source."""
    try:
        update_request = UpdateSourceRequest(
            name=request.name,
            description=request.description,
            configuration=(request.config.model_copy() if request.config else None),
            ingestion_schedule=(
                request.ingestion_schedule.model_copy()
                if request.ingestion_schedule
                else None
            ),
        )
        data_source = service.update_source(
            source_id,
            update_request,
            DEFAULT_OWNER_ID,
        )
        if not data_source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data source not found",
            )
        return DataSourceResponse.model_validate(data_source)
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - defensive guard
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update data source: {e!s}",
        )


@data_sources_router.delete(
    "/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete data source",
    description="Delete an existing data source.",
)
async def delete_data_source(
    source_id: UUID,
    service: SourceManagementService = Depends(get_source_service),
    auth_service: DataSourceAuthorizationService = Depends(
        get_auth_service,
    ),  # noqa: ARG001
) -> None:
    """Delete a data source."""
    try:
        success = service.delete_source(source_id, DEFAULT_OWNER_ID)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data source not found",
            )
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - defensive guard
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete data source: {e!s}",
        )


__all__ = [
    "CreateDataSourceRequest",
    "DataSourceListResponse",
    "DataSourceResponse",
    "data_sources_router",
]
