"""Pydantic request and response schemas for admin data source routes."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.domain.entities.user_data_source import (
    IngestionSchedule,
    QualityMetrics,
    SourceConfiguration,
    SourceStatus,
    SourceType,
)


class CreateDataSourceRequest(BaseModel):
    """Request payload for creating a data source."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    source_type: SourceType
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
    """Request payload for updating a data source."""

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
    source_type: SourceType
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


__all__ = [
    "CreateDataSourceRequest",
    "DataSourceListResponse",
    "DataSourceResponse",
    "UpdateDataSourceRequest",
]
