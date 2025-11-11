"""
API request/response schemas for the MED13 Resource Library.

These Pydantic models define the structure of data exchanged
through the REST API endpoints.
"""

from .common import (
    ActivityFeedItem,
    DashboardSummary,
    ErrorDetail,
    ErrorResponse,
    GeneSummary,
    HealthComponent,
    HealthResponse,
    PaginatedResponse,
    PaginationParams,
    PhenotypeSummary,
    PublicationSummary,
    VariantLinkSummary,
)
from .evidence import (
    EvidenceCreate,
    EvidenceLevel,
    EvidenceList,
    EvidenceResponse,
    EvidenceSummaryResponse,
    EvidenceType,
    EvidenceUpdate,
)
from .gene import (
    GeneCreate,
    GeneList,
    GenePhenotypeSummary,
    GeneResponse,
    GeneUpdate,
)
from .phenotype import (
    PhenotypeCategory,
    PhenotypeCategoryResult,
    PhenotypeCreate,
    PhenotypeEvidenceResponse,
    PhenotypeList,
    PhenotypeResponse,
    PhenotypeSearchResult,
    PhenotypeStatisticsResponse,
    PhenotypeUpdate,
)
from .publication import (
    AuthorInfo,
    PublicationCreate,
    PublicationList,
    PublicationResponse,
    PublicationType,
    PublicationUpdate,
)
from .variant import (
    ClinicalSignificance,
    VariantCreate,
    VariantList,
    VariantResponse,
    VariantSummaryResponse,
    VariantType,
    VariantUpdate,
)

__all__ = [
    "ActivityFeedItem",
    "AuthorInfo",
    "ClinicalSignificance",
    "DashboardSummary",
    "ErrorDetail",
    "ErrorResponse",
    "EvidenceCreate",
    "EvidenceLevel",
    "EvidenceList",
    "EvidenceResponse",
    "EvidenceSummaryResponse",
    "EvidenceType",
    "EvidenceUpdate",
    "GeneCreate",
    "GeneList",
    "GenePhenotypeSummary",
    "GeneResponse",
    "GeneSummary",
    "GeneUpdate",
    "HealthComponent",
    "HealthResponse",
    "PaginatedResponse",
    "PaginationParams",
    "PhenotypeCategory",
    "PhenotypeCategoryResult",
    "PhenotypeCreate",
    "PhenotypeEvidenceResponse",
    "PhenotypeList",
    "PhenotypeResponse",
    "PhenotypeSummary",
    "PhenotypeSearchResult",
    "PhenotypeStatisticsResponse",
    "PhenotypeUpdate",
    "PublicationCreate",
    "PublicationList",
    "PublicationResponse",
    "PublicationType",
    "PublicationUpdate",
    "PublicationSummary",
    "VariantCreate",
    "VariantList",
    "VariantResponse",
    "VariantLinkSummary",
    "VariantSummaryResponse",
    "VariantType",
    "VariantUpdate",
]
