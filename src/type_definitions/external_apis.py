"""
External API response type definitions for MED13 Resource Library.

Contains TypedDict classes for responses from external biomedical APIs:
ClinVar, PubMed, HPO, UniProt, etc. These provide type safety when
processing external data and help prevent runtime errors.
"""

from typing import Dict, List, Optional, Any, TypedDict


# ClinVar API Types
class ClinVarSearchResult(TypedDict):
    """Individual ClinVar search result."""

    uid: str
    term: str
    count: Optional[int]


class ClinVarSearchResponse(TypedDict):
    """ClinVar ESearch API response structure."""

    header: Dict[str, Any]
    esearchresult: Dict[str, Any]
    count: str
    retmax: str
    retstart: str
    idlist: List[str]
    translationset: List[ClinVarSearchResult]
    translationstack: Dict[str, Any]
    querytranslation: str


class ClinVarVariantRecord(TypedDict, total=False):
    """Individual ClinVar variant record."""

    variation_id: str
    variation_name: str
    gene: Optional[Dict[str, Any]]
    condition: Optional[Dict[str, Any]]
    clinical_significance: Optional[Dict[str, Any]]
    review_status: Optional[str]
    interpretation: Optional[Dict[str, Any]]
    submissions: List[Dict[str, Any]]
    last_updated: Optional[str]


class ClinVarVariantResponse(TypedDict):
    """ClinVar ESummary API response for variant details."""

    header: Dict[str, Any]
    result: Dict[str, ClinVarVariantRecord]


# PubMed API Types
class PubMedSearchResponse(TypedDict):
    """PubMed ESearch API response structure."""

    header: Dict[str, Any]
    esearchresult: Dict[str, Any]
    count: str
    retmax: str
    retstart: str
    idlist: List[str]
    translationset: List[Dict[str, Any]]
    translationstack: Dict[str, Any]
    querytranslation: str


class PubMedArticleAuthor(TypedDict, total=False):
    """PubMed article author information."""

    lastname: str
    firstname: str
    initials: str
    affiliation: Optional[str]


class PubMedArticleJournal(TypedDict, total=False):
    """PubMed article journal information."""

    title: str
    volume: Optional[str]
    issue: Optional[str]
    pages: Optional[str]


class PubMedArticleResponse(TypedDict, total=False):
    """PubMed ESummary API response for article details."""

    uid: str
    pubmed_id: str
    doi: Optional[str]
    title: str
    authors: List[PubMedArticleAuthor]
    journal: PubMedArticleJournal
    pubdate: str
    abstract: Optional[str]
    keywords: List[str]
    pmc_id: Optional[str]


# HPO Ontology Types
class HPOTerm(TypedDict, total=False):
    """HPO ontology term structure."""

    id: str
    name: str
    definition: Optional[str]
    synonyms: List[str]
    parents: List[str]
    children: List[str]
    ancestors: List[str]
    descendants: List[str]
    comment: Optional[str]


class HPOOntologyResponse(TypedDict):
    """HPO ontology API response structure."""

    version: str
    date: str
    terms: Dict[str, HPOTerm]
    metadata: Dict[str, Any]


# UniProt API Types
class UniProtReference(TypedDict, total=False):
    """UniProt reference structure."""

    citation: str
    authors: List[str]
    title: str
    journal: str
    volume: Optional[str]
    pages: Optional[str]
    year: int
    doi: Optional[str]
    pubmed_id: Optional[str]


class UniProtFeature(TypedDict, total=False):
    """UniProt protein feature structure."""

    type: str
    description: str
    begin: int
    end: int
    evidence: List[str]


class UniProtEntryResponse(TypedDict, total=False):
    """UniProt entry API response structure."""

    accession: str
    name: str
    protein_names: List[str]
    gene_name: Optional[str]
    organism: str
    sequence: str
    length: int
    molecular_weight: Optional[int]
    features: List[UniProtFeature]
    references: List[UniProtReference]
    function: Optional[str]
    subcellular_location: Optional[List[str]]
    tissue_specificity: Optional[str]
    disease_association: Optional[List[str]]
    last_modified: str


# Generic External API Response Types
class ExternalAPIError(TypedDict):
    """Generic external API error response."""

    error: str
    message: str
    code: Optional[str]
    details: Optional[Dict[str, Any]]


class ExternalAPIRateLimit(TypedDict):
    """External API rate limit information."""

    limit: int
    remaining: int
    reset_time: int
    retry_after: Optional[int]


class ExternalAPIResponse(TypedDict, total=False):
    """Generic external API response wrapper."""

    success: bool
    data: Any
    error: Optional[ExternalAPIError]
    rate_limit: Optional[ExternalAPIRateLimit]
    request_id: Optional[str]
    timestamp: str


# Validation Types for External Data
class ExternalDataValidationResult(TypedDict):
    """Result of validating external API data."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    data_quality_score: float
    transformation_needed: bool
    sanitized_data: Optional[Any]


class APIEndpointConfig(TypedDict):
    """Configuration for external API endpoints."""

    base_url: str
    timeout: int
    retries: int
    rate_limit: int
    headers: Dict[str, str]
    auth_required: bool
    cache_enabled: bool


# Runtime Validation Types
class ValidationIssue(TypedDict):
    """Individual validation issue."""

    field: str
    issue_type: str  # "missing", "invalid", "unexpected"
    message: str
    severity: str  # "error", "warning", "info"


class APIResponseValidationResult(TypedDict):
    """Result of validating an external API response."""

    is_valid: bool
    issues: List[ValidationIssue]
    data_quality_score: float
    sanitized_data: Optional[Any]
    validation_time_ms: float


# Zenodo API Types
class ZenodoMetadata(TypedDict, total=False):
    """Zenodo deposit metadata structure."""

    title: str
    description: str
    creators: List[Dict[str, str]]
    keywords: List[str]
    license: str
    publication_date: str
    access_right: str
    communities: List[Dict[str, str]]
    subjects: List[Dict[str, str]]
    version: str
    language: str
    notes: str


class ZenodoFileInfo(TypedDict):
    """Zenodo file information."""

    id: str
    filename: str
    filesize: int
    checksum: str
    download: str


class ZenodoDepositResponse(TypedDict, total=False):
    """Zenodo deposit creation/response structure."""

    id: int
    conceptrecid: str
    doi: str
    doi_url: str
    metadata: ZenodoMetadata
    created: str
    modified: str
    owner: int
    record_id: int
    record_url: str
    state: str
    submitted: bool
    files: List[ZenodoFileInfo]
    links: Dict[str, str]


class ZenodoPublishResponse(TypedDict):
    """Zenodo publication response structure."""

    id: int
    doi: str
    doi_url: str
    record_url: str
    conceptdoi: str
    conceptrecid: str
