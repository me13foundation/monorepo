"""
Common type definitions for MED13 Resource Library.

Contains TypedDict classes for update operations, API responses,
and other common patterns throughout the application.
"""

from typing import Dict, List, Optional, Any, TypedDict, Literal


# Update operation types (replace Dict[str, Any])
class GeneUpdate(TypedDict, total=False):
    """Type-safe gene update parameters."""

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


class VariantUpdate(TypedDict, total=False):
    """Type-safe variant update parameters."""

    gene_id: str
    hgvs_notation: str
    variant_type: str
    clinical_significance: str
    population_frequency: Dict[str, float]
    chromosome: Optional[str]
    position: Optional[int]
    reference_allele: Optional[str]
    alternate_allele: Optional[str]


class PhenotypeUpdate(TypedDict, total=False):
    """Type-safe phenotype update parameters."""

    hpo_id: str
    name: str
    definition: Optional[str]
    synonyms: List[str]
    parents: List[str]
    children: List[str]


class EvidenceUpdate(TypedDict, total=False):
    """Type-safe evidence update parameters."""

    variant_id: str
    phenotype_id: Optional[str]
    publication_id: Optional[str]
    evidence_level: str
    confidence_score: float
    source: str
    evidence_type: str
    description: Optional[str]


class PublicationUpdate(TypedDict, total=False):
    """Type-safe publication update parameters."""

    title: str
    authors: List[str]
    journal: Optional[str]
    publication_year: int
    doi: Optional[str]
    pmid: Optional[str]
    abstract: Optional[str]


# API response types
class APIResponse(TypedDict, total=False):
    """Standard API response structure."""

    data: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int
    errors: List[str]
    message: str


class PaginatedResponse(TypedDict, total=False):
    """Paginated API response structure."""

    items: List[Dict[str, Any]]
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
    errors: List[ValidationError]
    warnings: List[ValidationError]


# Data processing types
RawRecord = Dict[str, Any]
"""Raw data record from external sources (justified for flexibility with external APIs)."""


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
