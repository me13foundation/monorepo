"""
Common type definitions for MED13 Resource Library.

Contains TypedDict classes for update operations, API responses,
and other common patterns throughout the application.
"""

from __future__ import annotations

from typing import Literal, TypedDict

JSONPrimitive = str | int | float | bool | None
type JSONValue = JSONPrimitive | dict[str, "JSONValue"] | list["JSONValue"]
JSONObject = dict[str, JSONValue]
RawRecord = dict[str, JSONValue]
"""Raw data record from external sources (typed JSON)."""


# Update operation types (replace Dict[str, Any])
class GeneUpdate(TypedDict, total=False):
    """Type-safe gene update parameters."""

    symbol: str
    name: str | None
    description: str | None
    gene_type: str
    chromosome: str | None
    start_position: int | None
    end_position: int | None
    ensembl_id: str | None
    ncbi_gene_id: int | None
    uniprot_id: str | None


class VariantUpdate(TypedDict, total=False):
    """Type-safe variant update parameters."""

    gene_id: str
    hgvs_notation: str
    variant_type: str
    clinical_significance: str
    population_frequency: dict[str, float]
    chromosome: str | None
    position: int | None
    reference_allele: str | None
    alternate_allele: str | None


class PhenotypeUpdate(TypedDict, total=False):
    """Type-safe phenotype update parameters."""

    hpo_id: str
    name: str
    definition: str | None
    synonyms: list[str]
    parents: list[str]
    children: list[str]


class EvidenceUpdate(TypedDict, total=False):
    """Type-safe evidence update parameters."""

    variant_id: str
    phenotype_id: str | None
    publication_id: str | None
    evidence_level: str
    confidence_score: float
    source: str
    evidence_type: str
    description: str | None


class PublicationUpdate(TypedDict, total=False):
    """Type-safe publication update parameters."""

    title: str
    authors: list[str]
    journal: str | None
    publication_year: int
    doi: str | None
    pmid: str | None
    abstract: str | None


# API response types
class APIResponse(TypedDict, total=False):
    """Standard API response structure."""

    data: list[JSONObject]
    total: int
    page: int
    per_page: int
    errors: list[str]
    message: str


class PaginatedResponse(TypedDict, total=False):
    """Paginated API response structure."""

    items: list[JSONObject]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


# Validation types
class ValidationError(TypedDict):
    """Validation error structure."""

    field: str
    message: str
    code: str


class ValidationResult(TypedDict):
    """Validation result structure."""

    is_valid: bool
    errors: list[ValidationError]
    warnings: list[ValidationError]


# Status and filter types
EntityStatus = Literal["pending", "approved", "rejected", "quarantined"]
PriorityLevel = Literal["high", "medium", "low"]
ClinicalSignificance = Literal[
    "pathogenic",
    "likely_pathogenic",
    "uncertain_significance",
    "likely_benign",
    "benign",
    "conflicting",
    "not_provided",
]


class EntityFilter(TypedDict, total=False):
    """Common entity filtering parameters."""

    status: EntityStatus
    priority: PriorityLevel
    search: str
    sort_by: str
    sort_order: Literal["asc", "desc"]
    page: int
    per_page: int


# Authentication credential types
class ApiKeyCredentials(TypedDict):
    """API key authentication credentials."""

    api_key: str
    header_name: str  # e.g., "X-API-Key", "Authorization"


class BasicAuthCredentials(TypedDict):
    """Basic authentication credentials."""

    username: str
    password: str


class OAuthCredentials(TypedDict):
    """OAuth authentication credentials."""

    client_id: str
    client_secret: str
    token_url: str
    scope: str | None


class BearerTokenCredentials(TypedDict):
    """Bearer token authentication credentials."""

    token: str


# Union type for all auth credential types
AuthCredentials = (
    ApiKeyCredentials
    | BasicAuthCredentials
    | OAuthCredentials
    | BearerTokenCredentials
    | dict[str, str | int | float | bool | None]
)
"""Type-safe authentication credentials. Falls back to dict for custom auth types."""


# Source-specific metadata types
class SourceMetadata(TypedDict, total=False):
    """Type-safe source-specific metadata."""

    version: str
    last_updated: str
    record_count: int
    data_format: str
    encoding: str
    compression: str
    schema_version: str
    custom_fields: dict[str, str | int | float | bool | None]
    limit: int | None
    method: str
    query_params: dict[str, JSONValue]
    headers: dict[str, str]
    required_fields: list[str]
    expected_types: dict[str, str]
    ingest_mode: str
    auth_type: str
    connection_string: str
    driver: str


# Research space settings types
class ResearchSpaceSettings(TypedDict, total=False):
    """Type-safe research space settings."""

    # Curation settings
    auto_approve: bool
    require_review: bool
    review_threshold: float

    # Data source settings
    max_data_sources: int
    allowed_source_types: list[str]

    # Access control
    public_read: bool
    allow_invites: bool

    # Notification settings
    email_notifications: bool
    notification_frequency: str

    # Custom settings
    custom: dict[str, str | int | float | bool | None]


# Query specification types
FilterValue = str | int | float | bool | None
QueryFilters = dict[str, FilterValue]


# Statistics and health check types
class StatisticsResponse(TypedDict, total=False):
    """Type-safe statistics response."""

    total_sources: int
    status_counts: dict[str, int]
    type_counts: dict[str, int]
    average_quality_score: float | None
    sources_with_quality_metrics: int


class HealthCheckResponse(TypedDict, total=False):
    """Type-safe health check response."""

    database: bool
    jwt_provider: bool
    password_hasher: bool
    services: bool
