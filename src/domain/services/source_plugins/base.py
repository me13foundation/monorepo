from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.domain.entities.user_data_source import (
        SourceConfiguration,
        SourceType,
    )


class SourcePlugin(ABC):
    """Base class for data source plugins."""

    source_type: SourceType

    def __init__(self, *, name: str | None = None, description: str | None = None):
        self.name = name or self.source_type.value.replace("_", " ").title()
        self.description = description or ""

    @abstractmethod
    def validate_configuration(
        self,
        configuration: SourceConfiguration,
    ) -> SourceConfiguration:
        """Validate and sanitize a configuration before persistence."""

    def activation_metadata(self, configuration: SourceConfiguration) -> dict[str, Any]:
        """
        Optional metadata emitted when a plugin is activated.

        Subclasses can override to expose structured plugin-specific data.
        """

        _ = configuration  # Preserve signature for subclasses while avoiding unused warnings
        return {}


__all__ = ["SourcePlugin"]
