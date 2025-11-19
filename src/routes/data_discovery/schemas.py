"""Pydantic request and response schemas for data discovery routes."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.entities.data_discovery_parameters import (
    AdvancedQueryParameters,
    PubMedSortOption,
    QueryParameterType,
    TestResultStatus,
)
from src.domain.entities.discovery_preset import DiscoveryProvider, PresetScope
from src.domain.entities.discovery_search_job import DiscoverySearchStatus
from src.domain.entities.user_data_source import SourceType
from src.type_definitions.common import JSONObject
from src.type_definitions.storage import StorageOperationStatus


class QueryParametersModel(BaseModel):
    """API model for query parameters."""

    gene_symbol: str | None = Field(None, description="Gene symbol to query")
    search_term: str | None = Field(None, description="Phenotype or search term")


class AdvancedQueryParametersModel(QueryParametersModel):
    """API model for advanced PubMed parameters."""

    date_from: str | None = Field(None, description="Earliest publication date (ISO)")
    date_to: str | None = Field(None, description="Latest publication date (ISO)")
    publication_types: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    sort_by: str | None = Field(
        default=PubMedSortOption.RELEVANCE.value,
        description="Sort option",
    )
    max_results: int = Field(default=100, ge=1, le=1000)
    additional_terms: str | None = Field(default=None)

    # ClinVar
    variation_types: list[str] = Field(default_factory=list)
    clinical_significance: list[str] = Field(default_factory=list)

    # UniProt
    is_reviewed: bool | None = Field(default=None)
    organism: str | None = Field(default=None)

    def to_domain_model(self) -> AdvancedQueryParameters:
        """Convert serialized parameters into domain AdvancedQueryParameters."""
        return AdvancedQueryParameters(
            gene_symbol=self.gene_symbol,
            search_term=self.search_term,
            date_from=self._parse_date(self.date_from),
            date_to=self._parse_date(self.date_to),
            publication_types=self.publication_types,
            languages=self.languages,
            sort_by=(
                PubMedSortOption(self.sort_by)
                if self.sort_by
                else PubMedSortOption.RELEVANCE
            ),
            max_results=self.max_results,
            additional_terms=self.additional_terms,
            variation_types=self.variation_types,
            clinical_significance=self.clinical_significance,
            is_reviewed=self.is_reviewed,
            organism=self.organism,
        )

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if value is None:
            return None
        return date.fromisoformat(value)

    @classmethod
    def from_domain(
        cls,
        parameters: AdvancedQueryParameters,
    ) -> "AdvancedQueryParametersModel":
        return cls(
            gene_symbol=parameters.gene_symbol,
            search_term=parameters.search_term,
            date_from=(
                parameters.date_from.isoformat() if parameters.date_from else None
            ),
            date_to=parameters.date_to.isoformat() if parameters.date_to else None,
            publication_types=parameters.publication_types,
            languages=parameters.languages,
            sort_by=parameters.sort_by.value if parameters.sort_by else None,
            max_results=parameters.max_results,
            additional_terms=parameters.additional_terms,
            variation_types=parameters.variation_types,
            clinical_significance=parameters.clinical_significance,
            is_reviewed=parameters.is_reviewed,
            organism=parameters.organism,
        )


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
    capabilities: JSONObject


class DataDiscoverySessionResponse(BaseModel):
    """Response model for data discovery sessions."""

    id: UUID
    owner_id: UUID
    research_space_id: UUID | None
    name: str
    current_parameters: AdvancedQueryParametersModel
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
    "StorageOperationResponse",
    "UpdateParametersRequest",
    "UpdateSelectionRequest",
]
