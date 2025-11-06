"""
API request/response schemas for the MED13 Resource Library.

These Pydantic models define the structure of data exchanged
through the REST API endpoints.
"""

from .common import (
    ErrorDetail,
    ErrorResponse,
    HealthComponent,
    HealthResponse,
    PaginatedResponse,
    PaginationParams,
)
from .evidence import (
    EvidenceCreate,
    EvidenceLevel,
    EvidenceList,
    EvidenceResponse,
    EvidenceType,
    EvidenceUpdate,
)
from .gene import (
    GeneCreate,
    GeneList,
    GeneResponse,
    GeneUpdate,
)
from .phenotype import (
    PhenotypeCategory,
    PhenotypeCreate,
    PhenotypeList,
    PhenotypeResponse,
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
    VariantType,
    VariantUpdate,
)

__all__ = [
    "AuthorInfo",
    "ClinicalSignificance",
    "ErrorDetail",
    "ErrorResponse",
    "EvidenceCreate",
    "EvidenceLevel",
    "EvidenceList",
    "EvidenceResponse",
    "EvidenceType",
    "EvidenceUpdate",
    "GeneCreate",
    "GeneList",
    "GeneResponse",
    "GeneUpdate",
    "HealthComponent",
    "HealthResponse",
    "PaginatedResponse",
    "PaginationParams",
    "PhenotypeCategory",
    "PhenotypeCreate",
    "PhenotypeList",
    "PhenotypeResponse",
    "PhenotypeUpdate",
    "PublicationCreate",
    "PublicationList",
    "PublicationResponse",
    "PublicationType",
    "PublicationUpdate",
    "VariantCreate",
    "VariantList",
    "VariantResponse",
    "VariantType",
    "VariantUpdate",
]
