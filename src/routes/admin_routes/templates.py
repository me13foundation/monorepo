"""
Template management endpoints for the admin API.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from src.application.services.template_management_service import (
    CreateTemplateRequest as ServiceCreateTemplateRequest,
)
from src.application.services.template_management_service import (
    TemplateManagementService,
)
from src.application.services.template_management_service import (
    UpdateTemplateRequest as ServiceUpdateTemplateRequest,
)
from src.domain.entities.source_template import (
    SourceTemplate,
    TemplateCategory,
    TemplateUIConfig,
    ValidationRule,
)
from src.domain.entities.user_data_source import (
    SourceType as DomainSourceType,
)
from src.type_definitions.common import JSONObject

from .dependencies import DEFAULT_OWNER_ID, get_template_service

templates_router = APIRouter(prefix="/templates")


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
    source_type: DomainSourceType
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
    def from_entity(cls, template: SourceTemplate) -> TemplateResponse:
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
    source_type: DomainSourceType
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


@templates_router.get(
    "",
    response_model=TemplateListResponse,
    summary="List available templates",
)
async def list_templates(
    scope: TemplateScope = Query(
        TemplateScope.AVAILABLE,
        description="Template listing scope",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    service: TemplateManagementService = Depends(get_template_service),
) -> TemplateListResponse:
    """List templates with optional scope filtering."""
    owner_id = DEFAULT_OWNER_ID
    skip = (page - 1) * limit

    if scope == TemplateScope.PUBLIC:
        templates = service.get_public_templates(skip=skip, limit=limit)
    elif scope == TemplateScope.MINE:
        templates = service.get_user_templates(owner_id, skip=skip, limit=limit)
    else:
        templates = service.get_available_templates(owner_id, skip=skip, limit=limit)

    return TemplateListResponse(
        templates=[TemplateResponse.from_entity(tpl) for tpl in templates],
        total=len(templates),
        page=page,
        limit=limit,
        scope=scope,
    )


@templates_router.get(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Get template details",
)
async def get_template_detail(
    template_id: UUID,
    service: TemplateManagementService = Depends(get_template_service),
) -> TemplateResponse:
    """Retrieve a single template."""
    template = service.get_template(template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )
    return TemplateResponse.from_entity(template)


@templates_router.post(
    "",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create template",
)
async def create_template(
    payload: TemplateCreatePayload,
    service: TemplateManagementService = Depends(get_template_service),
) -> TemplateResponse:
    """Create a new source template."""
    owner_id = DEFAULT_OWNER_ID
    create_request = ServiceCreateTemplateRequest(
        creator_id=owner_id,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        source_type=payload.source_type,
        schema_definition=payload.schema_definition,
        validation_rules=payload.validation_rules,
        ui_config=payload.ui_config or TemplateUIConfig(),
        tags=payload.tags,
        is_public=payload.is_public,
    )
    template = service.create_template(create_request)
    return TemplateResponse.from_entity(template)


@templates_router.put(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Update template",
)
async def update_template(
    template_id: UUID,
    payload: TemplateUpdatePayload,
    service: TemplateManagementService = Depends(get_template_service),
) -> TemplateResponse:
    """Update an existing template."""
    owner_id = DEFAULT_OWNER_ID
    update_request = ServiceUpdateTemplateRequest(
        name=payload.name,
        description=payload.description,
        category=payload.category,
        schema_definition=payload.schema_definition,
        validation_rules=payload.validation_rules,
        ui_config=payload.ui_config,
        tags=payload.tags,
    )
    template = service.update_template(template_id, update_request, owner_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )
    return TemplateResponse.from_entity(template)


@templates_router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete template",
)
async def delete_template(
    template_id: UUID,
    service: TemplateManagementService = Depends(get_template_service),
) -> None:
    """Delete a template."""
    owner_id = DEFAULT_OWNER_ID
    success = service.delete_template(template_id, owner_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )


@templates_router.post(
    "/{template_id}/public",
    response_model=TemplateResponse,
    summary="Make a template public",
)
async def make_template_public(
    template_id: UUID,
    service: TemplateManagementService = Depends(get_template_service),
) -> TemplateResponse:
    """Mark a template as public."""
    template = service.make_template_public(template_id, DEFAULT_OWNER_ID)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateResponse.from_entity(template)


@templates_router.post(
    "/{template_id}/approve",
    response_model=TemplateResponse,
    summary="Approve a template for general use",
)
async def approve_template(
    template_id: UUID,
    service: TemplateManagementService = Depends(get_template_service),
) -> TemplateResponse:
    """Mark a template as approved."""
    template = service.approve_template(template_id, DEFAULT_OWNER_ID)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateResponse.from_entity(template)


__all__ = [
    "TemplateScope",
    "TemplateResponse",
    "TemplateListResponse",
    "templates_router",
]
