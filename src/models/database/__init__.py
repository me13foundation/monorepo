# MED13 Resource Library - SQLAlchemy Database Models
# Strongly typed database entities with relationships and constraints

from .audit import AuditLog
from .base import Base
from .evidence import EvidenceLevel, EvidenceModel, EvidenceType
from .gene import GeneModel, GeneType
from .ingestion_job import (
    IngestionJobModel,
)
from .ingestion_job import (
    IngestionStatusEnum as IngestionStatus,
)
from .ingestion_job import (
    IngestionTriggerEnum as IngestionTrigger,
)
from .phenotype import PhenotypeCategory, PhenotypeModel
from .publication import PublicationModel, PublicationType
from .review import ReviewRecord
from .source_template import (
    SourceTemplateModel,
    SourceTypeEnum,
)
from .source_template import (
    TemplateCategoryEnum as TemplateCategory,
)
from .user import UserModel
from .user_data_source import (
    SourceStatusEnum as SourceStatus,
)
from .user_data_source import (
    SourceTypeEnum as SourceType,
)

# Data Sources module models
from .user_data_source import (
    UserDataSourceModel,
)
from .variant import ClinicalSignificance, VariantModel, VariantType

__all__ = [
    "AuditLog",
    "Base",
    "ClinicalSignificance",
    "EvidenceLevel",
    "EvidenceModel",
    "EvidenceType",
    "GeneModel",
    "GeneType",
    "IngestionJobModel",
    "IngestionStatus",
    "IngestionTrigger",
    "PhenotypeCategory",
    "PhenotypeModel",
    "PublicationModel",
    "PublicationType",
    "ReviewRecord",
    "SourceStatus",
    "SourceTemplateModel",
    "SourceType",
    "SourceTypeEnum",
    "TemplateCategory",
    "UserDataSourceModel",
    "UserModel",
    "VariantModel",
    "VariantType",
]
