"""Port interface for Flujo state inspection."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from src.type_definitions.data_sources import FlujoTableSummary


class FlujoStatePort(ABC):
    """Abstraction for reading Flujo state backend details."""

    @abstractmethod
    def find_latest_run_id(self, *, since: datetime) -> str | None:
        """Return the latest Flujo run id created since the provided timestamp."""
        ...

    @abstractmethod
    def get_run_table_summaries(self, run_id: str) -> list[FlujoTableSummary]:
        """Return per-table summaries for a specific Flujo run."""
        ...
