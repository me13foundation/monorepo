"""
UNIFIED Dependency injection container for MED13 Resource Library.

Provides centralized dependency management for all application services.
Combines Clean Architecture (auth system) with legacy patterns during transition.
"""

import asyncio
import logging
import os
import secrets
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

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
from src.application.services.evidence_service import EvidenceApplicationService
from src.application.services.gene_service import GeneApplicationService
from src.application.services.phenotype_service import PhenotypeApplicationService
from src.application.services.publication_service import PublicationApplicationService
from src.application.services.user_management_service import UserManagementService
from src.application.services.variant_service import VariantApplicationService
from src.domain.services.evidence_domain_service import EvidenceDomainService
from src.domain.services.gene_domain_service import GeneDomainService
from src.domain.services.variant_domain_service import VariantDomainService
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
from src.infrastructure.repositories.sqlalchemy_session_repository import (
    SqlAlchemySessionRepository,
)
from src.infrastructure.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from src.infrastructure.repositories.variant_repository import (
    SqlAlchemyVariantRepository,
)
from src.infrastructure.security.jwt_provider import JWTProvider
from src.infrastructure.security.password_hasher import PasswordHasher

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
        database_url: str = "sqlite+aiosqlite:///./med13.db",
        jwt_secret_key: str | None = None,
        jwt_algorithm: str = "HS256",
    ):
        """
        Initialize the unified dependency container.

        Args:
            database_url: Database connection string (async)
            jwt_secret_key: Secret key for JWT signing
            jwt_algorithm: JWT algorithm (default: HS256)
        """
        self.database_url = database_url
        resolved_secret = jwt_secret_key or DEFAULT_DEV_JWT_SECRET
        self.jwt_secret_key = resolved_secret
        self.jwt_algorithm = jwt_algorithm

        # Initialize ASYNC database engine (for Clean Architecture - auth)
        self.engine = create_async_engine(
            database_url,
            echo=False,  # Set to True for debugging
            pool_pre_ping=True,
        )

        # Create async session factory
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Initialize security components (Clean Architecture)
        self.password_hasher = PasswordHasher()
        self.jwt_provider = JWTProvider(
            secret_key=resolved_secret,
            algorithm=jwt_algorithm,
        )

        # Initialize Clean Architecture repositories (lazy-loaded, async)
        self._user_repository: SqlAlchemyUserRepository | None = None
        self._session_repository: SqlAlchemySessionRepository | None = None

        # Initialize Clean Architecture services (lazy-loaded, async)
        self._authentication_service: AuthenticationService | None = None
        self._authorization_service: AuthorizationService | None = None
        self._user_management_service: UserManagementService | None = None

        # Initialize Legacy domain services (pure business logic, no dependencies)
        self._gene_domain_service: GeneDomainService | None = None
        self._variant_domain_service: VariantDomainService | None = None
        self._evidence_domain_service: EvidenceDomainService | None = None

    def get_user_repository(self) -> SqlAlchemyUserRepository:
        """Get the user repository instance."""
        if self._user_repository is None:
            self._user_repository = SqlAlchemyUserRepository(self.async_session_factory)
        return self._user_repository

    def get_session_repository(self) -> SqlAlchemySessionRepository:
        """Get the session repository instance."""
        if self._session_repository is None:
            self._session_repository = SqlAlchemySessionRepository(
                self.async_session_factory,
            )
        return self._session_repository

    async def get_authentication_service(self) -> AuthenticationService:
        """Get the authentication service instance."""
        if self._authentication_service is None:
            user_repository = self.get_user_repository()
            session_repository = self.get_session_repository()
            self._authentication_service = AuthenticationService(
                user_repository=user_repository,
                session_repository=session_repository,
                jwt_provider=self.jwt_provider,
                password_hasher=self.password_hasher,
            )
        return self._authentication_service

    async def get_authorization_service(self) -> AuthorizationService:
        """Get the authorization service instance."""
        if self._authorization_service is None:
            user_repository = self.get_user_repository()
            self._authorization_service = AuthorizationService(
                user_repository=user_repository,
            )
        return self._authorization_service

    async def get_user_management_service(self) -> UserManagementService:
        """Get the user management service instance."""
        if self._user_management_service is None:
            user_repository = self.get_user_repository()
            self._user_management_service = UserManagementService(
                user_repository=user_repository,
                password_hasher=self.password_hasher,
            )
        return self._user_management_service

    # LEGACY SYSTEM METHODS (Sync SQLAlchemy for backward compatibility)

    def get_gene_domain_service(self) -> GeneDomainService:
        """Get the gene domain service instance."""
        if self._gene_domain_service is None:
            self._gene_domain_service = GeneDomainService()
        return self._gene_domain_service

    def get_variant_domain_service(self) -> VariantDomainService:
        """Get the variant domain service instance."""
        if self._variant_domain_service is None:
            self._variant_domain_service = VariantDomainService()
        return self._variant_domain_service

    def get_evidence_domain_service(self) -> EvidenceDomainService:
        """Get the evidence domain service instance."""
        if self._evidence_domain_service is None:
            self._evidence_domain_service = EvidenceDomainService()
        return self._evidence_domain_service

    # LEGACY APPLICATION SERVICES

    def create_unified_search_service(self, session: Session) -> UnifiedSearchService:
        """Create a unified search service with all entity services."""
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
        """Create the curation detail service used by curator workflows."""
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
        """Get a database session (FastAPI dependency)."""
        async with self.async_session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    @asynccontextmanager
    async def lifespan_context(self) -> AsyncGenerator[None, None]:
        """FastAPI lifespan context manager."""
        # Startup
        try:
            yield
        finally:
            # Shutdown
            await self.engine.dispose()

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on all dependencies."""
        health_status = {
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
        """Create a gene application service with the given session."""
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
        """Create a variant application service with the given session."""
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
        """Create a phenotype application service with the given session."""
        phenotype_repository = SqlAlchemyPhenotypeRepository(session)
        return PhenotypeApplicationService(
            phenotype_repository=phenotype_repository,
        )

    def create_evidence_application_service(
        self,
        session: Session,
    ) -> EvidenceApplicationService:
        """Create an evidence application service with the given session."""
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
        """Create a publication application service with the given session."""
        publication_repository = SqlAlchemyPublicationRepository(session)
        return PublicationApplicationService(
            publication_repository=publication_repository,
        )

    def create_curation_service(self, session: Session) -> CurationService:
        """Create a curation service with the given session."""
        return CurationService(
            review_repository=SqlAlchemyReviewRepository(),
            variant_service=self.create_variant_application_service(session),
            evidence_service=self.create_evidence_application_service(session),
            phenotype_service=self.create_phenotype_application_service(session),
        )

    def create_export_service(self, session: Session) -> BulkExportService:
        """Create an export service with the given session."""
        return BulkExportService(
            gene_service=self.create_gene_application_service(session),
            variant_service=self.create_variant_application_service(session),
            phenotype_service=self.create_phenotype_application_service(session),
            evidence_service=self.create_evidence_application_service(session),
        )

    def create_search_service(self, session: Session) -> UnifiedSearchService:
        """Create a search service with the given session."""
        return UnifiedSearchService(
            gene_service=self.create_gene_application_service(session),
            variant_service=self.create_variant_application_service(session),
            phenotype_service=self.create_phenotype_application_service(session),
            evidence_service=self.create_evidence_application_service(session),
        )


# Global container instance (will be configured in main.py)
container = DependencyContainer()


# LEGACY SESSION SETUP (for backward compatibility)
def initialize_legacy_session(session: Session) -> None:
    """Legacy function - no longer needed. Services now take session as parameter."""
    # This function is kept for backward compatibility but no longer does anything


# FastAPI dependency functions (these will be called synchronously by FastAPI)
def get_user_repository_dependency() -> SqlAlchemyUserRepository:
    """FastAPI dependency for user repository."""
    return container.get_user_repository()


def get_authentication_service_dependency() -> AuthenticationService:
    """FastAPI dependency for authentication service."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create directly when event loop is running (FastAPI context)
            return AuthenticationService(
                user_repository=get_user_repository_dependency(),
                session_repository=SqlAlchemySessionRepository(
                    container.async_session_factory,
                ),
                jwt_provider=container.jwt_provider,
                password_hasher=container.password_hasher,
            )
        # Use async container method when no event loop
        return loop.run_until_complete(container.get_authentication_service())
    except RuntimeError:
        # Fallback when no event loop exists
        return AuthenticationService(
            user_repository=get_user_repository_dependency(),
            session_repository=SqlAlchemySessionRepository(
                container.async_session_factory,
            ),
            jwt_provider=container.jwt_provider,
            password_hasher=container.password_hasher,
        )


def get_user_management_service_dependency() -> UserManagementService:
    """FastAPI dependency for user management service."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create directly when event loop is running (FastAPI context)
            return UserManagementService(
                user_repository=get_user_repository_dependency(),
                password_hasher=container.password_hasher,
            )
        # Use async container method when no event loop
        return loop.run_until_complete(container.get_user_management_service())
    except RuntimeError:
        # Fallback when no event loop exists
        return UserManagementService(
            user_repository=get_user_repository_dependency(),
            password_hasher=container.password_hasher,
        )


# LEGACY DEPENDENCY FUNCTIONS (for backward compatibility)
def get_legacy_dependency_container() -> DependencyContainer:
    """Get the legacy dependency container for routes that still use the old system."""
    return container
