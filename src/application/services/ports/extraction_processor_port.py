"""Port interface for publication extraction processors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

from src.type_definitions.common import JSONObject  # noqa: TC001

if TYPE_CHECKING:
    from src.domain.entities.extraction_queue_item import ExtractionQueueItem
    from src.domain.entities.publication import Publication


ExtractionOutcome = Literal["completed", "failed", "skipped"]


@dataclass(frozen=True)
class ExtractionProcessorResult:
    status: ExtractionOutcome
    metadata: JSONObject
    error_message: str | None = None


class ExtractionProcessorPort(Protocol):
    """Port for extracting structured facts from publications."""

    def extract_publication(
        self,
        *,
        queue_item: ExtractionQueueItem,
        publication: Publication | None,
    ) -> ExtractionProcessorResult:
        """Extract facts for a single publication."""


__all__ = [
    "ExtractionOutcome",
    "ExtractionProcessorPort",
    "ExtractionProcessorResult",
]
