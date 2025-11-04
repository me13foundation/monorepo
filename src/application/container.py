"""
Dependency injection container for MED13 Resource Library.

Provides centralized dependency management for all application services.
"""

from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from ..infrastructure.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from ..infrastructure.repositories.sqlalchemy_session_repository import (
    SqlAlchemySessionRepository,
)
from ..infrastructure.security.password_hasher import PasswordHasher
from ..infrastructure.security.jwt_provider import JWTProvider
from .services.authentication_service import AuthenticationService
from .services.authorization_service import AuthorizationService
from .services.user_management_service import UserManagementService


class DependencyContainer:
    """
    Dependency injection container for managing application services.

    Provides centralized configuration and lifecycle management for all
    application dependencies.
    """

    def __init__(
        self,
        database_url: str = "sqlite+aiosqlite:///./med13.db",
        jwt_secret_key: str = "med13-resource-library-secret-key-for-development-testing-123456789012345678901234567890",
        jwt_algorithm: str = "HS256",
    ):
        """
        Initialize the dependency container.

        Args:
            database_url: Database connection string
            jwt_secret_key: Secret key for JWT signing
            jwt_algorithm: JWT algorithm (default: HS256)
        """
        self.database_url = database_url
        self.jwt_secret_key = jwt_secret_key
        self.jwt_algorithm = jwt_algorithm

        # Initialize database engine
        self.engine = create_async_engine(
            database_url,
            echo=False,  # Set to True for debugging
            pool_pre_ping=True,
        )

        # Create session factory
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Initialize security components
        self.password_hasher = PasswordHasher()
        self.jwt_provider = JWTProvider(
            secret_key=jwt_secret_key, algorithm=jwt_algorithm
        )

        # Initialize repositories (lazy-loaded)
        self._user_repository = None
        self._session_repository = None

        # Initialize services (lazy-loaded)
        self._authentication_service = None
        self._authorization_service = None
        self._user_management_service = None

    async def get_user_repository(self) -> SqlAlchemyUserRepository:
        """Get the user repository instance."""
        if self._user_repository is None:
            self._user_repository = SqlAlchemyUserRepository(self.async_session_factory)
        return self._user_repository

    async def get_session_repository(self) -> SqlAlchemySessionRepository:
        """Get the session repository instance."""
        if self._session_repository is None:
            self._session_repository = SqlAlchemySessionRepository(
                self.async_session_factory
            )
        return self._session_repository

    async def get_authentication_service(self) -> AuthenticationService:
        """Get the authentication service instance."""
        if self._authentication_service is None:
            user_repository = await self.get_user_repository()
            session_repository = await self.get_session_repository()
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
            user_repository = await self.get_user_repository()
            self._authorization_service = AuthorizationService(
                user_repository=user_repository
            )
        return self._authorization_service

    async def get_user_management_service(self) -> UserManagementService:
        """Get the user management service instance."""
        if self._user_management_service is None:
            user_repository = await self.get_user_repository()
            self._user_management_service = UserManagementService(
                user_repository=user_repository, password_hasher=self.password_hasher
            )
        return self._user_management_service

    async def get_db_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session (FastAPI dependency)."""
        async with self.async_session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    @asynccontextmanager
    async def lifespan_context(self):
        """FastAPI lifespan context manager."""
        # Startup
        try:
            yield
        finally:
            # Shutdown
            await self.engine.dispose()

    async def health_check(self) -> dict:
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
                await session.execute("SELECT 1")
                health_status["database"] = True
        except Exception:
            pass

        # Test JWT provider
        try:
            test_token = self.jwt_provider.create_access_token("test-user", "viewer")
            decoded = self.jwt_provider.decode_token(test_token)
            health_status["jwt_provider"] = decoded.get("sub") == "test-user"
        except Exception:
            pass

        # Test password hasher
        try:
            test_hash = self.password_hasher.hash_password("test-password")
            is_valid = self.password_hasher.verify_password("test-password", test_hash)
            health_status["password_hasher"] = is_valid
        except Exception:
            pass

        # Test services initialization
        try:
            await self.get_authentication_service()
            await self.get_authorization_service()
            await self.get_user_management_service()
            health_status["services"] = True
        except Exception:
            pass

        return health_status


# Global container instance (will be configured in main.py)
container = DependencyContainer()
