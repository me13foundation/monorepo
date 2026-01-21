"""Tests for QueryAgentService model selection functionality."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.agents.services.query_agent_service import (
    QueryAgentService,
    QueryAgentServiceDependencies,
)
from src.domain.agents.contracts.query_generation import QueryGenerationContract
from src.domain.agents.ports.query_agent_port import QueryAgentPort


class StubQueryAgent(QueryAgentPort):
    """Stub query agent for testing that captures calls."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self._contract = QueryGenerationContract(
            decision="generated",
            confidence_score=0.9,
            rationale="Test query",
            evidence=[],
            query="MED13[Title/Abstract]",
            source_type="pubmed",
            query_complexity="simple",
        )

    async def generate_query(
        self,
        research_space_description: str,
        user_instructions: str,
        source_type: str,
        *,
        model_id: str | None = None,
        user_id: str | None = None,
        correlation_id: str | None = None,
    ) -> QueryGenerationContract:
        self.calls.append(
            {
                "research_space_description": research_space_description,
                "user_instructions": user_instructions,
                "source_type": source_type,
                "model_id": model_id,
                "user_id": user_id,
                "correlation_id": correlation_id,
            },
        )
        return self._contract

    async def close(self) -> None:
        pass


class TestQueryAgentServiceModelSelection:
    """Tests for model_id passthrough in QueryAgentService."""

    @pytest.fixture
    def stub_agent(self) -> StubQueryAgent:
        """Create a stub query agent."""
        return StubQueryAgent()

    @pytest.fixture
    def service(self, stub_agent: StubQueryAgent) -> QueryAgentService:
        """Create a query agent service with the stub agent."""
        deps = QueryAgentServiceDependencies(
            query_agent=stub_agent,
            research_space_repository=None,
        )
        return QueryAgentService(deps)

    @pytest.mark.asyncio
    async def test_generate_query_passes_model_id(
        self,
        service: QueryAgentService,
        stub_agent: StubQueryAgent,
    ) -> None:
        """Should pass model_id to the underlying agent."""
        await service.generate_query_for_source(
            research_space_description="Test research",
            user_instructions="Find papers",
            source_type="pubmed",
            model_id="openai:gpt-5",
        )

        assert len(stub_agent.calls) == 1
        assert stub_agent.calls[0]["model_id"] == "openai:gpt-5"

    @pytest.mark.asyncio
    async def test_generate_query_none_model_id(
        self,
        service: QueryAgentService,
        stub_agent: StubQueryAgent,
    ) -> None:
        """Should pass None model_id when not specified."""
        await service.generate_query_for_source(
            research_space_description="Test research",
            user_instructions="Find papers",
            source_type="pubmed",
        )

        assert len(stub_agent.calls) == 1
        assert stub_agent.calls[0]["model_id"] is None

    @pytest.mark.asyncio
    async def test_generate_query_for_research_space_passes_model_id(
        self,
        stub_agent: StubQueryAgent,
    ) -> None:
        """Should pass model_id through research space lookup."""
        # Create mock research space repository
        mock_repo = MagicMock()
        space_id = uuid4()
        mock_repo.find_by_id.return_value = MagicMock(description="Test space")

        deps = QueryAgentServiceDependencies(
            query_agent=stub_agent,
            research_space_repository=mock_repo,
        )
        service = QueryAgentService(deps)

        await service.generate_query_for_research_space(
            research_space_id=str(space_id),
            user_instructions="Find papers",
            source_type="pubmed",
            model_id="openai:gpt-5",
        )

        assert len(stub_agent.calls) == 1
        assert stub_agent.calls[0]["model_id"] == "openai:gpt-5"

    @pytest.mark.asyncio
    async def test_generate_queries_for_multiple_sources_passes_model_id(
        self,
        service: QueryAgentService,
        stub_agent: StubQueryAgent,
    ) -> None:
        """Should pass model_id for all source types."""
        await service.generate_queries_for_multiple_sources(
            research_space_description="Test",
            user_instructions="Test",
            source_types=["pubmed", "clinvar"],
            model_id="openai:gpt-5",
        )

        # Should have 2 calls (one per source type)
        assert len(stub_agent.calls) == 2
        # All calls should have the same model_id
        assert all(call["model_id"] == "openai:gpt-5" for call in stub_agent.calls)

    @pytest.mark.asyncio
    async def test_generate_query_passes_all_params(
        self,
        service: QueryAgentService,
        stub_agent: StubQueryAgent,
    ) -> None:
        """Should pass all parameters correctly."""
        await service.generate_query_for_source(
            research_space_description="MED13 research",
            user_instructions="Find recent papers on MED13",
            source_type="pubmed",
            model_id="openai:gpt-4o-mini",
            user_id="user-123",
            correlation_id="corr-456",
        )

        assert len(stub_agent.calls) == 1
        call = stub_agent.calls[0]
        assert call["research_space_description"] == "MED13 research"
        assert call["user_instructions"] == "Find recent papers on MED13"
        assert call["source_type"] == "pubmed"
        assert call["model_id"] == "openai:gpt-4o-mini"
        assert call["user_id"] == "user-123"
        assert call["correlation_id"] == "corr-456"

    @pytest.mark.asyncio
    async def test_close_delegates_to_agent(
        self,
        stub_agent: StubQueryAgent,
    ) -> None:
        """Should call close on the underlying agent."""
        stub_agent.close = AsyncMock()  # type: ignore[method-assign]
        deps = QueryAgentServiceDependencies(
            query_agent=stub_agent,
            research_space_repository=None,
        )
        service = QueryAgentService(deps)

        await service.close()
        stub_agent.close.assert_called_once()
