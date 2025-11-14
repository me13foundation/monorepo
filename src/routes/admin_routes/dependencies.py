"""
Shared dependencies and constants for admin routes.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.application.services.data_source_activation_service import (
    DataSourceActivationService,
)
from src.application.services.data_source_authorization_service import (
    DataSourceAuthorizationService,
)
from src.application.services.source_management_service import (
    SourceManagementService,
)
from src.application.services.template_management_service import (
    TemplateManagementService,
)
from src.database.session import SessionLocal
from src.domain.entities.data_discovery_session import SourceCatalogEntry
from src.infrastructure.repositories.data_discovery_repository_impl import (
    SQLAlchemySourceCatalogRepository,
)
from src.infrastructure.repositories.data_source_activation_repository import (
    SqlAlchemyDataSourceActivationRepository,
)
from src.infrastructure.repositories.source_template_repository import (
    SqlAlchemySourceTemplateRepository,
)
from src.infrastructure.repositories.user_data_source_repository import (
    SqlAlchemyUserDataSourceRepository,
)

DEFAULT_OWNER_ID = UUID("00000000-0000-0000-0000-000000000001")
SYSTEM_ACTOR_ID = DEFAULT_OWNER_ID


def get_db_session() -> Session:
    """Create a bare SQLAlchemy session for admin services."""
    return SessionLocal()


def get_source_service() -> SourceManagementService:
    """Instantiate the SourceManagementService with SQLAlchemy repositories."""
    session = get_db_session()
    user_repo = SqlAlchemyUserDataSourceRepository(session)
    template_repo = SqlAlchemySourceTemplateRepository(session)
    return SourceManagementService(user_repo, template_repo)


def get_template_service() -> TemplateManagementService:
    """Instantiate the TemplateManagementService."""
    session = get_db_session()
    template_repo = SqlAlchemySourceTemplateRepository(session)
    return TemplateManagementService(template_repo)


def get_activation_service() -> DataSourceActivationService:
    """Instantiate the DataSourceActivationService."""
    session = get_db_session()
    activation_repo = SqlAlchemyDataSourceActivationRepository(session)
    return DataSourceActivationService(activation_repo)


async def get_auth_service() -> DataSourceAuthorizationService:
    """Instantiate the authorization service."""
    return DataSourceAuthorizationService()


def get_catalog_entry(session: Session, catalog_entry_id: str) -> SourceCatalogEntry:
    """
    Retrieve a catalog entry or raise HTTP 404.

    Args:
        session: Active database session.
        catalog_entry_id: Identifier of the catalog entry to retrieve.
    """
    repo = SQLAlchemySourceCatalogRepository(session)
    entry = repo.find_by_id(catalog_entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Catalog entry not found")
    return entry


__all__ = [
    "DEFAULT_OWNER_ID",
    "SYSTEM_ACTOR_ID",
    "get_activation_service",
    "get_auth_service",
    "get_catalog_entry",
    "get_db_session",
    "get_source_service",
    "get_template_service",
]
