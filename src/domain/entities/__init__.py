"""
Domain entities for MED13 Resource Library.

These entities represent the core business objects and their relationships.
"""

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
    "QualityMetrics",
    "SourceConfiguration",
    "SourceStatus",
    "SourceTemplate",
    "SourceType",
    "TemplateCategory",
    "TemplateUIConfig",
    "UserDataSource",
    "ValidationRule",
    "Variant",
]
