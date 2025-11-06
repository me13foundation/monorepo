"""
Common type definitions for MED13 Resource Library.

Contains TypedDict classes for update operations, API responses,
and other common patterns throughout the application.
"""

from typing import Any, Literal, TypedDict


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

    data: list[dict[str, Any]]
    total: int
    page: int
    per_page: int
    errors: list[str]
    message: str


class PaginatedResponse(TypedDict, total=False):
    """Paginated API response structure."""

    items: list[dict[str, Any]]
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


# Data processing types
RawRecord = dict[str, Any]
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
