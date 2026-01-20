"""
Base pipeline patterns for AI agents.

Provides common governance patterns including confidence-based
routing and human-in-the-loop escalation.

Type Safety Note:
    This module uses `Any` types for Flujo library generic parameters.
    This is a documented exception to the project's strict "Never Any" policy.

    Rationale:
    - Flujo's Step.granular() returns Pipeline[Any, Any] instead of Step
    - Flujo's generic type parameters are not fully compatible with strict typing
    - The Any usage is confined to infrastructure layer only
    - Domain contracts (QueryGenerationContract, etc.) remain fully typed

    The type ignores are:
    - Step.granular() returns Pipeline, not Step (type: ignore[arg-type])
    - Generic parameter constraints in Flujo DSL types
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from flujo import Pipeline, Step
from flujo.domain.dsl import ConditionalStep, HumanInTheLoopStep

from src.infrastructure.llm.config.governance import GovernanceConfig

if TYPE_CHECKING:
    from collections.abc import Callable


def check_confidence(
    output: object,
    _ctx: object,
    threshold: float = 0.85,
) -> str:
    """
    Check if output confidence meets the threshold for auto-approval.

    Args:
        output: Agent output with confidence_score
        _ctx: Pipeline context (unused)
        threshold: Minimum confidence for auto-approval

    Returns:
        "proceed" if confidence is sufficient, "escalate" otherwise
    """
    if not hasattr(output, "confidence_score"):
        return "escalate"
    confidence = getattr(output, "confidence_score", 0.0)
    return "proceed" if confidence >= threshold else "escalate"


def create_confidence_checker(
    threshold: float,
) -> Callable[[object, object], str]:
    """
    Create a confidence checker with a specific threshold.

    Args:
        threshold: Minimum confidence for auto-approval

    Returns:
        Callable for use with ConditionalStep
    """

    def _check(output: object, ctx: object) -> str:
        return check_confidence(output, ctx, threshold)

    return _check


def create_governance_gate(
    name: str,
    governance_config: GovernanceConfig | None = None,
    escalation_message: str = "Low confidence decision. Review required.",
) -> ConditionalStep[Any]:
    """
    Create a standard governance gate for confidence-based routing.

    Args:
        name: Name for the governance step
        governance_config: Optional governance configuration
        escalation_message: Message shown when escalating to human review

    Returns:
        ConditionalStep configured for confidence-based routing
    """
    config = governance_config or GovernanceConfig.from_environment()
    threshold = config.confidence_threshold

    return ConditionalStep(
        name=name,
        condition_callable=create_confidence_checker(threshold),
        branches={
            "escalate": Pipeline(
                steps=[
                    HumanInTheLoopStep(
                        name=f"{name}_human_review",
                        message_for_user=escalation_message,
                    ),
                ],
            ),
            "proceed": Pipeline(steps=[]),
        },
    )


class PipelineBuilder:
    """
    Builder for creating pipelines with standard governance patterns.

    Provides a fluent interface for constructing pipelines with
    consistent governance and durability settings.
    """

    def __init__(
        self,
        name: str,
        governance_config: GovernanceConfig | None = None,
    ) -> None:
        """
        Initialize the pipeline builder.

        Args:
            name: Name for the pipeline
            governance_config: Optional governance configuration
        """
        self._name = name
        self._governance = governance_config or GovernanceConfig.from_environment()
        self._steps: list[Step[Any, Any] | ConditionalStep[Any]] = []
        self._use_granular: bool = True
        self._enforce_idempotency: bool = True

    def with_agent_step(
        self,
        step_name: str,
        agent: object,
        *,
        granular: bool = True,
        idempotent: bool = True,
    ) -> PipelineBuilder:
        """
        Add an agent step to the pipeline.

        Args:
            step_name: Name for the step
            agent: The agent to execute
            granular: Use granular durability
            idempotent: Enforce idempotency

        Returns:
            Self for chaining
        """
        if granular:
            # Step.granular returns a Pipeline wrapping a GranularStep
            self._steps.append(
                Step.granular(  # type: ignore[arg-type]
                    name=step_name,
                    agent=agent,
                    enforce_idempotency=idempotent,
                ),
            )
        else:
            self._steps.append(
                Step(
                    name=step_name,
                    agent=agent,
                ),
            )
        return self

    def with_governance_gate(
        self,
        escalation_message: str = "Low confidence. Review required.",
    ) -> PipelineBuilder:
        """
        Add a governance gate for confidence-based routing.

        Args:
            escalation_message: Message for human review

        Returns:
            Self for chaining
        """
        gate = create_governance_gate(
            name=f"{self._name}_governance",
            governance_config=self._governance,
            escalation_message=escalation_message,
        )
        self._steps.append(gate)
        return self

    def build(self) -> Pipeline[Any, Any]:
        """
        Build the pipeline.

        Returns:
            Configured Pipeline instance
        """
        return Pipeline(steps=self._steps)
