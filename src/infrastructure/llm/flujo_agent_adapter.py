"""Flujo-based implementation of the AI agent port."""

import logging
import os

from flujo import Flujo, Step
from flujo.agents import make_agent_async
from flujo.domain.models import PipelineContext, PipelineResult, StepResult
from flujo.exceptions import FlujoError
from pydantic import BaseModel, Field

from src.application.services.ports.ai_agent_port import AiAgentPort
from src.infrastructure.llm.flujo_config import resolve_flujo_state_uri

logger = logging.getLogger(__name__)

_INVALID_OPENAI_KEYS = {"test", "changeme", "placeholder"}


class QueryOutput(BaseModel):
    """Structured output for the intelligent query generator."""

    query: str = Field(
        ...,
        description="The generated query string for the data source",
    )


class FlujoAgentAdapter(AiAgentPort):
    """
    Adapter that uses the Flujo framework to implement AI agent capabilities.

    This adapter is designed to be multi-source and scalable. It orchestrates
    source-specific AI agents to transform research context and user instructions
    into high-fidelity search queries for any supported data source.
    """

    def __init__(self, model: str = "openai:gpt-4o-mini") -> None:
        """
        Initialize the Flujo adapter with a registry of source-specific agents.

        Args:
            model: The LLM model identifier to use for the agents
        """
        self._model = model
        os.environ.setdefault("FLUJO_STATE_URI", resolve_flujo_state_uri())
        self._pipelines: dict[str, Flujo[str, QueryOutput, PipelineContext]] = {}

        # Initialize supported sources
        self._setup_pubmed_agent()

    def _setup_pubmed_agent(self) -> None:
        """Configure the agent specifically for PubMed queries."""
        agent = make_agent_async(
            model=self._model,
            system_prompt=(
                "You are an expert biomedical research assistant specializing in "
                "constructing complex, high-fidelity PubMed Boolean queries.\n\n"
                "Your goal is to transform a research space description and "
                "specific user instructions into a valid PubMed query string "
                "that maximizes recall for relevant literature while maintaining "
                "precision.\n\n"
                "Rules:\n"
                "1. Output ONLY a valid PubMed Boolean query string.\n"
                "2. Use [Title/Abstract] or [MeSH Terms] where appropriate.\n"
                "3. Ensure proper nesting of parentheses.\n"
                "4. Incorporate both the research space context and the user's steering instructions."
            ),
            output_type=QueryOutput,
        )

        self._pipelines["pubmed"] = Flujo(
            Step(
                name="generate_pubmed_query",
                agent=agent,
            ),
        )

    async def generate_intelligent_query(
        self,
        research_space_description: str,
        user_instructions: str,
        source_type: str,
    ) -> str:
        """
        Generate an intelligent query for the specified source type.

        This method identifies the appropriate AI agent for the source and
        executes a Flujo workflow to generate a context-aware query.
        """
        source_key = source_type.lower()
        if source_key not in self._pipelines:
            # If the source is not explicitly supported with a specialized agent,
            # we return empty to ensure high-fidelity for supported sources.
            return ""

        if self._model.startswith("openai:") and not self._has_openai_key():
            logger.info(
                "OpenAI API key not configured; skipping AI query generation for %s.",
                source_type,
            )
            return ""

        pipeline = self._pipelines[source_key]

        input_text = (
            f"SOURCE TYPE: {source_type.upper()}\n"
            f"RESEARCH SPACE CONTEXT:\n{research_space_description}\n\n"
            f"USER STEERING INSTRUCTIONS:\n{user_instructions}\n\n"
            f"Generate a high-fidelity search query optimized for {source_type}."
        )

        # Run the Flujo pipeline
        final_output: str | None = None
        try:
            async for item in pipeline.run_async(input_text):
                if isinstance(item, StepResult):
                    candidate = self._coerce_query_output(item.output)
                    if candidate:
                        final_output = candidate
                elif isinstance(item, PipelineResult):
                    candidate = self._extract_pipeline_result_output(item)
                    if candidate:
                        final_output = candidate
        except FlujoError as exc:
            logger.warning(
                "Flujo pipeline failed for %s; returning fallback output. Error: %s",
                source_type,
                exc,
            )
            return final_output or ""

        return final_output or ""

    @staticmethod
    def _has_openai_key() -> bool:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("FLUJO_OPENAI_API_KEY")
        if api_key is None:
            return False
        normalized = api_key.strip()
        if not normalized:
            return False
        return normalized.lower() not in _INVALID_OPENAI_KEYS

    @staticmethod
    def _coerce_query_output(output: object | None) -> str | None:
        if isinstance(output, QueryOutput):
            return output.query
        if isinstance(output, str):
            return output
        return None

    def _extract_pipeline_result_output(
        self,
        result: PipelineResult[PipelineContext],
    ) -> str | None:
        step_history = getattr(result, "step_history", None)
        if not isinstance(step_history, list):
            return None

        for step_result in reversed(step_history):
            if isinstance(step_result, StepResult):
                candidate = self._coerce_query_output(step_result.output)
                if candidate:
                    return candidate
        return None
