"""
Application services - orchestration layer for use cases.

These services coordinate domain services and repositories to implement
application use cases while maintaining proper separation of concerns.
"""

from src.application.search.search_service import UnifiedSearchService

from . import (
    audit_service,
    authentication_service,
    authorization_service,
    dashboard_service,
    data_discovery_service,
    data_source_activation_service,
    data_source_authorization_service,
    discovery_configuration_service,
    evidence_service,
    gene_service,
    ingestion_scheduling_service,
    phenotype_service,
    publication_service,
    pubmed_discovery_service,
    pubmed_ingestion_service,
    pubmed_query_builder,
    source_management_service,
    space_data_discovery_service,
    storage_configuration_requests,
    storage_configuration_service,
    storage_configuration_validator,
    storage_operation_coordinator,
    system_status_service,
    template_management_service,
    user_management_service,
    variant_service,
)

AuthenticationService = authentication_service.AuthenticationService
AuthorizationService = authorization_service.AuthorizationService
AuditTrailService = audit_service.AuditTrailService
DashboardService = dashboard_service.DashboardService
DataDiscoveryService = data_discovery_service.DataDiscoveryService
DataSourceActivationService = data_source_activation_service.DataSourceActivationService
DataSourceAuthorizationService = (
    data_source_authorization_service.DataSourceAuthorizationService
)
DataSourceAvailabilitySummary = (
    data_source_activation_service.DataSourceAvailabilitySummary
)
DataSourcePermission = data_source_authorization_service.DataSourcePermission
DiscoveryConfigurationService = (
    discovery_configuration_service.DiscoveryConfigurationService
)
EvidenceApplicationService = evidence_service.EvidenceApplicationService
GeneApplicationService = gene_service.GeneApplicationService
IngestionSchedulingService = ingestion_scheduling_service.IngestionSchedulingService
PhenotypeApplicationService = phenotype_service.PhenotypeApplicationService
PublicationApplicationService = publication_service.PublicationApplicationService
PubMedDiscoveryService = pubmed_discovery_service.PubMedDiscoveryService
PubMedIngestionService = pubmed_ingestion_service.PubMedIngestionService
PubMedQueryBuilder = pubmed_query_builder.PubMedQueryBuilder
PubmedDownloadRequest = pubmed_discovery_service.PubmedDownloadRequest
RunPubmedSearchRequest = pubmed_discovery_service.RunPubmedSearchRequest
SessionRevocationContext = system_status_service.SessionRevocationContext
SourceManagementService = source_management_service.SourceManagementService
SpaceDataDiscoveryService = space_data_discovery_service.SpaceDataDiscoveryService
StorageConfigurationService = storage_configuration_service.StorageConfigurationService
StorageConfigurationValidator = (
    storage_configuration_validator.StorageConfigurationValidator
)
StorageOperationCoordinator = storage_operation_coordinator.StorageOperationCoordinator
SystemStatusService = system_status_service.SystemStatusService
TemplateManagementService = template_management_service.TemplateManagementService
UserManagementService = user_management_service.UserManagementService
VariantApplicationService = variant_service.VariantApplicationService

CreateSourceRequest = source_management_service.CreateSourceRequest
UpdateSourceRequest = source_management_service.UpdateSourceRequest
CreateStorageConfigurationRequest = (
    storage_configuration_requests.CreateStorageConfigurationRequest
)
UpdateStorageConfigurationRequest = (
    storage_configuration_requests.UpdateStorageConfigurationRequest
)
CreateTemplateRequest = template_management_service.CreateTemplateRequest
UpdateTemplateRequest = template_management_service.UpdateTemplateRequest
UserRole = data_source_authorization_service.UserRole

__all__ = [
    "AuthenticationService",
    "AuthorizationService",
    "AuditTrailService",
    "CreateSourceRequest",
    "CreateStorageConfigurationRequest",
    "CreateTemplateRequest",
    "DashboardService",
    "DataDiscoveryService",
    "DataSourceActivationService",
    "DataSourceAuthorizationService",
    "DataSourceAvailabilitySummary",
    "DataSourcePermission",
    "DiscoveryConfigurationService",
    "EvidenceApplicationService",
    "GeneApplicationService",
    "IngestionSchedulingService",
    "PhenotypeApplicationService",
    "PubMedDiscoveryService",
    "PubMedIngestionService",
    "PubMedQueryBuilder",
    "PubmedDownloadRequest",
    "PublicationApplicationService",
    "RunPubmedSearchRequest",
    "SessionRevocationContext",
    "SourceManagementService",
    "SpaceDataDiscoveryService",
    "StorageConfigurationService",
    "StorageConfigurationValidator",
    "StorageOperationCoordinator",
    "SystemStatusService",
    "TemplateManagementService",
    "UnifiedSearchService",
    "UpdateSourceRequest",
    "UpdateStorageConfigurationRequest",
    "UpdateTemplateRequest",
    "UserManagementService",
    "UserRole",
    "VariantApplicationService",
]
