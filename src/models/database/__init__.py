# MED13 Resource Library - SQLAlchemy Database Models
# Strongly typed database entities with relationships and constraints

from . import (
    audit,
    base,
    data_discovery,
    data_source_activation,
    evidence,
    gene,
    ingestion_job,
    phenotype,
    publication,
    research_space,
    review,
    source_template,
    storage,
    system_status,
    user,
    user_data_source,
    variant,
)

AuditLog = audit.AuditLog
Base = base.Base

DataDiscoverySessionModel = data_discovery.DataDiscoverySessionModel
QueryTestResultModel = data_discovery.QueryTestResultModel
SourceCatalogEntryModel = data_discovery.SourceCatalogEntryModel

ActivationScopeEnum = data_source_activation.ActivationScopeEnum
DataSourceActivationModel = data_source_activation.DataSourceActivationModel

EvidenceLevel = evidence.EvidenceLevel
EvidenceModel = evidence.EvidenceModel
EvidenceType = evidence.EvidenceType

GeneModel = gene.GeneModel
GeneType = gene.GeneType

IngestionJobModel = ingestion_job.IngestionJobModel
IngestionStatus = ingestion_job.IngestionStatusEnum
IngestionTrigger = ingestion_job.IngestionTriggerEnum

PhenotypeCategory = phenotype.PhenotypeCategory
PhenotypeModel = phenotype.PhenotypeModel

PublicationModel = publication.PublicationModel
PublicationType = publication.PublicationType

MembershipRoleEnum = research_space.MembershipRoleEnum
ResearchSpaceMembershipModel = research_space.ResearchSpaceMembershipModel
ResearchSpaceModel = research_space.ResearchSpaceModel
SpaceStatusEnum = research_space.SpaceStatusEnum

ReviewRecord = review.ReviewRecord

SourceTemplateModel = source_template.SourceTemplateModel
SourceTypeEnum = source_template.SourceTypeEnum
TemplateCategory = source_template.TemplateCategoryEnum

StorageConfigurationModel = storage.StorageConfigurationModel
StorageHealthSnapshotModel = storage.StorageHealthSnapshotModel
StorageHealthStatusEnum = storage.StorageHealthStatusEnum
StorageOperationModel = storage.StorageOperationModel
StorageOperationStatusEnum = storage.StorageOperationStatusEnum
StorageOperationTypeEnum = storage.StorageOperationTypeEnum
StorageProviderEnum = storage.StorageProviderEnum

SystemStatusModel = system_status.SystemStatusModel

UserModel = user.UserModel

SourceStatus = user_data_source.SourceStatusEnum
SourceType = user_data_source.SourceTypeEnum
UserDataSourceModel = user_data_source.UserDataSourceModel

ClinicalSignificance = variant.ClinicalSignificance
VariantModel = variant.VariantModel
VariantType = variant.VariantType

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
