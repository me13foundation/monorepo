"""
PubMed query generation pipeline.

Creates a pipeline for generating PubMed Boolean queries with
governance patterns for confidence-based routing.

Type Safety Note:
    This module uses `Any` types for Flujo Step/ConditionalStep generics.
    See base_pipeline.py for the rationale on this documented exception.

    The return type Flujo[str, QueryGenerationContract, QueryGenerationContext]
    is fully typed - only internal step lists use Any for Flujo compatibility.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from flujo import Flujo, Pipeline, Step
from flujo.domain.dsl import ConditionalStep, HumanInTheLoopStep

from src.domain.agents.contexts.query_context import QueryGenerationContext
from src.infrastructure.llm.config.governance import GovernanceConfig
from src.infrastructure.llm.factories.query_agent_factory import (
    create_pubmed_query_agent,
)

if TYPE_CHECKING:
    from flujo.state.backends.base import StateBackend

    from src.domain.agents.contracts.query_generation import QueryGenerationContract


def _check_query_confidence(
    output: object,
    _ctx: object,
) -> str:
    """
    Check query generation confidence for routing.

    Routes to human review if:
    - Confidence is below threshold
    - Decision is "escalate"
    - Decision is "fallback" with low confidence
    """
    governance = GovernanceConfig.from_environment()
    threshold = governance.confidence_threshold

    # Get attributes safely for type checker
    decision = getattr(output, "decision", None)
    confidence_score = getattr(output, "confidence_score", 0.0)

    # Explicit escalation decision
    if decision == "escalate":
        return "escalate"

    # Fallback with low confidence should escalate
    if decision == "fallback" and confidence_score < threshold:
        return "escalate"

    # Normal confidence check
    return "proceed" if confidence_score >= threshold else "escalate"


def create_pubmed_query_pipeline(
    state_backend: StateBackend,
    *,
    model: str | None = None,
    use_governance: bool = True,
    use_granular: bool = True,
) -> Flujo[str, QueryGenerationContract, QueryGenerationContext]:
    """
    Create the PubMed query generation pipeline.

    Args:
        state_backend: Flujo state backend for persistence
        model: Optional model ID override
        use_governance: Include confidence-based governance gate
        use_granular: Use granular step for per-turn durability

    Returns:
        Configured Flujo runner for PubMed query generation
    """
    agent = create_pubmed_query_agent(model=model)

    # Build pipeline steps
    steps: list[Step[Any, Any] | ConditionalStep[Any]] = []

    # Create the main agent step
    if use_granular:
        # Step.granular returns a Pipeline wrapping a GranularStep
        steps.append(
            Step.granular(  # type: ignore[arg-type]
                name="generate_pubmed_query",
                agent=agent,
                enforce_idempotency=True,
            ),
        )
    else:
        steps.append(
            Step(
                name="generate_pubmed_query",
                agent=agent,
            ),
        )

    if use_governance:
        governance_gate: ConditionalStep[Any] = ConditionalStep(
            name="query_confidence_gate",
            condition_callable=_check_query_confidence,
            branches={
                "escalate": Pipeline(
                    steps=[
                        HumanInTheLoopStep(
                            name="query_human_review",
                            message_for_user=(
                                "Query generation confidence is below threshold. "
                                "Please review the generated query before use."
                            ),
                        ),
                    ],
                ),
                "proceed": Pipeline(steps=[]),
            },
        )
        steps.append(governance_gate)

    return Flujo(
        Pipeline(steps=steps),
        context_model=QueryGenerationContext,
        state_backend=state_backend,
        persist_state=True,
    )
