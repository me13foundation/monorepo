"""
Domain entities for MED13 Resource Library.

These entities represent the core business objects and their relationships.
"""

# Data Discovery entities
from .data_discovery_parameters import (
    AdvancedQueryParameters,
    PubMedSortOption,
    QueryParameterCapabilities,
    QueryParameters,
    QueryParameterType,
    TestResultStatus,
)
from .data_discovery_session import (
    DataDiscoverySession,
    QueryTestResult,
    SourceCatalogEntry,
)
from .data_source_activation import (
    ActivationScope,
    DataSourceActivation,
)
from .discovery_search_job import (
    DiscoverySearchJob,
    DiscoverySearchStatus,
)
from .evidence import Evidence
from .gene import Gene

# Data Sources module entities
from .ingestion_job import (
    IngestionError,
    IngestionJob,
    IngestionStatus,
    IngestionTrigger,
    JobMetrics,
)
from .phenotype import Phenotype
from .publication import Publication
from .source_template import (
    SourceTemplate,
    TemplateCategory,
    TemplateUIConfig,
    ValidationRule,
)
from .storage_configuration import (
    StorageConfiguration,
    StorageHealthSnapshot,
    StorageOperation,
    StorageProviderMetadata,
    StorageProviderTestResult,
)
from .user_data_source import (
    IngestionSchedule,
    QualityMetrics,
    SourceConfiguration,
    SourceStatus,
    SourceType,
    UserDataSource,
)
from .variant import Variant

__all__ = [
    "AdvancedQueryParameters",
    "DataDiscoverySession",
    "Evidence",
    "Gene",
    "IngestionError",
    "IngestionJob",
    "IngestionSchedule",
    "IngestionStatus",
    "IngestionTrigger",
    "JobMetrics",
    "Phenotype",
    "Publication",
    "PubMedSortOption",
    "QualityMetrics",
    "QueryParameterCapabilities",
    "QueryParameterType",
    "QueryParameters",
    "QueryTestResult",
    "SourceCatalogEntry",
    "SourceConfiguration",
    "SourceStatus",
    "SourceTemplate",
    "SourceType",
    "TemplateCategory",
    "TemplateUIConfig",
    "TestResultStatus",
    "UserDataSource",
    "ValidationRule",
    "Variant",
    "ActivationScope",
    "DataSourceActivation",
    "StorageConfiguration",
    "StorageHealthSnapshot",
    "StorageOperation",
    "StorageProviderMetadata",
    "StorageProviderTestResult",
    "DiscoverySearchJob",
    "DiscoverySearchStatus",
]
