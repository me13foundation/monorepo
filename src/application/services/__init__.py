"""
Application services - orchestration layer for use cases.

These services coordinate domain services and repositories to implement
application use cases while maintaining proper separation of concerns.
"""

from .gene_service import GeneApplicationService
from .variant_service import VariantApplicationService
from .evidence_service import EvidenceApplicationService
from .phenotype_service import PhenotypeApplicationService
from .publication_service import PublicationApplicationService

# Data Sources module services
from .source_management_service import (
    SourceManagementService,
    CreateSourceRequest,
    UpdateSourceRequest,
)
from .template_management_service import (
    TemplateManagementService,
    CreateTemplateRequest,
    UpdateTemplateRequest,
)
from .data_source_authorization_service import (
    DataSourceAuthorizationService,
    DataSourcePermission,
    UserRole,
)

__all__ = [
    # Core application services
    "GeneApplicationService",
    "VariantApplicationService",
    "EvidenceApplicationService",
    "PhenotypeApplicationService",
    "PublicationApplicationService",
    # Data Sources services
    "SourceManagementService",
    "TemplateManagementService",
    "DataSourceAuthorizationService",
    # Request models
    "CreateSourceRequest",
    "UpdateSourceRequest",
    "CreateTemplateRequest",
    "UpdateTemplateRequest",
    # Authorization
    "DataSourcePermission",
    "UserRole",
]
