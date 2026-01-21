"""
Base factory patterns for AI agent creation.

Provides common patterns and protocols for agent factories
following the Factory Pattern recommended by Flujo.

Type Safety Note:
    Flujo's make_agent_async() returns AsyncAgentWrapper[Any, Any] internally.
    This is a fundamental limitation of the Flujo library's type system.

    We define FlujoAgent as a type alias to document this clearly rather than
    scattering bare 'Any' throughout the codebase. The actual output types
    are enforced at the contract level (QueryGenerationContract, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from src.domain.agents.models import ModelCapability, ModelSpec
from src.infrastructure.llm.config.model_registry import get_model_registry

OutputT = TypeVar("OutputT", bound=BaseModel)

# Type alias for Flujo agent instances.
# Flujo's make_agent_async returns AsyncAgentWrapper[Any, Any] internally.
# We use 'object' as the base type to avoid explicit 'Any' while acknowledging
# we can't fully type Flujo's internal agent wrapper.
FlujoAgent = object


def _get_default_model_id() -> str:
    """Get the default model ID from registry."""
    registry = get_model_registry()
    return registry.get_default_model(ModelCapability.QUERY_GENERATION).model_id


class BaseAgentFactory(ABC, Generic[OutputT]):
    """
    Base class for agent factories.

    Provides common functionality for creating agents with
    consistent configuration and error handling.
    """

    def __init__(
        self,
        default_model: str | None = None,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize the factory.

        Args:
            default_model: Default model ID to use (loads from registry if None)
            max_retries: Default retry count for agent calls
        """
        self._default_model = default_model or _get_default_model_id()
        self._max_retries = max_retries

    @property
    @abstractmethod
    def output_type(self) -> type[OutputT]:
        """Return the output type for this factory's agents."""

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this factory's agents."""

    def create(self, model: str | None = None) -> FlujoAgent:
        """
        Create an agent instance.

        Args:
            model: Optional model ID override

        Returns:
            Configured Flujo agent (AsyncAgentWrapper with OutputT contract)
        """
        from flujo.agents import make_agent_async

        model_id = model or self._default_model
        registry = get_model_registry()

        # Check if it's a reasoning model that needs special settings
        try:
            model_spec = registry.get_model(model_id)
            reasoning_settings = model_spec.get_reasoning_settings()

            if reasoning_settings:
                return make_agent_async(
                    model=model_id,
                    system_prompt=self.get_system_prompt(),
                    output_type=self.output_type,
                    max_retries=model_spec.max_retries,
                    timeout=int(model_spec.timeout_seconds),
                    model_settings=reasoning_settings,
                )
        except KeyError:
            # Model not in registry, use defaults
            pass

        return make_agent_async(
            model=model_id,
            system_prompt=self.get_system_prompt(),
            output_type=self.output_type,
            max_retries=self._max_retries,
        )

    def create_with_spec(self, spec: ModelSpec) -> FlujoAgent:
        """
        Create an agent using a ModelSpec.

        Args:
            spec: Model specification with all settings

        Returns:
            Configured Flujo agent (AsyncAgentWrapper with OutputT contract)
        """
        from flujo.agents import make_agent_async

        reasoning_settings = spec.get_reasoning_settings()

        if reasoning_settings:
            return make_agent_async(
                model=spec.model_id,
                system_prompt=self.get_system_prompt(),
                output_type=self.output_type,
                max_retries=spec.max_retries,
                timeout=int(spec.timeout_seconds),
                model_settings=reasoning_settings,
            )

        return make_agent_async(
            model=spec.model_id,
            system_prompt=self.get_system_prompt(),
            output_type=self.output_type,
            max_retries=spec.max_retries,
        )
