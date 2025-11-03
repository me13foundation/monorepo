"""
Type definitions for MED13 Resource Library.

This module contains all type definitions used throughout the application,
organized by domain and usage pattern.
"""

from .common import (
    GeneUpdate,
    VariantUpdate,
    PhenotypeUpdate,
    EvidenceUpdate,
    PublicationUpdate,
    APIResponse,
    PaginatedResponse,
    ValidationResult,
    RawRecord,
)

from .external_apis import (
    ClinVarSearchResponse,
    ClinVarVariantResponse,
    PubMedSearchResponse,
    PubMedArticleResponse,
    HPOOntologyResponse,
    UniProtEntryResponse,
)

__all__ = [
    "GeneUpdate",
    "VariantUpdate",
    "PhenotypeUpdate",
    "EvidenceUpdate",
    "PublicationUpdate",
    "APIResponse",
    "PaginatedResponse",
    "ValidationResult",
    "RawRecord",
    "ClinVarSearchResponse",
    "ClinVarVariantResponse",
    "PubMedSearchResponse",
    "PubMedArticleResponse",
    "HPOOntologyResponse",
    "UniProtEntryResponse",
]
