"""
Context for query generation agent pipelines.

Provides typed context for query generation workflows including
research space context and source-specific metadata.
"""

from pydantic import Field

from src.domain.agents.contexts.base import BaseAgentContext


class QueryGenerationContext(BaseAgentContext):
    """
    Context for query generation agent pipelines.

    Extends BaseAgentContext with fields specific to query generation
    workflows, including research space context and source targeting.
    """

    research_space_id: str | None = Field(
        default=None,
        description="ID of the research space this query is for",
    )
    research_space_description: str | None = Field(
        default=None,
        description="Description of the research space context",
    )
    source_type: str = Field(
        default="unknown",
        description="Target data source type (pubmed, clinvar, etc.)",
    )
    user_instructions: str | None = Field(
        default=None,
        description="User-provided instructions for query steering",
    )
    previous_queries: list[str] = Field(
        default_factory=list,
        description="Previously generated queries for refinement context",
    )
