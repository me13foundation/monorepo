"""Factory helpers for building ingestion scheduling services with infrastructure adapters."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from src.application.services.ingestion_scheduling_service import (
    IngestionSchedulingService,
)
from src.application.services.pubmed_discovery_service import PubMedDiscoveryService
from src.application.services.pubmed_ingestion_service import PubMedIngestionService
from src.application.services.pubmed_query_builder import PubMedQueryBuilder
from src.application.services.storage_configuration_service import (
    StorageConfigurationService,
)
from src.application.services.storage_operation_coordinator import (
    StorageOperationCoordinator,
)
from src.database.session import SessionLocal
from src.domain.entities.user_data_source import SourceType
from src.infrastructure.data_sources import PubMedSourceGateway
from src.infrastructure.data_sources.pubmed_search_gateway import (
    DeterministicPubMedSearchGateway,
    SimplePubMedPdfGateway,
)
from src.infrastructure.repositories.data_discovery_repository_impl import (
    SQLAlchemyDiscoverySearchJobRepository,
)
from src.infrastructure.repositories.ingestion_job_repository import (
    SqlAlchemyIngestionJobRepository,
)
from src.infrastructure.repositories.publication_repository import (
    SqlAlchemyPublicationRepository,
)
from src.infrastructure.repositories.storage_repository import (
    SqlAlchemyStorageConfigurationRepository,
    SqlAlchemyStorageOperationRepository,
)
from src.infrastructure.repositories.user_data_source_repository import (
    SqlAlchemyUserDataSourceRepository,
)
from src.infrastructure.scheduling import InMemoryScheduler
from src.infrastructure.storage import initialize_storage_plugins

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.orm import Session

    from src.application.services.ports.scheduler_port import SchedulerPort

SCHEDULER_BACKEND = InMemoryScheduler()


def build_ingestion_scheduling_service(
    *,
    session: Session,
    scheduler: SchedulerPort | None = None,
) -> IngestionSchedulingService:
    """Create a fully wired ingestion scheduling service for the current session."""
    publication_repository = SqlAlchemyPublicationRepository(session)
    user_source_repository = SqlAlchemyUserDataSourceRepository(session)
    job_repository = SqlAlchemyIngestionJobRepository(session)

    storage_configuration_repository = SqlAlchemyStorageConfigurationRepository(
        session,
    )
    storage_operation_repository = SqlAlchemyStorageOperationRepository(session)
    storage_service = StorageConfigurationService(
        configuration_repository=storage_configuration_repository,
        operation_repository=storage_operation_repository,
        plugin_registry=initialize_storage_plugins(),
    )

    pubmed_service = PubMedIngestionService(
        gateway=PubMedSourceGateway(),
        publication_repository=publication_repository,
        storage_service=storage_service,
    )

    storage_coordinator = StorageOperationCoordinator(storage_service)

    discovery_job_repository = SQLAlchemyDiscoverySearchJobRepository(session)
    query_builder = PubMedQueryBuilder()
    search_gateway = DeterministicPubMedSearchGateway(query_builder)
    pdf_gateway = SimplePubMedPdfGateway()
    pubmed_discovery_service = PubMedDiscoveryService(
        job_repository=discovery_job_repository,
        query_builder=query_builder,
        search_gateway=search_gateway,
        pdf_gateway=pdf_gateway,
        storage_coordinator=storage_coordinator,
    )

    ingestion_services = {
        SourceType.PUBMED: pubmed_service.ingest,
    }

    return IngestionSchedulingService(
        scheduler=scheduler or SCHEDULER_BACKEND,
        source_repository=user_source_repository,
        job_repository=job_repository,
        ingestion_services=ingestion_services,
        storage_operation_repository=storage_operation_repository,
        pubmed_discovery_service=pubmed_discovery_service,
    )


@contextmanager
def ingestion_scheduling_service_context(
    *,
    session: Session | None = None,
    scheduler: SchedulerPort | None = None,
) -> Iterator[IngestionSchedulingService]:
    """Context manager that yields a scheduling service and closes the session."""
    local_session = session or SessionLocal()
    try:
        service = build_ingestion_scheduling_service(
            session=local_session,
            scheduler=scheduler,
        )
        yield service
    finally:
        if session is None:
            local_session.close()
