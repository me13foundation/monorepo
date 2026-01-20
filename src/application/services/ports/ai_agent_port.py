"""Port interface for AI agent operations."""

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable


class AiAgentPort(ABC):
    """
    Port interface for AI agent operations.

    Defines how the application layer interacts with AI agents
    for intelligent query generation and other agentic tasks.
    """

    @abstractmethod
    async def generate_intelligent_query(
        self,
        research_space_description: str,
        user_instructions: str,
        source_type: str,
    ) -> str:
        """
        Generate an intelligent query string for a specific data source.

        Args:
            research_space_description: Description of the research space context
            user_instructions: User-provided prompting to steer the agent
            source_type: The type of data source (e.g., "pubmed")

        Returns:
            A generated query string compatible with the source type
        """


@runtime_checkable
class AiAgentRunMetadataProvider(Protocol):
    """Optional protocol for AI agents that expose their last Flujo run id."""

    def get_last_run_id(self) -> str | None:
        """Return the most recently executed Flujo run id, if available."""
        ...
