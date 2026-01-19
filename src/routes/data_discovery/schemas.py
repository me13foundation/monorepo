"""Pydantic request and response schemas for data discovery routes."""

from uuid import UUID

from pydantic import BaseModel, Field

# Import DTOs from application layer
from src.application.services.data_discovery_service.dtos import (
    AdvancedQueryParametersModel,
    DataDiscoverySessionResponse,
    OrchestratedSessionState,
    QueryParametersModel,
    SourceCapabilitiesDTO,
    SourceCatalogEntry,
    ValidationIssueDTO,
    ValidationResultDTO,
    ViewContextDTO,
)
from src.application.services.data_discovery_service.requests import (
    ExecuteQueryTestRequest,
)
from src.application.services.discovery_configuration_requests import (
    CreatePubmedPresetRequest,
)
from src.domain.entities.data_discovery_parameters import (
    AdvancedQueryParameters,
    PubMedSortOption,
    QueryParameterCapabilities,
    TestResultStatus,
)
from src.domain.entities.discovery_preset import DiscoveryProvider, PresetScope
from src.domain.entities.discovery_search_job import DiscoverySearchStatus
from src.type_definitions.common import JSONObject
from src.type_definitions.storage import StorageOperationStatus

# Re-export DTOs for API use
__all__ = [
    "AddToSpaceRequest",
    "AdvancedQueryParametersModel",
    "PubMedSortOption",
    "CreatePubmedPresetRequestModel",
    "CreateSessionRequest",
    "DataDiscoverySessionResponse",
    "DiscoveryPresetResponse",
    "DiscoverySearchJobResponse",
    "ExecuteTestRequest",
    "PubmedDownloadRequestModel",
    "QueryParametersModel",
    "QueryTestResultResponse",
    "RunPubmedSearchRequestModel",
    "SourceCatalogResponse",
    "QueryParameterCapabilities",
    "StorageOperationResponse",
    "UpdateParametersRequest",
    "UpdateSelectionRequest",
    "SourceCapabilitiesDTO",
    "ValidationIssueDTO",
    "ValidationResultDTO",
    "ViewContextDTO",
    "OrchestratedSessionState",
]

_QUERY_PARAMETER_CAPABILITIES = QueryParameterCapabilities


class CreateSessionRequest(BaseModel):
    """Request payload for creating a workbench session."""

    name: str = Field("Untitled Session", description="Session name")
    research_space_id: UUID | None = Field(None, description="Research space ID")
    initial_parameters: AdvancedQueryParametersModel = Field(
        default_factory=lambda: AdvancedQueryParametersModel(
            gene_symbol=None,
            search_term=None,
            date_from=None,
            date_to=None,
            publication_types=[],
            languages=[],
            sort_by=PubMedSortOption.RELEVANCE.value,
            max_results=100,
            additional_terms=None,
            variation_types=[],
            clinical_significance=[],
            is_reviewed=None,
            organism=None,
        ),
        description="Initial query parameters",
    )


class UpdateParametersRequest(BaseModel):
    """Request payload for updating session parameters."""

    parameters: AdvancedQueryParametersModel = Field(
        ...,
        description="New query parameters",
    )


class ExecuteTestRequest(BaseModel):
    """Request payload for executing a query test."""

    catalog_entry_id: str = Field(..., description="Catalog entry ID to test")
    timeout_seconds: int = Field(30, ge=5, le=120, description="Timeout in seconds")
    parameters: AdvancedQueryParametersModel | None = Field(
        None,
        description="Optional parameters to override session defaults",
    )

    def to_domain_request(self, session_id: UUID) -> ExecuteQueryTestRequest:
        """Convert request payload into a domain test request."""
        return ExecuteQueryTestRequest(
            session_id=session_id,
            catalog_entry_id=self.catalog_entry_id,
            timeout_seconds=self.timeout_seconds,
            parameters=self.parameters.to_domain_model() if self.parameters else None,
        )


class AddToSpaceRequest(BaseModel):
    """Request payload for adding a source to a research space."""

    catalog_entry_id: str = Field(..., description="Catalog entry ID")
    research_space_id: UUID = Field(..., description="Target research space ID")
    source_config: JSONObject = Field(
        default_factory=dict,
        description="Source configuration",
    )


class SourceCatalogResponse(SourceCatalogEntry):
    """
    Response model for source catalog entries.

    Inherits from SourceCatalogEntry DTO for backward compatibility and API documentation.
    """


class QueryTestResultResponse(BaseModel):
    """Response model for query test results."""

    id: UUID
    catalog_entry_id: str
    session_id: UUID
    parameters: AdvancedQueryParametersModel
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


class DiscoveryPresetResponse(BaseModel):
    """Response model for discovery presets."""

    id: UUID
    name: str
    description: str | None
    provider: DiscoveryProvider
    scope: PresetScope
    research_space_id: UUID | None
    parameters: AdvancedQueryParametersModel
    metadata: JSONObject
    created_at: str
    updated_at: str


class CreatePubmedPresetRequestModel(BaseModel):
    """Request payload for creating PubMed presets."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    scope: PresetScope = Field(default=PresetScope.USER)
    research_space_id: UUID | None = None
    parameters: AdvancedQueryParametersModel

    def to_advanced_parameters(self) -> AdvancedQueryParameters:
        """Convert request payload into domain advanced parameters."""
        return self.parameters.to_domain_model()

    def to_domain_request(self) -> CreatePubmedPresetRequest:
        """Build the domain preset request from the API payload."""
        return CreatePubmedPresetRequest(
            name=self.name,
            description=self.description,
            scope=self.scope,
            research_space_id=self.research_space_id,
            parameters=self.to_advanced_parameters(),
        )


class DiscoverySearchJobResponse(BaseModel):
    """Response model for asynchronous search jobs."""

    id: UUID
    owner_id: UUID
    session_id: UUID | None
    provider: DiscoveryProvider
    status: DiscoverySearchStatus
    query_preview: str
    parameters: AdvancedQueryParametersModel
    total_results: int
    result_metadata: JSONObject
    error_message: str | None
    storage_key: str | None
    created_at: str
    updated_at: str
    completed_at: str | None


class RunPubmedSearchRequestModel(BaseModel):
    """Request payload for starting PubMed searches."""

    session_id: UUID | None = None
    parameters: AdvancedQueryParametersModel


class PubmedDownloadRequestModel(BaseModel):
    """Request payload for downloading PubMed PDFs."""

    job_id: UUID
    article_id: str


class StorageOperationResponse(BaseModel):
    """Response payload for storage operations triggered by downloads."""

    id: UUID
    configuration_id: UUID
    key: str
    status: StorageOperationStatus
    created_at: str
    metadata: JSONObject
