"""
Domain repository interfaces - abstract contracts for data access.

These interfaces define the contracts that domain services depend on,
enabling dependency inversion and testability.
"""

from .base import Repository, QuerySpecification
from .gene_repository import GeneRepository
from .variant_repository import VariantRepository
from .phenotype_repository import PhenotypeRepository
from .evidence_repository import EvidenceRepository
from .publication_repository import PublicationRepository

# Data Sources module repositories
from .user_data_source_repository import UserDataSourceRepository
from .source_template_repository import SourceTemplateRepository
from .ingestion_job_repository import IngestionJobRepository

__all__ = [
    # Base infrastructure
    "Repository",
    "QuerySpecification",
    # Core domain repositories
    "GeneRepository",
    "VariantRepository",
    "PhenotypeRepository",
    "EvidenceRepository",
    "PublicationRepository",
    # Data Sources repositories
    "UserDataSourceRepository",
    "SourceTemplateRepository",
    "IngestionJobRepository",
]
