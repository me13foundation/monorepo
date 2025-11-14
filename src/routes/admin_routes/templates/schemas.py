"""Pydantic schemas for admin template routes."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.domain.entities.source_template import (
    SourceTemplate,
    TemplateCategory,
    TemplateUIConfig,
    ValidationRule,
)
from src.domain.entities.user_data_source import SourceType
from src.type_definitions.common import JSONObject


class TemplateScope(str, Enum):
    """Available template listing scopes."""

    AVAILABLE = "available"
    PUBLIC = "public"
    MINE = "mine"


class TemplateResponse(BaseModel):
    """Response model for template information."""

    id: UUID
    created_by: UUID
    name: str
    description: str
    category: TemplateCategory
    source_type: SourceType
    schema_definition: JSONObject
    validation_rules: list[ValidationRule]
    ui_config: TemplateUIConfig
    is_public: bool
    is_approved: bool
    approval_required: bool
    usage_count: int
    success_rate: float
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None
    tags: list[str]
    version: str
    compatibility_version: str

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, template: SourceTemplate) -> "TemplateResponse":
        """Construct response from domain entity."""
        return cls(**template.model_dump())


class TemplateListResponse(BaseModel):
    """Paginated template list response."""

    templates: list[TemplateResponse]
    total: int
    page: int
    limit: int
    scope: TemplateScope


class TemplateCreatePayload(BaseModel):
    """Request payload for creating a template."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=1000)
    category: TemplateCategory = TemplateCategory.OTHER
    source_type: SourceType
    schema_definition: JSONObject = Field(..., description="JSON schema definition")
    validation_rules: list[ValidationRule] = Field(default_factory=list)
    ui_config: TemplateUIConfig | None = None
    tags: list[str] = Field(default_factory=list)
    is_public: bool = False


class TemplateUpdatePayload(BaseModel):
    """Request payload for updating a template."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    category: TemplateCategory | None = None
    schema_definition: JSONObject | None = None
    validation_rules: list[ValidationRule] | None = None
    ui_config: TemplateUIConfig | None = None
    tags: list[str] | None = None


__all__ = [
    "TemplateCreatePayload",
    "TemplateListResponse",
    "TemplateResponse",
    "TemplateScope",
    "TemplateUpdatePayload",
]
