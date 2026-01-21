"""
Flujo-based implementation of the query agent port.

Implements the QueryAgentPort using Flujo pipelines with
evidence-first contracts and governance patterns.

Type Safety Note:
    This module uses `Any` types for Flujo runner generic parameters.
    This is a documented exception to the project's strict "Never Any" policy.

    Rationale:
    - Flujo[InputT, OutputT, ContextT] requires concrete types at runtime
    - The pipeline's actual types are QueryGenerationContract, QueryGenerationContext
    - Internal dict storage uses Flujo[Any, Any, Any] for flexibility
    - All public API methods return fully-typed domain contracts

    The domain boundary (QueryAgentPort) remains strictly typed with no Any.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from flujo.domain.models import PipelineResult, StepResult
from flujo.exceptions import FlujoError, PausedException, PipelineAbortSignal

from src.domain.agents.contracts.query_generation import QueryGenerationContract
from src.domain.agents.ports.query_agent_port import (
    QueryAgentPort,
    QueryAgentRunMetadataProvider,
)
from src.infrastructure.llm.config.governance import GovernanceConfig
from src.infrastructure.llm.pipelines.query_pipelines.pubmed_pipeline import (
    create_pubmed_query_pipeline,
)
from src.infrastructure.llm.state.backend_manager import get_state_backend
from src.infrastructure.llm.state.lifecycle import get_lifecycle_manager

if TYPE_CHECKING:
    from typing import Any

    from flujo import Flujo

    from src.domain.agents.contexts.query_context import QueryGenerationContext

logger = logging.getLogger(__name__)

_INVALID_OPENAI_KEYS = frozenset({"test", "changeme", "placeholder"})


class FlujoQueryAgentAdapter(QueryAgentPort, QueryAgentRunMetadataProvider):
    """
    Adapter that uses Flujo framework for query generation.

    Implements the QueryAgentPort interface using Flujo pipelines
    with evidence-first contracts, confidence-based governance,
    and proper lifecycle management.
    """

    def __init__(
        self,
        model: str | None = None,
        *,
        use_governance: bool = True,
        use_granular: bool = False,
    ) -> None:
        """
        Initialize the Flujo query agent adapter.

        Args:
            model: Optional model ID override
            use_governance: Enable confidence-based governance
            use_granular: Use granular steps for multi-turn durability (default False)
                          Query generation is single-turn, so granular is not needed.
        """
        self._model = model
        self._use_governance = use_governance
        self._use_granular = use_granular
        self._state_backend = get_state_backend()
        self._pipelines: dict[str, Flujo[Any, Any, Any]] = {}
        self._last_run_id: str | None = None
        self._governance = GovernanceConfig.from_environment()
        self._lifecycle_manager = get_lifecycle_manager()

        # Initialize supported source pipelines
        self._setup_pipelines()

    def _setup_pipelines(self) -> None:
        """Initialize pipelines for supported data sources."""
        # PubMed pipeline
        pubmed_pipeline = create_pubmed_query_pipeline(
            state_backend=self._state_backend,
            model=self._model,
            use_governance=self._use_governance,
            use_granular=self._use_granular,
        )
        self._pipelines["pubmed"] = pubmed_pipeline
        self._lifecycle_manager.register_runner(pubmed_pipeline)

    async def generate_query(
        self,
        research_space_description: str,
        user_instructions: str,
        source_type: str,
        *,
        user_id: str | None = None,
        correlation_id: str | None = None,
    ) -> QueryGenerationContract:
        """
        Generate an intelligent query for the specified source type.

        Args:
            research_space_description: Description of the research space context
            user_instructions: User-provided prompting to steer the agent
            source_type: The type of data source (e.g., "pubmed", "clinvar")
            user_id: Optional user ID for audit attribution
            correlation_id: Optional correlation ID for distributed tracing

        Returns:
            QueryGenerationContract with the generated query and metadata
        """
        self._last_run_id = None
        source_key = source_type.lower()

        # Check for supported source
        if source_key not in self._pipelines:
            logger.warning(
                "Unsupported source type: %s. Returning escalation contract.",
                source_type,
            )
            return self._create_unsupported_source_contract(source_type)

        # Check for OpenAI key if using OpenAI model
        if self._is_openai_model() and not self._has_openai_key():
            logger.info(
                "OpenAI API key not configured; returning fallback contract for %s.",
                source_type,
            )
            return self._create_no_api_key_contract(source_type)

        pipeline = self._pipelines[source_key]

        # Build input text
        input_text = self._build_input_text(
            research_space_description,
            user_instructions,
            source_type,
        )

        # Build initial context
        initial_context = {
            "user_id": user_id,
            "correlation_id": correlation_id,
            "source_type": source_type,
            "research_space_description": research_space_description,
            "user_instructions": user_instructions,
            "request_source": "api",
        }

        # Execute pipeline with proper exception handling
        try:
            return await self._execute_pipeline(
                pipeline,
                input_text,
                initial_context,
            )
        except (PausedException, PipelineAbortSignal):
            # Allow pause/abort signals to bubble up for HITL handling
            raise
        except FlujoError as exc:
            logger.warning(
                "Flujo pipeline failed for %s; returning fallback contract. Error: %s",
                source_type,
                exc,
            )
            return self._create_error_contract(source_type, str(exc))

    async def _execute_pipeline(
        self,
        pipeline: Flujo[Any, Any, Any],
        input_text: str,
        initial_context: dict[str, str | None],
    ) -> QueryGenerationContract:
        """
        Execute the pipeline and extract the result.

        Args:
            pipeline: The Flujo pipeline to execute
            input_text: Input text for the agent
            initial_context: Initial context data

        Returns:
            QueryGenerationContract from the pipeline output
        """
        final_output: QueryGenerationContract | None = None

        async for item in pipeline.run_async(
            input_text,
            initial_context_data=initial_context,
        ):
            if isinstance(item, StepResult):
                candidate = self._extract_contract(item.output)
                if candidate:
                    final_output = candidate
            elif isinstance(item, PipelineResult):
                self._capture_run_id(item)
                candidate = self._extract_from_pipeline_result(item)
                if candidate:
                    final_output = candidate

        if final_output is None:
            logger.warning("Pipeline completed without producing a valid contract")
            return self._create_empty_result_contract(
                initial_context.get("source_type") or "unknown",
            )

        return final_output

    async def close(self) -> None:
        """
        Clean up resources and drain connection pools.

        Should be called during application shutdown.
        """
        for source_type, pipeline in self._pipelines.items():
            try:
                if hasattr(pipeline, "aclose"):
                    await pipeline.aclose()
                self._lifecycle_manager.unregister_runner(pipeline)
            except (RuntimeError, OSError, ConnectionError) as exc:
                logger.warning(
                    "Error closing pipeline for %s: %s",
                    source_type,
                    exc,
                )

        self._pipelines.clear()

    def get_last_run_id(self) -> str | None:
        """Return the most recently executed Flujo run id."""
        return self._last_run_id

    # --- Private helper methods ---

    def _is_openai_model(self) -> bool:
        """Check if the configured model is an OpenAI model."""
        if self._model:
            return self._model.startswith("openai:")
        return True  # Default model is OpenAI

    @staticmethod
    def _has_openai_key() -> bool:
        """Check if a valid OpenAI API key is configured."""
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("FLUJO_OPENAI_API_KEY")
        if api_key is None:
            return False
        normalized = api_key.strip()
        if not normalized:
            return False
        return normalized.lower() not in _INVALID_OPENAI_KEYS

    @staticmethod
    def _build_input_text(
        research_space_description: str,
        user_instructions: str,
        source_type: str,
    ) -> str:
        """Build the input text for the agent."""
        return (
            f"SOURCE TYPE: {source_type.upper()}\n"
            f"RESEARCH SPACE CONTEXT:\n{research_space_description}\n\n"
            f"USER STEERING INSTRUCTIONS:\n{user_instructions}\n\n"
            f"Generate a high-fidelity search query optimized for {source_type}."
        )

    @staticmethod
    def _extract_contract(output: object) -> QueryGenerationContract | None:
        """Extract a contract from step output."""
        if isinstance(output, QueryGenerationContract):
            return output
        return None

    def _extract_from_pipeline_result(
        self,
        result: PipelineResult[QueryGenerationContext],
    ) -> QueryGenerationContract | None:
        """Extract contract from pipeline result's step history."""
        step_history = getattr(result, "step_history", None)
        if not isinstance(step_history, list):
            return None

        for step_result in reversed(step_history):
            if isinstance(step_result, StepResult):
                candidate = self._extract_contract(step_result.output)
                if candidate:
                    return candidate
        return None

    def _capture_run_id(
        self,
        result: PipelineResult[QueryGenerationContext],
    ) -> None:
        """Capture the run ID from the pipeline result."""
        context: object = result.final_pipeline_context
        if context is None:
            return

        # Try to get run_id from context object
        run_id = getattr(context, "run_id", None)
        if isinstance(run_id, str) and run_id.strip():
            self._last_run_id = run_id.strip()
            return

        # Fallback: try dict-like access
        if hasattr(context, "get"):
            get_method = context.get
            run_id_val = get_method("run_id")
            if isinstance(run_id_val, str) and run_id_val.strip():
                self._last_run_id = run_id_val.strip()

    # --- Contract factory methods ---

    @staticmethod
    def _create_unsupported_source_contract(
        source_type: str,
    ) -> QueryGenerationContract:
        """Create a contract for unsupported source types."""
        return QueryGenerationContract(
            decision="escalate",
            confidence_score=0.0,
            rationale=f"Source type '{source_type}' is not yet supported.",
            evidence=[],
            query="",
            source_type=source_type,
            query_complexity="simple",
        )

    @staticmethod
    def _create_no_api_key_contract(source_type: str) -> QueryGenerationContract:
        """Create a contract when API key is missing."""
        return QueryGenerationContract(
            decision="fallback",
            confidence_score=0.0,
            rationale="OpenAI API key not configured. Cannot generate intelligent query.",
            evidence=[],
            query="",
            source_type=source_type,
            query_complexity="simple",
        )

    @staticmethod
    def _create_error_contract(source_type: str, error: str) -> QueryGenerationContract:
        """Create a contract for pipeline errors."""
        return QueryGenerationContract(
            decision="escalate",
            confidence_score=0.0,
            rationale=f"Pipeline execution failed: {error}",
            evidence=[],
            query="",
            source_type=source_type,
            query_complexity="simple",
        )

    @staticmethod
    def _create_empty_result_contract(source_type: str) -> QueryGenerationContract:
        """Create a contract when pipeline produces no output."""
        return QueryGenerationContract(
            decision="escalate",
            confidence_score=0.0,
            rationale="Pipeline completed without producing a valid query.",
            evidence=[],
            query="",
            source_type=source_type,
            query_complexity="simple",
        )
