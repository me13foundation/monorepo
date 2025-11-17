# MED13 Resource Library - SQLAlchemy Database Models
# Strongly typed database entities with relationships and constraints

from .audit import AuditLog
from .base import Base

# Data Discovery models
from .data_discovery import (
    DataDiscoverySessionModel,
    QueryTestResultModel,
    SourceCatalogEntryModel,
)
from .data_source_activation import (
    ActivationScopeEnum,
    DataSourceActivationModel,
)
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
from .research_space import (
    MembershipRoleEnum,
    ResearchSpaceMembershipModel,
    ResearchSpaceModel,
    SpaceStatusEnum,
)
from .review import ReviewRecord
from .source_template import (
    SourceTemplateModel,
    SourceTypeEnum,
)
from .source_template import (
    TemplateCategoryEnum as TemplateCategory,
)
from .storage import (
    StorageConfigurationModel,
    StorageHealthSnapshotModel,
    StorageHealthStatusEnum,
    StorageOperationModel,
    StorageOperationStatusEnum,
    StorageOperationTypeEnum,
    StorageProviderEnum,
)
from .system_status import SystemStatusModel
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
    "DataDiscoverySessionModel",
    "EvidenceLevel",
    "EvidenceModel",
    "EvidenceType",
    "GeneModel",
    "GeneType",
    "IngestionJobModel",
    "IngestionStatus",
    "IngestionTrigger",
    "MembershipRoleEnum",
    "PhenotypeCategory",
    "PhenotypeModel",
    "PublicationModel",
    "PublicationType",
    "QueryTestResultModel",
    "ResearchSpaceMembershipModel",
    "ResearchSpaceModel",
    "ReviewRecord",
    "SourceCatalogEntryModel",
    "SourceStatus",
    "SourceTemplateModel",
    "SourceType",
    "SourceTypeEnum",
    "StorageConfigurationModel",
    "StorageHealthSnapshotModel",
    "StorageHealthStatusEnum",
    "StorageOperationModel",
    "StorageOperationStatusEnum",
    "StorageOperationTypeEnum",
    "StorageProviderEnum",
    "SystemStatusModel",
    "SpaceStatusEnum",
    "TemplateCategory",
    "UserDataSourceModel",
    "UserModel",
    "VariantModel",
    "VariantType",
    "DataSourceActivationModel",
    "ActivationScopeEnum",
]
