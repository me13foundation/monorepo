"""Port interface for AI agent operations."""

from abc import ABC, abstractmethod


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
