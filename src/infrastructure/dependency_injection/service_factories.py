"""
Factory mixin for building application services used by the dependency container.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.application.curation.repositories.review_repository import (
    SqlAlchemyReviewRepository,
)
from src.application.curation.services.curation_service import CurationService
from src.application.export.export_service import BulkExportService
from src.application.search.search_service import UnifiedSearchService
from src.application.services.data_discovery_service import DataDiscoveryService
from src.application.services.data_source_activation_service import (
    DataSourceActivationService,
)
from src.application.services.evidence_service import EvidenceApplicationService
from src.application.services.gene_service import GeneApplicationService
from src.application.services.phenotype_service import PhenotypeApplicationService
from src.application.services.publication_service import PublicationApplicationService
from src.application.services.source_management_service import SourceManagementService
from src.application.services.storage_configuration_service import (
    StorageConfigurationService,
)
from src.application.services.storage_operation_coordinator import (
    StorageOperationCoordinator,
)
from src.application.services.variant_service import VariantApplicationService
from src.domain.services.evidence_domain_service import EvidenceDomainService
from src.domain.services.gene_domain_service import GeneDomainService
from src.domain.services.variant_domain_service import VariantDomainService
from src.infrastructure.queries.source_query_client import HTTPQueryClient
from src.infrastructure.repositories.data_discovery_repository_impl import (
    SQLAlchemyDataDiscoverySessionRepository,
    SQLAlchemyQueryTestResultRepository,
    SQLAlchemySourceCatalogRepository,
)
from src.infrastructure.repositories.data_source_activation_repository import (
    SqlAlchemyDataSourceActivationRepository,
)
from src.infrastructure.repositories.evidence_repository import (
    SqlAlchemyEvidenceRepository,
)
from src.infrastructure.repositories.gene_repository import SqlAlchemyGeneRepository
from src.infrastructure.repositories.phenotype_repository import (
    SqlAlchemyPhenotypeRepository,
)
from src.infrastructure.repositories.publication_repository import (
    SqlAlchemyPublicationRepository,
)
from src.infrastructure.repositories.source_template_repository import (
    SqlAlchemySourceTemplateRepository,
)
from src.infrastructure.repositories.storage_repository import (
    SqlAlchemyStorageConfigurationRepository,
    SqlAlchemyStorageOperationRepository,
)
from src.infrastructure.repositories.user_data_source_repository import (
    SqlAlchemyUserDataSourceRepository,
)
from src.infrastructure.repositories.variant_repository import (
    SqlAlchemyVariantRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from src.application.services.system_status_service import SystemStatusService
    from src.domain.services.storage_metrics import StorageMetricsRecorder
    from src.domain.services.storage_providers import StoragePluginRegistry


class ApplicationServiceFactoryMixin:
    """Provides helper factory methods shared by the dependency container."""

    if TYPE_CHECKING:
        _storage_plugin_registry: StoragePluginRegistry
        _storage_metrics_recorder: StorageMetricsRecorder

        def get_system_status_service(self) -> SystemStatusService:
            ...

    def create_gene_application_service(
        self,
        session: Session,
    ) -> GeneApplicationService:
        gene_repository = SqlAlchemyGeneRepository(session)
        gene_domain_service = GeneDomainService()
        variant_repository = SqlAlchemyVariantRepository(session)
        return GeneApplicationService(
            gene_repository=gene_repository,
            gene_domain_service=gene_domain_service,
            variant_repository=variant_repository,
        )

    def create_variant_application_service(
        self,
        session: Session,
    ) -> VariantApplicationService:
        variant_repository = SqlAlchemyVariantRepository(session)
        variant_domain_service = VariantDomainService()
        evidence_repository = SqlAlchemyEvidenceRepository(session)
        return VariantApplicationService(
            variant_repository=variant_repository,
            variant_domain_service=variant_domain_service,
            evidence_repository=evidence_repository,
        )

    def create_phenotype_application_service(
        self,
        session: Session,
    ) -> PhenotypeApplicationService:
        phenotype_repository = SqlAlchemyPhenotypeRepository(session)
        return PhenotypeApplicationService(
            phenotype_repository=phenotype_repository,
        )

    def create_evidence_application_service(
        self,
        session: Session,
    ) -> EvidenceApplicationService:
        evidence_repository = SqlAlchemyEvidenceRepository(session)
        evidence_domain_service = EvidenceDomainService()
        return EvidenceApplicationService(
            evidence_repository=evidence_repository,
            evidence_domain_service=evidence_domain_service,
        )

    def create_publication_application_service(
        self,
        session: Session,
    ) -> PublicationApplicationService:
        publication_repository = SqlAlchemyPublicationRepository(session)
        evidence_repository = SqlAlchemyEvidenceRepository(session)
        return PublicationApplicationService(
            publication_repository=publication_repository,
            evidence_repository=evidence_repository,
        )

    def create_storage_configuration_service(
        self,
        session: Session,
    ) -> StorageConfigurationService:
        configuration_repository = SqlAlchemyStorageConfigurationRepository(session)
        operation_repository = SqlAlchemyStorageOperationRepository(session)
        system_status_service = self.get_system_status_service()
        return StorageConfigurationService(
            configuration_repository=configuration_repository,
            operation_repository=operation_repository,
            plugin_registry=self._storage_plugin_registry,
            system_status_service=system_status_service,
            metrics_recorder=self._storage_metrics_recorder,
        )

    def create_storage_operation_coordinator(
        self,
        session: Session,
    ) -> StorageOperationCoordinator:
        """Return a coordinator for storing artifacts via storage providers."""

        storage_service = self.create_storage_configuration_service(session)
        return StorageOperationCoordinator(storage_service)

    def create_curation_service(self, session: Session) -> CurationService:
        return CurationService(
            review_repository=SqlAlchemyReviewRepository(),
            variant_service=self.create_variant_application_service(session),
            evidence_service=self.create_evidence_application_service(session),
            phenotype_service=self.create_phenotype_application_service(session),
        )

    def create_export_service(self, session: Session) -> BulkExportService:
        return BulkExportService(
            gene_service=self.create_gene_application_service(session),
            variant_service=self.create_variant_application_service(session),
            phenotype_service=self.create_phenotype_application_service(session),
            evidence_service=self.create_evidence_application_service(session),
        )

    def create_search_service(self, session: Session) -> UnifiedSearchService:
        return UnifiedSearchService(
            gene_service=self.create_gene_application_service(session),
            variant_service=self.create_variant_application_service(session),
            phenotype_service=self.create_phenotype_application_service(session),
            evidence_service=self.create_evidence_application_service(session),
        )

    def create_source_management_service(
        self,
        session: Session,
    ) -> SourceManagementService:
        user_data_source_repo = SqlAlchemyUserDataSourceRepository(session)
        template_repo = SqlAlchemySourceTemplateRepository(session)
        return SourceManagementService(
            user_data_source_repository=user_data_source_repo,
            source_template_repository=template_repo,
        )

    def create_data_discovery_service(self, session: Session) -> DataDiscoveryService:
        session_repo = SQLAlchemyDataDiscoverySessionRepository(session)
        catalog_repo = SQLAlchemySourceCatalogRepository(session)
        query_repo = SQLAlchemyQueryTestResultRepository(session)

        query_client = HTTPQueryClient()

        source_service = self.create_source_management_service(session)
        template_repo = SqlAlchemySourceTemplateRepository(session)
        activation_repo = SqlAlchemyDataSourceActivationRepository(session)
        activation_service = DataSourceActivationService(activation_repo)

        return DataDiscoveryService(
            data_discovery_session_repository=session_repo,
            source_catalog_repository=catalog_repo,
            query_result_repository=query_repo,
            source_query_client=query_client,
            source_management_service=source_service,
            source_template_repository=template_repo,
            activation_service=activation_service,
        )


__all__ = ["ApplicationServiceFactoryMixin"]
