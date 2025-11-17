"""
UNIFIED Dependency injection container for MED13 Resource Library.

Provides centralized dependency management for all application services.
Combines Clean Architecture (auth system) with legacy patterns during transition.
"""

from __future__ import annotations

import asyncio
import logging
import os
import secrets
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.application.curation.conflict_detector import ConflictDetector
from src.application.curation.repositories.review_repository import (
    SqlAlchemyReviewRepository,
)
from src.application.curation.services.curation_service import CurationService
from src.application.curation.services.detail_service import CurationDetailService
from src.application.export.export_service import BulkExportService
from src.application.search.search_service import UnifiedSearchService
from src.application.services.authentication_service import AuthenticationService
from src.application.services.authorization_service import AuthorizationService
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
from src.application.services.user_management_service import UserManagementService
from src.application.services.variant_service import VariantApplicationService
from src.database.sqlite_utils import build_sqlite_connect_args, configure_sqlite_engine
from src.database.url_resolver import resolve_async_database_url
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
from src.infrastructure.repositories.sqlalchemy_session_repository import (
    SqlAlchemySessionRepository,
)
from src.infrastructure.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
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
from src.infrastructure.security.jwt_provider import JWTProvider
from src.infrastructure.security.password_hasher import PasswordHasher
from src.infrastructure.storage import initialize_storage_plugins

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.orm import Session

    from src.domain.services.security.jwt_provider import JWTProviderService
    from src.domain.services.security.password_hasher import PasswordHasherService
    from src.type_definitions.common import HealthCheckResponse

DEFAULT_DEV_JWT_SECRET = os.getenv("MED13_DEV_JWT_SECRET") or secrets.token_urlsafe(64)

logger = logging.getLogger(__name__)


