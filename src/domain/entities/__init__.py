"""
Domain entities for MED13 Resource Library.

These entities represent the core business objects and their relationships.
"""

from .evidence import Evidence
from .gene import Gene
from .phenotype import Phenotype
from .publication import Publication
from .variant import Variant

# Data Sources module entities
from .ingestion_job import (
    IngestionJob,
    IngestionStatus,
    IngestionTrigger,
    JobMetrics,
    IngestionError,
)
from .source_template import (
    SourceTemplate,
    TemplateCategory,
    ValidationRule,
    TemplateUIConfig,
)
from .user_data_source import (
    UserDataSource,
    SourceType,
    SourceStatus,
    SourceConfiguration,
    IngestionSchedule,
    QualityMetrics,
)

__all__ = [
    # Core entities
    "Evidence",
    "Gene",
    "Phenotype",
    "Publication",
    "Variant",
    # Data Sources entities
    "UserDataSource",
    "SourceTemplate",
    "IngestionJob",
    # Enums and value objects
    "SourceType",
    "SourceStatus",
    "IngestionStatus",
    "IngestionTrigger",
    "TemplateCategory",
    # Supporting models
    "SourceConfiguration",
    "IngestionSchedule",
    "QualityMetrics",
    "JobMetrics",
    "IngestionError",
    "ValidationRule",
    "TemplateUIConfig",
]
