"""Factory helpers for building ingestion scheduling services with infrastructure adapters."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from src.application.services.ingestion_scheduling_service import (
    IngestionSchedulingService,
)
from src.application.services.pubmed_ingestion_service import PubMedIngestionService
from src.database.session import SessionLocal
from src.domain.entities.user_data_source import SourceType
from src.infrastructure.data_sources import PubMedSourceGateway
from src.infrastructure.repositories.ingestion_job_repository import (
    SqlAlchemyIngestionJobRepository,
)
from src.infrastructure.repositories.publication_repository import (
    SqlAlchemyPublicationRepository,
)
from src.infrastructure.repositories.user_data_source_repository import (
    SqlAlchemyUserDataSourceRepository,
)
from src.infrastructure.scheduling import InMemoryScheduler

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

    pubmed_service = PubMedIngestionService(
        gateway=PubMedSourceGateway(),
        publication_repository=publication_repository,
    )

    ingestion_services = {
        SourceType.PUBMED: pubmed_service.ingest,
    }

    return IngestionSchedulingService(
        scheduler=scheduler or SCHEDULER_BACKEND,
        source_repository=user_source_repository,
        job_repository=job_repository,
        ingestion_services=ingestion_services,
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
