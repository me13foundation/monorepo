"""Schemas for admin data catalog routes."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.entities.data_discovery_session import SourceCatalogEntry
from src.domain.entities.data_source_activation import (
    ActivationScope,
    DataSourceActivation,
)


class CatalogEntryResponse(BaseModel):
    """Admin response model for source catalog entries."""

    id: str
    name: str
    description: str
    category: str
    subcategory: str | None
    tags: list[str]
    param_type: str
    is_active: bool
    requires_auth: bool
    usage_count: int
    success_rate: float

    @classmethod
    def from_entity(cls, entry: SourceCatalogEntry) -> "CatalogEntryResponse":
        return cls(
            id=entry.id,
            name=entry.name,
            description=entry.description,
            category=entry.category,
            subcategory=entry.subcategory,
            tags=entry.tags,
            param_type=(
                entry.param_type.value
                if hasattr(entry.param_type, "value")
                else entry.param_type
            ),
            is_active=entry.is_active,
            requires_auth=entry.requires_auth,
            usage_count=entry.usage_count,
            success_rate=entry.success_rate,
        )


class ActivationRuleResponse(BaseModel):
    """API response model for activation rule details."""

    id: UUID
    scope: ActivationScope
    is_active: bool
    research_space_id: UUID | None
    updated_by: UUID
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, rule: DataSourceActivation) -> "ActivationRuleResponse":
        return cls(
            id=rule.id,
            scope=rule.scope,
            is_active=rule.is_active,
            research_space_id=rule.research_space_id,
            updated_by=rule.updated_by,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )


class DataSourceAvailabilityResponse(BaseModel):
    """Availability summary for a catalog entry."""

    catalog_entry_id: str
    effective_is_active: bool
    global_rule: ActivationRuleResponse | None
    project_rules: list[ActivationRuleResponse]


class ActivationUpdateRequest(BaseModel):
    """Payload for toggling activation status."""

    is_active: bool = Field(..., description="Desired activation state")


class BulkActivationUpdateRequest(BaseModel):
    """Payload for applying a global activation to multiple catalog entries."""

    is_active: bool = Field(..., description="Desired activation state")
    catalog_entry_ids: list[str] | None = Field(
        default=None,
        description="Optional subset of catalog entries to update.",
    )


__all__ = [
    "ActivationRuleResponse",
    "ActivationUpdateRequest",
    "BulkActivationUpdateRequest",
    "CatalogEntryResponse",
    "DataSourceAvailabilityResponse",
]
