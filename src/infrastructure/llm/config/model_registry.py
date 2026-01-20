"""
Model registry for AI agent configurations.

Centralizes model configurations, costs, and default settings
for all AI agents in the system.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class ModelConfig:
    """Configuration for a specific LLM model."""

    model_id: str
    display_name: str
    prompt_tokens_per_1k: float
    completion_tokens_per_1k: float
    max_retries: int = 3
    timeout_seconds: float = 30.0
    supports_structured_output: bool = True


class ModelRegistry:
    """
    Registry of available LLM models and their configurations.

    Provides centralized access to model configurations for
    agent factories and cost tracking.
    """

    # Default models for different use cases
    DEFAULT_QUERY_MODEL: ClassVar[str] = "openai:gpt-4o-mini"
    DEFAULT_EXTRACTION_MODEL: ClassVar[str] = "openai:gpt-4o"
    DEFAULT_CURATION_MODEL: ClassVar[str] = "openai:gpt-4o"

    _models: ClassVar[dict[str, ModelConfig]] = {
        "openai:gpt-4o-mini": ModelConfig(
            model_id="openai:gpt-4o-mini",
            display_name="GPT-4o Mini",
            prompt_tokens_per_1k=0.00015,
            completion_tokens_per_1k=0.0006,
            max_retries=3,
            timeout_seconds=30.0,
        ),
        "openai:gpt-4o": ModelConfig(
            model_id="openai:gpt-4o",
            display_name="GPT-4o",
            prompt_tokens_per_1k=0.005,
            completion_tokens_per_1k=0.015,
            max_retries=3,
            timeout_seconds=60.0,
        ),
        "openai:gpt-4-turbo": ModelConfig(
            model_id="openai:gpt-4-turbo",
            display_name="GPT-4 Turbo",
            prompt_tokens_per_1k=0.01,
            completion_tokens_per_1k=0.03,
            max_retries=3,
            timeout_seconds=90.0,
        ),
        "anthropic:claude-3-5-sonnet": ModelConfig(
            model_id="anthropic:claude-3-5-sonnet",
            display_name="Claude 3.5 Sonnet",
            prompt_tokens_per_1k=0.003,
            completion_tokens_per_1k=0.015,
            max_retries=3,
            timeout_seconds=60.0,
        ),
    }

    @classmethod
    def get_model(cls, model_id: str) -> ModelConfig:
        """
        Get configuration for a specific model.

        Raises:
            KeyError: If the model is not registered
        """
        if model_id not in cls._models:
            msg = (
                f"Model '{model_id}' not found in registry. "
                f"Available models: {list(cls._models.keys())}"
            )
            raise KeyError(msg)
        return cls._models[model_id]

    @classmethod
    def get_model_or_default(
        cls,
        model_id: str | None,
        default: str | None = None,
    ) -> ModelConfig:
        """
        Get model config, falling back to default if not found.

        Args:
            model_id: The model ID to look up
            default: Fallback model ID (defaults to DEFAULT_QUERY_MODEL)

        Returns:
            ModelConfig for the requested or default model
        """
        if model_id and model_id in cls._models:
            return cls._models[model_id]
        fallback = default or cls.DEFAULT_QUERY_MODEL
        return cls._models[fallback]

    @classmethod
    def list_models(cls) -> list[str]:
        """List all registered model IDs."""
        return list(cls._models.keys())

    @classmethod
    def register_model(cls, config: ModelConfig) -> None:
        """
        Register a new model configuration.

        Use for testing or adding custom model configurations.
        """
        cls._models[config.model_id] = config
