from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Base domain event structure."""

    event_type: str
    entity_type: str
    entity_id: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = Field(default_factory=dict)


__all__ = ["DomainEvent"]