class DependencyContainer:
    """
    UNIFIED Dependency injection container for MED13 Resource Library.

    Combines Clean Architecture (async auth system) with legacy sync patterns.
    Provides centralized configuration and lifecycle management for all dependencies.
    """

    def __init__(
        self,
        database_url: str | None = None,
        jwt_secret_key: str | None = None,
        jwt_algorithm: str = "HS256",
    ):
        resolved_db_url = database_url or resolve_async_database_url()
        self.database_url = resolved_db_url
        resolved_secret = jwt_secret_key or DEFAULT_DEV_JWT_SECRET
        self.jwt_secret_key = resolved_secret
        self.jwt_algorithm = jwt_algorithm

        # Initialize ASYNC database engine (for Clean Architecture - auth)
        engine_kwargs: dict[str, object] = {
            "echo": False,  # Set to True for debugging
            "pool_pre_ping": True,
        }
        if resolved_db_url.startswith("sqlite"):
            engine_kwargs["connect_args"] = build_sqlite_connect_args(
                include_thread_check=False,
            )
            engine_kwargs["poolclass"] = NullPool

        self.engine = create_async_engine(
            resolved_db_url,
            **engine_kwargs,
        )

        if resolved_db_url.startswith("sqlite"):
            configure_sqlite_engine(self.engine.sync_engine)

        # Create async session factory
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Initialize security components (Clean Architecture)
        self.password_hasher: PasswordHasherService = PasswordHasher()
        self.jwt_provider: JWTProviderService = JWTProvider(
            secret_key=resolved_secret,
            algorithm=jwt_algorithm,
        )

        # Initialize Clean Architecture repositories (lazy-loaded, async)
        self._user_repository: SqlAlchemyUserRepository | None = None
        self._session_repository: SqlAlchemySessionRepository | None = None

        # Initialize Clean Architecture services (lazy-loaded, async)
        self._authentication_service: AuthenticationService | None = None
        self._authentication_service_loop: asyncio.AbstractEventLoop | None = None
        self._authorization_service: AuthorizationService | None = None
        self._authorization_service_loop: asyncio.AbstractEventLoop | None = None
        self._user_management_service: UserManagementService | None = None
        self._user_management_service_loop: asyncio.AbstractEventLoop | None = None

        # Initialize Legacy domain services (pure business logic, no dependencies)
        self._gene_domain_service: GeneDomainService | None = None
        self._variant_domain_service: VariantDomainService | None = None
        self._evidence_domain_service: EvidenceDomainService | None = None
        self._storage_plugin_registry = initialize_storage_plugins()

    def get_user_repository(self) -> SqlAlchemyUserRepository:
        if self._user_repository is None:
            self._user_repository = SqlAlchemyUserRepository(self.async_session_factory)
        return self._user_repository

    def get_session_repository(self) -> SqlAlchemySessionRepository:
        if self._session_repository is None:
            self._session_repository = SqlAlchemySessionRepository(
                self.async_session_factory,
            )
        return self._session_repository

    async def get_authentication_service(self) -> AuthenticationService:
        current_loop = asyncio.get_running_loop()
        if (
            self._authentication_service is None
            or self._authentication_service_loop is not current_loop
        ):
            user_repository = self.get_user_repository()
            session_repository = self.get_session_repository()
            self._authentication_service = AuthenticationService(
                user_repository=user_repository,
                session_repository=session_repository,
                jwt_provider=self.jwt_provider,
                password_hasher=self.password_hasher,
            )
            self._authentication_service_loop = current_loop
        return self._authentication_service

    async def get_authorization_service(self) -> AuthorizationService:
        current_loop = asyncio.get_running_loop()
        if (
            self._authorization_service is None
            or self._authorization_service_loop is not current_loop
        ):
            user_repository = self.get_user_repository()
            self._authorization_service = AuthorizationService(
                user_repository=user_repository,
            )
            self._authorization_service_loop = current_loop
        return self._authorization_service

    async def get_user_management_service(self) -> UserManagementService:
        current_loop = asyncio.get_running_loop()
        if (
            self._user_management_service is None
            or self._user_management_service_loop is not current_loop
        ):
            user_repository = self.get_user_repository()
            self._user_management_service = UserManagementService(
                user_repository=user_repository,
                password_hasher=self.password_hasher,
            )
            self._user_management_service_loop = current_loop
        return self._user_management_service

    # LEGACY SYSTEM METHODS (Sync SQLAlchemy for backward compatibility)

    def get_gene_domain_service(self) -> GeneDomainService:
        if self._gene_domain_service is None:
            self._gene_domain_service = GeneDomainService()
        return self._gene_domain_service

    def get_variant_domain_service(self) -> VariantDomainService:
        if self._variant_domain_service is None:
            self._variant_domain_service = VariantDomainService()
        return self._variant_domain_service

    def get_evidence_domain_service(self) -> EvidenceDomainService:
        if self._evidence_domain_service is None:
            self._evidence_domain_service = EvidenceDomainService()
        return self._evidence_domain_service

    # LEGACY APPLICATION SERVICES

    def create_unified_search_service(self, session: Session) -> UnifiedSearchService:
        return UnifiedSearchService(
            gene_service=self.create_gene_application_service(session),
            variant_service=self.create_variant_application_service(session),
            phenotype_service=self.create_phenotype_application_service(session),
            evidence_service=self.create_evidence_application_service(session),
        )

    def create_curation_detail_service(
        self,
        session: Session,
    ) -> CurationDetailService:
        conflict_detector = ConflictDetector(
            variant_domain_service=self.get_variant_domain_service(),
            evidence_domain_service=self.get_evidence_domain_service(),
        )

        return CurationDetailService(
            variant_service=self.create_variant_application_service(session),
            evidence_service=self.create_evidence_application_service(session),
            phenotype_repository=SqlAlchemyPhenotypeRepository(session),
            conflict_detector=conflict_detector,
            review_repository=SqlAlchemyReviewRepository(),
            db_session=session,
        )

    async def get_db_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.async_session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    @asynccontextmanager
    async def lifespan_context(self) -> AsyncGenerator[None, None]:
        # Startup
        try:
            yield
        finally:
            # Shutdown
            await self.engine.dispose()

    async def health_check(self) -> HealthCheckResponse:
        health_status: HealthCheckResponse = {
            "database": False,
            "jwt_provider": False,
            "password_hasher": False,
            "services": False,
        }

        try:
            # Test database connection
            async with self.async_session_factory() as session:
                await session.execute(text("SELECT 1"))
                health_status["database"] = True
        except (SQLAlchemyError, RuntimeError) as exc:
            logger.warning("Database health check failed: %s", exc)

        # Test JWT provider
        try:
            test_token = self.jwt_provider.create_access_token(uuid4(), "viewer")
            decoded = self.jwt_provider.decode_token(test_token)
            health_status["jwt_provider"] = decoded is not None
        except ValueError as exc:
            logger.warning("JWT provider health check failed: %s", exc)

        # Test password hasher
        try:
            test_hash = self.password_hasher.hash_password("test-password")
            is_valid = self.password_hasher.verify_password("test-password", test_hash)
            health_status["password_hasher"] = is_valid
        except ValueError as exc:
            logger.warning("Password hasher health check failed: %s", exc)

        # Test services initialization
        try:
            await self.get_authentication_service()
            await self.get_authorization_service()
            await self.get_user_management_service()
            health_status["services"] = True
        except (SQLAlchemyError, ValueError, RuntimeError) as exc:
            logger.warning("Service initialization health check failed: %s", exc)

        return health_status

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
        return StorageConfigurationService(
            configuration_repository=configuration_repository,
            operation_repository=operation_repository,
            plugin_registry=self._storage_plugin_registry,
        )

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
        # Create repositories
        user_data_source_repo = SqlAlchemyUserDataSourceRepository(session)
        template_repo = SqlAlchemySourceTemplateRepository(session)
        return SourceManagementService(
            user_data_source_repository=user_data_source_repo,
            source_template_repository=template_repo,
        )

    def create_data_discovery_service(self, session: Session) -> DataDiscoveryService:
        # Create repositories
        session_repo = SQLAlchemyDataDiscoverySessionRepository(session)
        catalog_repo = SQLAlchemySourceCatalogRepository(session)
        query_repo = SQLAlchemyQueryTestResultRepository(session)

        # Create query client
        query_client = HTTPQueryClient()

        # Create source management service
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


# Global container instance (will be configured in main.py)
container = DependencyContainer()
