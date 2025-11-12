"""Domain entities for data source activation policies."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from enum import Enum
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ActivationScope(str, Enum):
    """Scope types for data source activation policies."""

    GLOBAL = "global"
    RESEARCH_SPACE = "research_space"


class DataSourceActivation(BaseModel):
    """Represents a system-level activation policy for a catalog entry."""

    id: UUID
    catalog_entry_id: str
    scope: ActivationScope
    is_active: bool = Field(
        ...,
        description="Whether the data source is active for this scope",
    )
    research_space_id: UUID | None = Field(
        None,
        description="Target research space when scope is research_space",
    )
    updated_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def validate_scope(self) -> DataSourceActivation:
        """Ensure research space relationships align with the scope."""
        if (
            self.scope == ActivationScope.RESEARCH_SPACE
            and self.research_space_id is None
        ):
            msg = "research_space_id is required when scope is research_space"
            raise ValueError(msg)
        if self.scope == ActivationScope.GLOBAL and self.research_space_id is not None:
            msg = "research_space_id must be null for global scope"
            raise ValueError(msg)
        return self
