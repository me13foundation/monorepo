"""Pydantic request and response schemas for data discovery routes."""

from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.entities.data_discovery_session import (
    QueryParameterType,
    TestResultStatus,
)
from src.domain.entities.user_data_source import SourceType
from src.type_definitions.common import JSONObject


class QueryParametersModel(BaseModel):
    """API model for query parameters."""

    gene_symbol: str | None = Field(None, description="Gene symbol to query")
    search_term: str | None = Field(None, description="Phenotype or search term")


class CreateSessionRequest(BaseModel):
    """Request payload for creating a workbench session."""

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
    """Request payload for updating session parameters."""

    parameters: QueryParametersModel = Field(..., description="New query parameters")


class ExecuteTestRequest(BaseModel):
    """Request payload for executing a query test."""

    catalog_entry_id: str = Field(..., description="Catalog entry ID to test")
    timeout_seconds: int = Field(30, ge=5, le=120, description="Timeout in seconds")


class AddToSpaceRequest(BaseModel):
    """Request payload for adding a source to a research space."""

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
    source_type: SourceType
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
    """Request payload for bulk selection updates."""

    source_ids: list[str] = Field(
        default_factory=list,
        description="Catalog entry IDs that should remain selected",
    )


__all__ = [
    "AddToSpaceRequest",
    "CreateSessionRequest",
    "DataDiscoverySessionResponse",
    "ExecuteTestRequest",
    "QueryParametersModel",
    "QueryTestResultResponse",
    "SourceCatalogResponse",
    "UpdateParametersRequest",
    "UpdateSelectionRequest",
]
