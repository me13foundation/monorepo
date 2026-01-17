"""Tests for the data source AI test service."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

from src.application.services.data_source_ai_test_service import (
    DataSourceAiTestService,
    DataSourceAiTestSettings,
)
from src.application.services.ports.ai_agent_port import AiAgentPort
from src.domain.entities.research_space import ResearchSpace, SpaceStatus
from src.domain.entities.user_data_source import (
    IngestionSchedule,
    QualityMetrics,
    SourceConfiguration,
    SourceStatus,
    SourceType,
    UserDataSource,
)
from src.domain.repositories.research_space_repository import ResearchSpaceRepository
from src.domain.repositories.user_data_source_repository import UserDataSourceRepository
from src.domain.services.pubmed_ingestion import PubMedGateway

if TYPE_CHECKING:
    from uuid import UUID

    from src.domain.entities.data_source_configs import PubMedQueryConfig
    from src.type_definitions.common import (
        RawRecord,
        SourceMetadata,
        StatisticsResponse,
    )


class StubPubMedGateway(PubMedGateway):
    """Stub PubMed gateway returning pre-defined records."""

    def __init__(self, records: list[RawRecord]) -> None:
        self._records = records
        self.called_queries: list[str] = []

    async def fetch_records(self, config: PubMedQueryConfig) -> list[RawRecord]:
        self.called_queries.append(config.query)
        return self._records


class StubAiAgent(AiAgentPort):
    """Stub AI agent returning a predetermined query."""

    def __init__(self, query: str) -> None:
        self._query = query

    async def generate_intelligent_query(
        self,
        research_space_description: str,
        user_instructions: str,
        source_type: str,
    ) -> str:
        return self._query


class StubResearchSpaceRepository(ResearchSpaceRepository):
    """Stub research space repository."""

    def __init__(self, space: ResearchSpace | None) -> None:
        self._space = space

    def save(self, space: ResearchSpace) -> ResearchSpace:  # pragma: no cover
        self._space = space
        return space

    def find_by_id(self, space_id: UUID) -> ResearchSpace | None:
        if self._space and self._space.id == space_id:
            return self._space
        return None

    def find_by_slug(self, slug: str) -> ResearchSpace | None:  # pragma: no cover
        return None

    def find_by_owner(  # pragma: no cover
        self,
        owner_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ResearchSpace]:
        return []

    def find_by_status(  # pragma: no cover
        self,
        status: SpaceStatus,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ResearchSpace]:
        return []

    def find_active_spaces(  # pragma: no cover
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ResearchSpace]:
        return []

    def search_by_name(  # pragma: no cover
        self,
        query: str,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ResearchSpace]:
        return []

    def slug_exists(self, slug: str) -> bool:  # pragma: no cover
        return False

    def delete(self, space_id: UUID) -> bool:  # pragma: no cover
        return False

    def exists(self, space_id: UUID) -> bool:  # pragma: no cover
        return self._space is not None and self._space.id == space_id

    def count_by_owner(self, owner_id: UUID) -> int:  # pragma: no cover
        return 0


class StubUserDataSourceRepository(UserDataSourceRepository):
    """Stub user data source repository."""

    def __init__(self, source: UserDataSource | None) -> None:
        self._source = source

    def save(self, source: UserDataSource) -> UserDataSource:  # pragma: no cover
        self._source = source
        return source

    def find_by_id(self, source_id: UUID) -> UserDataSource | None:
        if self._source and self._source.id == source_id:
            return self._source
        return None

    def find_by_owner(  # pragma: no cover
        self,
        owner_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[UserDataSource]:
        return []

    def find_by_type(  # pragma: no cover
        self,
        source_type: SourceType,
        skip: int = 0,
        limit: int = 50,
    ) -> list[UserDataSource]:
        return []

    def find_by_status(  # pragma: no cover
        self,
        status: SourceStatus,
        skip: int = 0,
        limit: int = 50,
    ) -> list[UserDataSource]:
        return []

    def find_active_sources(  # pragma: no cover
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[UserDataSource]:
        return []

    def find_by_tag(  # pragma: no cover
        self,
        tag: str,
        skip: int = 0,
        limit: int = 50,
    ) -> list[UserDataSource]:
        return []

    def search_by_name(  # pragma: no cover
        self,
        query: str,
        owner_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[UserDataSource]:
        return []

    def update_status(
        self,
        source_id: UUID,
        status: SourceStatus,
    ) -> UserDataSource | None:  # pragma: no cover
        return None

    def update_quality_metrics(
        self,
        source_id: UUID,
        metrics: QualityMetrics,
    ) -> UserDataSource | None:  # pragma: no cover
        return None

    def update_configuration(
        self,
        source_id: UUID,
        config: SourceConfiguration,
    ) -> UserDataSource | None:  # pragma: no cover
        return None

    def update_ingestion_schedule(
        self,
        source_id: UUID,
        schedule: IngestionSchedule,
    ) -> UserDataSource | None:  # pragma: no cover
        return None

    def record_ingestion(
        self,
        source_id: UUID,
    ) -> UserDataSource | None:  # pragma: no cover
        return None

    def delete(self, source_id: UUID) -> bool:  # pragma: no cover
        return False

    def count_by_owner(self, owner_id: UUID) -> int:  # pragma: no cover
        return 0

    def count_by_status(self, status: SourceStatus) -> int:  # pragma: no cover
        return 0

    def count_by_type(self, source_type: SourceType) -> int:  # pragma: no cover
        return 0

    def exists(self, source_id: UUID) -> bool:  # pragma: no cover
        return self._source is not None and self._source.id == source_id

    def get_statistics(self) -> StatisticsResponse:  # pragma: no cover
        return {}


def build_pubmed_source(
    *,
    source_id: UUID,
    research_space_id: UUID | None,
    ai_enabled: bool,
) -> UserDataSource:
    metadata: SourceMetadata = {
        "query": "MED13",
        "max_results": 50,
        "agent_config": {
            "is_ai_managed": ai_enabled,
            "agent_prompt": "Focus on MED13 clinical studies.",
            "use_research_space_context": True,
        },
    }
    return UserDataSource(
        id=source_id,
        owner_id=uuid4(),
        research_space_id=research_space_id,
        name="Test PubMed",
        description="Test",
        source_type=SourceType.PUBMED,
        template_id=None,
        configuration=SourceConfiguration(metadata=metadata),
    )


@pytest.mark.asyncio
async def test_ai_test_success_returns_result() -> None:
    source_id = uuid4()
    space_id = uuid4()
    space = ResearchSpace(
        id=space_id,
        slug="test-space",
        name="Test Space",
        description="Study MED13 variants",
        owner_id=uuid4(),
        status=SpaceStatus.ACTIVE,
    )
    source = build_pubmed_source(
        source_id=source_id,
        research_space_id=space_id,
        ai_enabled=True,
    )

    service = DataSourceAiTestService(
        source_repository=StubUserDataSourceRepository(source),
        pubmed_gateway=StubPubMedGateway(
            [
                {
                    "pubmed_id": "1",
                    "title": "MED13 findings in cardiac research",
                    "doi": "10.1000/xyz",
                    "pmc_id": "PMC12345",
                    "publication_date": "2024-01-01",
                    "journal": {"title": "Nature Medicine"},
                },
            ],
        ),
        ai_agent=StubAiAgent("MED13[Title/Abstract]"),
        research_space_repository=StubResearchSpaceRepository(space),
        settings=DataSourceAiTestSettings(
            sample_size=3,
            ai_model_name="openai:gpt-test",
        ),
    )

    result = await service.test_ai_configuration(source_id)

    assert result.success is True
    assert result.executed_query == "MED13[Title/Abstract]"
    assert result.model == "openai:gpt-test"
    assert "MED13" in result.search_terms
    assert result.fetched_records == 1
    assert result.sample_size == 3
    assert len(result.findings) == 1
    assert result.findings[0].title == "MED13 findings in cardiac research"
    assert any(link.label == "PubMed" for link in result.findings[0].links)


@pytest.mark.asyncio
async def test_ai_disabled_returns_failure() -> None:
    source_id = uuid4()
    source = build_pubmed_source(
        source_id=source_id,
        research_space_id=None,
        ai_enabled=False,
    )

    service = DataSourceAiTestService(
        source_repository=StubUserDataSourceRepository(source),
        pubmed_gateway=StubPubMedGateway([{"pubmed_id": "1"}]),
        ai_agent=StubAiAgent("MED13"),
        research_space_repository=StubResearchSpaceRepository(None),
        settings=DataSourceAiTestSettings(ai_model_name="openai:gpt-test"),
    )

    result = await service.test_ai_configuration(source_id)

    assert result.success is False
    assert "AI-managed queries are disabled" in result.message
    assert result.findings == []


@pytest.mark.asyncio
async def test_no_results_returns_failure() -> None:
    source_id = uuid4()
    source = build_pubmed_source(
        source_id=source_id,
        research_space_id=None,
        ai_enabled=True,
    )

    service = DataSourceAiTestService(
        source_repository=StubUserDataSourceRepository(source),
        pubmed_gateway=StubPubMedGateway([]),
        ai_agent=StubAiAgent("MED13"),
        research_space_repository=StubResearchSpaceRepository(None),
        settings=DataSourceAiTestSettings(ai_model_name="openai:gpt-test"),
    )

    result = await service.test_ai_configuration(source_id)

    assert result.success is False
    assert "no results" in result.message.lower()
    assert result.findings == []
