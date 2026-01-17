"""Factory helpers for building data source AI test services."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import TYPE_CHECKING

from src.application.services import DataSourceAiTestService, DataSourceAiTestSettings
from src.database.session import SessionLocal
from src.infrastructure.data_sources import PubMedSourceGateway
from src.infrastructure.llm.flujo_agent_adapter import FlujoAgentAdapter
from src.infrastructure.repositories import (
    SqlAlchemyResearchSpaceRepository,
    SqlAlchemyUserDataSourceRepository,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.orm import Session

DEFAULT_AI_TEST_SAMPLE_SIZE = 5


def build_data_source_ai_test_service(
    *,
    session: Session,
) -> DataSourceAiTestService:
    """Create a fully wired AI test service for the current session."""
    source_repository = SqlAlchemyUserDataSourceRepository(session)
    research_space_repository = SqlAlchemyResearchSpaceRepository(session)
    model_name = os.getenv("MED13_AI_AGENT_MODEL", "openai:gpt-4o-mini")
    ai_agent = FlujoAgentAdapter(model=model_name)

    return DataSourceAiTestService(
        source_repository=source_repository,
        pubmed_gateway=PubMedSourceGateway(),
        ai_agent=ai_agent,
        research_space_repository=research_space_repository,
        settings=DataSourceAiTestSettings(
            sample_size=DEFAULT_AI_TEST_SAMPLE_SIZE,
            ai_model_name=model_name,
        ),
    )


@contextmanager
def data_source_ai_test_service_context(
    *,
    session: Session | None = None,
) -> Iterator[DataSourceAiTestService]:
    """Context manager that yields a test service and closes the session."""
    local_session = session or SessionLocal()
    try:
        service = build_data_source_ai_test_service(session=local_session)
        yield service
    finally:
        if session is None:
            local_session.close()


__all__ = [
    "DEFAULT_AI_TEST_SAMPLE_SIZE",
    "build_data_source_ai_test_service",
    "data_source_ai_test_service_context",
]
