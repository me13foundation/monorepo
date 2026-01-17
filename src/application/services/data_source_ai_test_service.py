"""
Application service for testing AI-managed data source configurations.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import ValidationError

from src.domain.entities.data_source_configs import PubMedQueryConfig
from src.domain.entities.user_data_source import SourceType
from src.type_definitions.data_sources import DataSourceAiTestResult

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from uuid import UUID

    from src.application.services.ports.ai_agent_port import AiAgentPort
    from src.domain.entities.user_data_source import UserDataSource
    from src.domain.repositories.research_space_repository import (
        ResearchSpaceRepository,
    )
    from src.domain.repositories.user_data_source_repository import (
        UserDataSourceRepository,
    )
    from src.domain.services.pubmed_ingestion import PubMedGateway
    from src.type_definitions.common import SourceMetadata


class DataSourceAiTestService:
    """Coordinate AI configuration testing for supported data sources."""

    def __init__(
        self,
        *,
        source_repository: UserDataSourceRepository,
        pubmed_gateway: PubMedGateway,
        ai_agent: AiAgentPort | None,
        research_space_repository: ResearchSpaceRepository | None,
        sample_size: int = 5,
    ) -> None:
        self._source_repository = source_repository
        self._pubmed_gateway = pubmed_gateway
        self._ai_agent = ai_agent
        self._research_space_repository = research_space_repository
        self._sample_size = max(sample_size, 1)

    async def test_ai_configuration(
        self,
        source_id: UUID,
    ) -> DataSourceAiTestResult:
        """Run a lightweight AI-driven test against a data source configuration."""
        source = self._require_source(source_id)
        checked_at = datetime.now(UTC)
        config = self._build_pubmed_config(source)
        error_message = self._validate_preconditions(source=source, config=config)
        executed_query: str | None = None
        fetched_records = 0

        if error_message is None and config is not None:
            research_space_description = self._resolve_research_space_description(
                source,
                config,
            )
            intelligent_query = await self._generate_intelligent_query(
                research_space_description,
                config.agent_config.agent_prompt,
            )

            if not intelligent_query:
                error_message = "AI agent did not return a query. Refine the AI instructions and try again."
            else:
                executed_query = intelligent_query
                test_config = config.model_copy(
                    update={
                        "query": intelligent_query,
                        "max_results": self._sample_size,
                    },
                )
                try:
                    raw_records = await self._pubmed_gateway.fetch_records(test_config)
                    fetched_records = len(raw_records)
                    if fetched_records == 0:
                        error_message = (
                            "PubMed returned no results for the AI-generated query. "
                            "Adjust the prompt or filters and try again."
                        )
                except Exception as exc:  # pragma: no cover - defensive
                    logger.exception("AI test failed for source %s", source.id)
                    error_message = f"PubMed request failed: {exc!s}"

        success = error_message is None
        if error_message is None:
            message = f"AI test succeeded with {fetched_records} record(s) returned."
        else:
            message = error_message

        return DataSourceAiTestResult(
            source_id=source.id,
            success=success,
            message=message,
            executed_query=executed_query,
            fetched_records=fetched_records,
            sample_size=self._sample_size,
            checked_at=checked_at,
        )

    def _require_source(self, source_id: UUID) -> UserDataSource:
        source = self._source_repository.find_by_id(source_id)
        if source is None:
            msg = f"Data source {source_id} not found"
            raise ValueError(msg)
        return source

    @staticmethod
    def _build_pubmed_config(
        source: UserDataSource,
    ) -> PubMedQueryConfig | None:
        metadata: SourceMetadata = dict(source.configuration.metadata or {})
        try:
            return PubMedQueryConfig.model_validate(metadata)
        except ValidationError as exc:
            logger.warning("Invalid PubMed config for source %s: %s", source.id, exc)
            return None

    def _validate_preconditions(
        self,
        *,
        source: UserDataSource,
        config: PubMedQueryConfig | None,
    ) -> str | None:
        if source.source_type != SourceType.PUBMED:
            return "AI testing is only supported for PubMed sources."
        if config is None:
            return "PubMed configuration is invalid. Review the source settings."
        if not config.agent_config.is_ai_managed:
            return "AI-managed queries are disabled for this source."
        if self._ai_agent is None:
            return "AI agent is not configured for testing."
        if self._research_space_repository is None:
            return "Research space context is unavailable for AI testing."
        return None

    def _resolve_research_space_description(
        self,
        source: UserDataSource,
        config: PubMedQueryConfig,
    ) -> str:
        if not config.agent_config.use_research_space_context:
            return ""
        if source.research_space_id is None:
            return ""
        repository = self._research_space_repository
        if repository is None:
            return ""
        space = repository.find_by_id(source.research_space_id)
        return space.description if space else ""

    async def _generate_intelligent_query(
        self,
        research_space_description: str,
        agent_prompt: str,
    ) -> str:
        if self._ai_agent is None:
            return ""
        try:
            query = await self._ai_agent.generate_intelligent_query(
                research_space_description=research_space_description,
                user_instructions=agent_prompt,
                source_type="pubmed",
            )
        except Exception:  # pragma: no cover - defensive
            logger.exception("AI query generation failed")
            return ""

        return query.strip()


__all__ = ["DataSourceAiTestService"]
