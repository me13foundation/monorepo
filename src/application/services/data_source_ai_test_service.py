"""
Application service for testing AI-managed data source configurations.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.domain.entities.data_source_configs import PubMedQueryConfig
from src.domain.entities.user_data_source import SourceType
from src.type_definitions.data_sources import (
    DataSourceAiTestFinding,
    DataSourceAiTestLink,
    DataSourceAiTestResult,
)

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
    from src.type_definitions.common import RawRecord, SourceMetadata


class DataSourceAiTestSettings(BaseModel):
    """Settings for AI data source test execution."""

    model_config = ConfigDict(extra="forbid")

    sample_size: int = Field(default=5, ge=1)
    ai_model_name: str | None = None


class DataSourceAiTestService:
    """Coordinate AI configuration testing for supported data sources."""

    def __init__(
        self,
        *,
        source_repository: UserDataSourceRepository,
        pubmed_gateway: PubMedGateway,
        ai_agent: AiAgentPort | None,
        research_space_repository: ResearchSpaceRepository | None,
        settings: DataSourceAiTestSettings | None = None,
    ) -> None:
        self._source_repository = source_repository
        self._pubmed_gateway = pubmed_gateway
        self._ai_agent = ai_agent
        self._research_space_repository = research_space_repository
        resolved_settings = settings or DataSourceAiTestSettings()
        self._sample_size = max(resolved_settings.sample_size, 1)
        self._ai_model_name = resolved_settings.ai_model_name

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
        findings: list[DataSourceAiTestFinding] = []

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
                        "relevance_threshold": 0,
                    },
                )
                try:
                    raw_records = await self._pubmed_gateway.fetch_records(test_config)
                    fetched_records = len(raw_records)
                    findings = self._build_findings(raw_records)
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

        search_terms = self._extract_search_terms(executed_query)
        model_name = self._resolve_model_name(
            has_ai_agent=self._ai_agent is not None,
        )

        return DataSourceAiTestResult(
            source_id=source.id,
            model=model_name,
            success=success,
            message=message,
            executed_query=executed_query,
            search_terms=search_terms,
            fetched_records=fetched_records,
            sample_size=self._sample_size,
            findings=findings,
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

    def _resolve_model_name(self, *, has_ai_agent: bool) -> str | None:
        if not has_ai_agent:
            return None
        model = self._ai_model_name
        return model.strip() if isinstance(model, str) and model.strip() else None

    @staticmethod
    def _extract_search_terms(query: str | None) -> list[str]:
        if not query:
            return []

        terms: list[str] = []
        quoted_terms = re.findall(r'"([^"]+)"', query)
        for term in quoted_terms:
            normalized = term.strip()
            if normalized and normalized not in terms:
                terms.append(normalized)

        scrubbed = re.sub(r'"[^"]+"', " ", query)
        scrubbed = re.sub(r"\[[^\]]+\]", " ", scrubbed)
        scrubbed = scrubbed.replace("(", " ").replace(")", " ")
        for token in scrubbed.split():
            normalized = token.strip()
            if not normalized:
                continue
            if normalized.upper() in {"AND", "OR", "NOT"}:
                continue
            if normalized not in terms:
                terms.append(normalized)

        return terms

    def _build_findings(
        self,
        records: list[RawRecord],
    ) -> list[DataSourceAiTestFinding]:
        findings: list[DataSourceAiTestFinding] = []
        for record in records[: self._sample_size]:
            pubmed_id = self._coerce_scalar(record.get("pubmed_id"))
            title = self._coerce_scalar(record.get("title")) or "Untitled PubMed record"
            doi = self._coerce_scalar(record.get("doi"))
            pmc_id = self._coerce_scalar(record.get("pmc_id"))
            publication_date = self._coerce_scalar(record.get("publication_date"))
            journal = self._extract_journal_title(record.get("journal"))
            links = self._build_links(pubmed_id, pmc_id, doi)

            findings.append(
                DataSourceAiTestFinding(
                    title=title,
                    pubmed_id=pubmed_id,
                    doi=doi,
                    pmc_id=pmc_id,
                    publication_date=publication_date,
                    journal=journal,
                    links=links,
                ),
            )
        return findings

    @staticmethod
    def _coerce_scalar(value: object | None) -> str | None:
        if isinstance(value, str):
            return value.strip() or None
        if isinstance(value, int | float):
            return str(value)
        return None

    @staticmethod
    def _extract_journal_title(value: object | None) -> str | None:
        if not isinstance(value, dict):
            return None
        title_value = value.get("title")
        return (
            title_value.strip()
            if isinstance(title_value, str) and title_value.strip()
            else None
        )

    @staticmethod
    def _build_links(
        pubmed_id: str | None,
        pmc_id: str | None,
        doi: str | None,
    ) -> list[DataSourceAiTestLink]:
        links: list[DataSourceAiTestLink] = []
        if pubmed_id:
            links.append(
                DataSourceAiTestLink(
                    label="PubMed",
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/",
                ),
            )
        if pmc_id:
            links.append(
                DataSourceAiTestLink(
                    label="PubMed Central",
                    url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/",
                ),
            )
        if doi:
            links.append(
                DataSourceAiTestLink(
                    label="DOI",
                    url=f"https://doi.org/{doi}",
                ),
            )
        return links


__all__ = ["DataSourceAiTestService", "DataSourceAiTestSettings"]
