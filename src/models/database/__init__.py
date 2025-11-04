# MED13 Resource Library - SQLAlchemy Database Models
# Strongly typed database entities with relationships and constraints

from .base import Base
from .gene import GeneModel, GeneType
from .variant import VariantModel, VariantType, ClinicalSignificance
from .phenotype import PhenotypeModel, PhenotypeCategory
from .evidence import EvidenceModel, EvidenceLevel, EvidenceType
from .publication import PublicationModel, PublicationType
from .audit import AuditLog
from .review import ReviewRecord

# Data Sources module models
from .user_data_source import (
    UserDataSourceModel,
    SourceTypeEnum as SourceType,
    SourceStatusEnum as SourceStatus,
)
from .source_template import (
    SourceTemplateModel,
    TemplateCategoryEnum as TemplateCategory,
    SourceTypeEnum,
)
from .ingestion_job import (
    IngestionJobModel,
    IngestionStatusEnum as IngestionStatus,
    IngestionTriggerEnum as IngestionTrigger,
)

__all__ = [
    # Base infrastructure
    "Base",
    "AuditLog",
    "ReviewRecord",
    # Core domain models
    "GeneModel",
    "GeneType",
    "VariantModel",
    "VariantType",
    "ClinicalSignificance",
    "PhenotypeModel",
    "PhenotypeCategory",
    "EvidenceModel",
    "EvidenceLevel",
    "EvidenceType",
    "PublicationModel",
    "PublicationType",
    # Data Sources models
    "UserDataSourceModel",
    "SourceTemplateModel",
    "IngestionJobModel",
    # Enums
    "SourceType",
    "SourceStatus",
    "TemplateCategory",
    "SourceTypeEnum",
    "IngestionStatus",
    "IngestionTrigger",
]
