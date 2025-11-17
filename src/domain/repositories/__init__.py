"""
Domain repository interfaces - abstract contracts for data access.

These interfaces define the contracts that domain services depend on,
enabling dependency inversion and testability.
"""

from .base import QuerySpecification, Repository
from .data_source_activation_repository import DataSourceActivationRepository
from .evidence_repository import EvidenceRepository
from .gene_repository import GeneRepository
from .ingestion_job_repository import IngestionJobRepository
from .phenotype_repository import PhenotypeRepository
from .publication_repository import PublicationRepository
from .source_template_repository import SourceTemplateRepository
from .storage_repository import (
    StorageConfigurationRepository,
    StorageOperationRepository,
)

# Data Sources module repositories
from .user_data_source_repository import UserDataSourceRepository
from .variant_repository import VariantRepository

__all__ = [
    "EvidenceRepository",
    "GeneRepository",
    "IngestionJobRepository",
    "PhenotypeRepository",
    "PublicationRepository",
    "QuerySpecification",
    "Repository",
    "SourceTemplateRepository",
    "StorageConfigurationRepository",
    "StorageOperationRepository",
    "UserDataSourceRepository",
    "VariantRepository",
    "DataSourceActivationRepository",
]
