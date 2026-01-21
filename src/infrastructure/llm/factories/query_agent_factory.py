"""
Factory for query generation agents.

Creates agents optimized for generating search queries
for various data sources (PubMed, ClinVar, etc.).
"""

from __future__ import annotations

from flujo.agents import make_agent_async

from src.domain.agents.contracts.query_generation import QueryGenerationContract
from src.domain.agents.models import ModelCapability
from src.infrastructure.llm.config.model_registry import get_model_registry
from src.infrastructure.llm.factories.base_factory import BaseAgentFactory, FlujoAgent
from src.infrastructure.llm.prompts.query.pubmed import PUBMED_QUERY_SYSTEM_PROMPT


def create_pubmed_query_agent(
    model: str | None = None,
    max_retries: int = 3,
) -> FlujoAgent:
    """
    Factory function for PubMed query generation agent.

    Creates an agent optimized for generating PubMed Boolean queries
    with evidence-first output schema.

    Args:
        model: Optional model ID override (defaults to registry default)
        max_retries: Number of retries for failed calls

    Returns:
        Configured agent for PubMed query generation
    """
    registry = get_model_registry()

    if model:
        try:
            model_spec = registry.get_model(model)
        except KeyError:
            # Model not in registry, use default
            model_spec = registry.get_default_model(ModelCapability.QUERY_GENERATION)
    else:
        model_spec = registry.get_default_model(ModelCapability.QUERY_GENERATION)

    # Handle reasoning models with special settings
    reasoning_settings = model_spec.get_reasoning_settings()

    if reasoning_settings:
        return make_agent_async(
            model=model_spec.model_id,
            system_prompt=PUBMED_QUERY_SYSTEM_PROMPT,
            output_type=QueryGenerationContract,
            max_retries=model_spec.max_retries,
            timeout=int(model_spec.timeout_seconds),
            model_settings=reasoning_settings,
        )

    return make_agent_async(
        model=model_spec.model_id,
        system_prompt=PUBMED_QUERY_SYSTEM_PROMPT,
        output_type=QueryGenerationContract,
        max_retries=max_retries,
    )


class QueryAgentFactory(BaseAgentFactory[QueryGenerationContract]):
    """
    Factory for query generation agents.

    Provides class-based factory pattern for creating query agents
    with configurable source-specific prompts.
    """

    def __init__(
        self,
        source_type: str = "pubmed",
        model: str | None = None,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize the query agent factory.

        Args:
            source_type: Data source type (pubmed, clinvar, etc.)
            model: Default model ID to use (loads from registry if None)
            max_retries: Default retry count for agent calls
        """
        super().__init__(
            default_model=model,  # Base class handles registry lookup
            max_retries=max_retries,
        )
        self._source_type = source_type
        self._prompts = {
            "pubmed": PUBMED_QUERY_SYSTEM_PROMPT,
            # Add more source-specific prompts here
        }

    @property
    def output_type(self) -> type[QueryGenerationContract]:
        """Return the output type for query agents."""
        return QueryGenerationContract

    def get_system_prompt(self) -> str:
        """Return the system prompt for the configured source type."""
        return self._prompts.get(
            self._source_type.lower(),
            self._prompts["pubmed"],  # Default to PubMed
        )

    @classmethod
    def for_pubmed(cls, model: str | None = None) -> QueryAgentFactory:
        """Create a factory for PubMed query agents."""
        return cls(source_type="pubmed", model=model)

    @classmethod
    def for_source(
        cls,
        source_type: str,
        model: str | None = None,
    ) -> QueryAgentFactory:
        """Create a factory for a specific source type."""
        return cls(source_type=source_type, model=model)
