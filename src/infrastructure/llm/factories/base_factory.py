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
from typing import TYPE_CHECKING, Generic, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from src.infrastructure.llm.config.model_registry import ModelConfig

OutputT = TypeVar("OutputT", bound=BaseModel)

# Type alias for Flujo agent instances.
# Flujo's make_agent_async returns AsyncAgentWrapper[Any, Any] internally.
# We use 'object' as the base type to avoid explicit 'Any' while acknowledging
# we can't fully type Flujo's internal agent wrapper.
FlujoAgent = object


class BaseAgentFactory(ABC, Generic[OutputT]):
    """
    Base class for agent factories.

    Provides common functionality for creating agents with
    consistent configuration and error handling.
    """

    def __init__(
        self,
        default_model: str = "openai:gpt-4o-mini",
        max_retries: int = 3,
    ) -> None:
        """
        Initialize the factory.

        Args:
            default_model: Default model ID to use
            max_retries: Default retry count for agent calls
        """
        self._default_model = default_model
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

        return make_agent_async(
            model=model or self._default_model,
            system_prompt=self.get_system_prompt(),
            output_type=self.output_type,
            max_retries=self._max_retries,
        )

    def create_with_config(self, config: ModelConfig) -> FlujoAgent:
        """
        Create an agent using a ModelConfig.

        Args:
            config: Model configuration with all settings

        Returns:
            Configured Flujo agent (AsyncAgentWrapper with OutputT contract)
        """
        from flujo.agents import make_agent_async

        return make_agent_async(
            model=config.model_id,
            system_prompt=self.get_system_prompt(),
            output_type=self.output_type,
            max_retries=config.max_retries,
        )
