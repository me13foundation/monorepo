"""
API-specific type definitions for MED13 Resource Library.

Contains types for API endpoints, request/response schemas,
and external API integrations.
"""

from typing import Dict, List, Optional, Any, TypedDict
from .common import PaginatedResponse


# Request types
class GeneCreateRequest(TypedDict, total=False):
    """Gene creation request."""

    symbol: str
    name: Optional[str]
    description: Optional[str]
    gene_type: str
    chromosome: Optional[str]
    start_position: Optional[int]
    end_position: Optional[int]
    ensembl_id: Optional[str]
    ncbi_gene_id: Optional[int]
    uniprot_id: Optional[str]


class GeneUpdateRequest(GeneCreateRequest):
    """Gene update request (same fields as create)."""

    pass


class VariantCreateRequest(TypedDict, total=False):
    """Variant creation request."""

    gene_id: str
    hgvs_notation: str
    variant_type: str
    clinical_significance: str
    population_frequency: Dict[str, float]
    chromosome: Optional[str]
    position: Optional[int]
    reference_allele: Optional[str]
    alternate_allele: Optional[str]


class VariantUpdateRequest(VariantCreateRequest):
    """Variant update request."""

    pass


class PhenotypeCreateRequest(TypedDict, total=False):
    """Phenotype creation request."""

    hpo_id: str
    name: str
    definition: Optional[str]
    synonyms: List[str]


class PhenotypeUpdateRequest(PhenotypeCreateRequest):
    """Phenotype update request."""

    pass


class EvidenceCreateRequest(TypedDict, total=False):
    """Evidence creation request."""

    variant_id: str
    phenotype_id: Optional[str]
    publication_id: Optional[str]
    evidence_level: str
    confidence_score: float
    source: str
    evidence_type: str
    description: Optional[str]


class EvidenceUpdateRequest(EvidenceCreateRequest):
    """Evidence update request."""

    pass


class PublicationCreateRequest(TypedDict, total=False):
    """Publication creation request."""

    title: str
    authors: List[str]
    journal: Optional[str]
    publication_year: int
    doi: Optional[str]
    pmid: Optional[str]
    abstract: Optional[str]


class PublicationUpdateRequest(PublicationCreateRequest):
    """Publication update request."""

    pass


# Query parameter types
class GeneQueryParams(TypedDict, total=False):
    """Gene query parameters."""

    page: int
    per_page: int
    search: str
    sort_by: str
    sort_order: str
    symbol: str
    chromosome: str
    gene_type: str


class VariantQueryParams(TypedDict, total=False):
    """Variant query parameters."""

    page: int
    per_page: int
    search: str
    sort_by: str
    sort_order: str
    gene_id: str
    clinical_significance: str
    variant_type: str


class PhenotypeQueryParams(TypedDict, total=False):
    """Phenotype query parameters."""

    page: int
    per_page: int
    search: str
    sort_by: str
    sort_order: str
    hpo_id: str


class EvidenceQueryParams(TypedDict, total=False):
    """Evidence query parameters."""

    page: int
    per_page: int
    search: str
    sort_by: str
    sort_order: str
    variant_id: str
    phenotype_id: str
    evidence_level: str
    confidence_min: float
    confidence_max: float


class PublicationQueryParams(TypedDict, total=False):
    """Publication query parameters."""

    page: int
    per_page: int
    search: str
    sort_by: str
    sort_order: str
    author: str
    year_min: int
    year_max: int
    journal: str
    doi: str
    pmid: str


# Response types - using type aliases to avoid TypedDict field overwriting
GeneListResponse = PaginatedResponse
VariantListResponse = PaginatedResponse
PhenotypeListResponse = PaginatedResponse
EvidenceListResponse = PaginatedResponse
PublicationListResponse = PaginatedResponse


# Error response types
class APIError(TypedDict):
    """API error response."""

    error: str
    message: str
    details: Optional[Dict[str, Any]]
    code: str


class ValidationErrorResponse(TypedDict):
    """Validation error response."""

    errors: List[Dict[str, str]]
    message: str


# Bulk operation types
class BulkUpdateRequest(TypedDict):
    """Bulk update request."""

    ids: List[str]
    updates: Dict[str, Any]  # Will be replaced with specific types per entity


class BulkOperationResponse(TypedDict):
    """Bulk operation response."""

    successful: List[str]
    failed: List[Dict[str, str]]
    total_processed: int
    errors: List[str]


# Search types
class SearchRequest(TypedDict, total=False):
    """Search request."""

    q: str
    entity_type: str
    filters: Dict[str, Any]
    sort_by: str
    sort_order: str
    page: int
    per_page: int


class SearchResult(TypedDict):
    """Individual search result."""

    id: str
    entity_type: str
    title: str
    description: Optional[str]
    score: float
    highlights: List[str]


# Search types
class SearchResponseExtra(TypedDict):
    """Additional fields for search response."""

    query: str
    search_time_ms: int


# Combine with base response (avoiding field redefinition)
SearchResponse = PaginatedResponse  # Base pagination
# Note: In actual usage, combine with SearchResponseExtra fields


# Export all types for easy importing
