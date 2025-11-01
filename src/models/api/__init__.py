"""
API request/response schemas for the MED13 Resource Library.

These Pydantic models define the structure of data exchanged
through the REST API endpoints.
"""

from .common import (
    PaginationParams,
    PaginatedResponse,
    ErrorResponse,
    HealthResponse,
    ErrorDetail,
    HealthComponent,
)
from .gene import (
    GeneResponse,
    GeneCreate,
    GeneUpdate,
    GeneList,
)
from .variant import (
    VariantResponse,
    VariantCreate,
    VariantUpdate,
    VariantList,
    VariantType,
    ClinicalSignificance,
)
from .phenotype import (
    PhenotypeResponse,
    PhenotypeCreate,
    PhenotypeUpdate,
    PhenotypeList,
    PhenotypeCategory,
)
from .evidence import (
    EvidenceResponse,
    EvidenceCreate,
    EvidenceUpdate,
    EvidenceList,
    EvidenceLevel,
    EvidenceType,
)
from .publication import (
    PublicationResponse,
    PublicationCreate,
    PublicationUpdate,
    PublicationList,
    PublicationType,
    AuthorInfo,
)

__all__ = [
    # Common schemas
    "PaginationParams",
    "PaginatedResponse",
    "ErrorResponse",
    "HealthResponse",
    "ErrorDetail",
    "HealthComponent",
    # Gene schemas
    "GeneResponse",
    "GeneCreate",
    "GeneUpdate",
    "GeneList",
    # Variant schemas
    "VariantResponse",
    "VariantCreate",
    "VariantUpdate",
    "VariantList",
    "VariantType",
    "ClinicalSignificance",
    # Phenotype schemas
    "PhenotypeResponse",
    "PhenotypeCreate",
    "PhenotypeUpdate",
    "PhenotypeList",
    "PhenotypeCategory",
    # Evidence schemas
    "EvidenceResponse",
    "EvidenceCreate",
    "EvidenceUpdate",
    "EvidenceList",
    "EvidenceLevel",
    "EvidenceType",
    # Publication schemas
    "PublicationResponse",
    "PublicationCreate",
    "PublicationUpdate",
    "PublicationList",
    "PublicationType",
    "AuthorInfo",
]
