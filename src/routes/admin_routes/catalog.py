"""
Data catalog and activation endpoints for the admin API.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.application.services.data_source_activation_service import (
    DataSourceActivationService,
    DataSourceAvailabilitySummary,
)
from src.database.session import get_session
from src.domain.entities.data_discovery_session import SourceCatalogEntry
from src.domain.entities.data_source_activation import (
    ActivationScope,
    DataSourceActivation,
)
from src.infrastructure.repositories.data_discovery_repository_impl import (
    SQLAlchemySourceCatalogRepository,
)

from .dependencies import (
    SYSTEM_ACTOR_ID,
    get_activation_service,
    get_catalog_entry,
)

catalog_router = APIRouter(prefix="/data-catalog")


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
    def from_entity(cls, entry: SourceCatalogEntry) -> CatalogEntryResponse:
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


def _activation_rule_to_response(rule: DataSourceActivation) -> ActivationRuleResponse:
    return ActivationRuleResponse(
        id=rule.id,
        scope=rule.scope,
        is_active=rule.is_active,
        research_space_id=rule.research_space_id,
        updated_by=rule.updated_by,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def _availability_summary_to_response(
    summary: DataSourceAvailabilitySummary,
) -> DataSourceAvailabilityResponse:
    return DataSourceAvailabilityResponse(
        catalog_entry_id=summary.catalog_entry_id,
        effective_is_active=summary.effective_is_active,
        global_rule=(
            _activation_rule_to_response(summary.global_rule)
            if summary.global_rule
            else None
        ),
        project_rules=[
            _activation_rule_to_response(rule) for rule in summary.project_rules
        ],
    )


@catalog_router.get(
    "",
    response_model=list[CatalogEntryResponse],
    summary="List source catalog entries",
    description="Retrieve the global data catalog entries.",
)
def list_catalog_entries(
    category: str | None = Query(None, description="Filter by category"),
    search: str | None = Query(None, description="Search query"),
    session: Session = Depends(get_session),
) -> list[CatalogEntryResponse]:
    repo = SQLAlchemySourceCatalogRepository(session)
    if search:
        entries = repo.search(search, category)
    elif category:
        entries = repo.find_by_category(category)
    else:
        entries = repo.find_all()
    return [CatalogEntryResponse.from_entity(entry) for entry in entries]


@catalog_router.get(
    "/availability",
    response_model=list[DataSourceAvailabilityResponse],
    summary="List catalog availability summaries",
)
def list_catalog_availability(
    session: Session = Depends(get_session),
    activation_service: DataSourceActivationService = Depends(get_activation_service),
) -> list[DataSourceAvailabilityResponse]:
    repo = SQLAlchemySourceCatalogRepository(session)
    entries = repo.find_all()
    summaries = activation_service.get_availability_summaries(
        [entry.id for entry in entries],
    )
    return [_availability_summary_to_response(summary) for summary in summaries]


@catalog_router.get(
    "/{catalog_entry_id}/availability",
    response_model=DataSourceAvailabilityResponse,
    summary="Get catalog entry availability",
)
def get_catalog_entry_availability(
    catalog_entry_id: str,
    activation_service: DataSourceActivationService = Depends(get_activation_service),
    session: Session = Depends(get_session),
) -> DataSourceAvailabilityResponse:
    get_catalog_entry(session, catalog_entry_id)
    summary = activation_service.get_availability_summary(catalog_entry_id)
    return _availability_summary_to_response(summary)


@catalog_router.put(
    "/availability/global",
    response_model=list[DataSourceAvailabilityResponse],
    summary="Bulk set global catalog entry availability",
)
def bulk_set_global_catalog_entry_availability(
    request: BulkActivationUpdateRequest,
    session: Session = Depends(get_session),
    activation_service: DataSourceActivationService = Depends(get_activation_service),
) -> list[DataSourceAvailabilityResponse]:
    repo = SQLAlchemySourceCatalogRepository(session)
    if request.catalog_entry_ids:
        target_ids: list[str] = []
        for catalog_entry_id in request.catalog_entry_ids:
            get_catalog_entry(session, catalog_entry_id)
            target_ids.append(catalog_entry_id)
    else:
        target_ids = [entry.id for entry in repo.find_all()]

    if not target_ids:
        return []

    for catalog_entry_id in target_ids:
        activation_service.set_global_activation(
            catalog_entry_id=catalog_entry_id,
            is_active=request.is_active,
            updated_by=SYSTEM_ACTOR_ID,
        )

    summaries = activation_service.get_availability_summaries(target_ids)
    return [_availability_summary_to_response(summary) for summary in summaries]


@catalog_router.put(
    "/{catalog_entry_id}/availability/global",
    response_model=DataSourceAvailabilityResponse,
    summary="Set global catalog entry availability",
)
def set_global_catalog_entry_availability(
    catalog_entry_id: str,
    request: ActivationUpdateRequest,
    activation_service: DataSourceActivationService = Depends(get_activation_service),
    session: Session = Depends(get_session),
) -> DataSourceAvailabilityResponse:
    get_catalog_entry(session, catalog_entry_id)
    activation_service.set_global_activation(
        catalog_entry_id=catalog_entry_id,
        is_active=request.is_active,
        updated_by=SYSTEM_ACTOR_ID,
    )
    summary = activation_service.get_availability_summary(catalog_entry_id)
    return _availability_summary_to_response(summary)


@catalog_router.delete(
    "/{catalog_entry_id}/availability/global",
    response_model=DataSourceAvailabilityResponse,
    summary="Clear global availability override",
)
def clear_global_catalog_entry_availability(
    catalog_entry_id: str,
    activation_service: DataSourceActivationService = Depends(get_activation_service),
    session: Session = Depends(get_session),
) -> DataSourceAvailabilityResponse:
    get_catalog_entry(session, catalog_entry_id)
    activation_service.clear_global_activation(catalog_entry_id)
    summary = activation_service.get_availability_summary(catalog_entry_id)
    return _availability_summary_to_response(summary)


@catalog_router.put(
    "/{catalog_entry_id}/availability/research-spaces/{space_id}",
    response_model=DataSourceAvailabilityResponse,
    summary="Set project-specific availability",
)
def set_project_catalog_entry_availability(
    catalog_entry_id: str,
    space_id: UUID,
    request: ActivationUpdateRequest,
    activation_service: DataSourceActivationService = Depends(get_activation_service),
    session: Session = Depends(get_session),
) -> DataSourceAvailabilityResponse:
    get_catalog_entry(session, catalog_entry_id)
    activation_service.set_project_activation(
        catalog_entry_id=catalog_entry_id,
        research_space_id=space_id,
        is_active=request.is_active,
        updated_by=SYSTEM_ACTOR_ID,
    )
    summary = activation_service.get_availability_summary(catalog_entry_id)
    return _availability_summary_to_response(summary)


@catalog_router.delete(
    "/{catalog_entry_id}/availability/research-spaces/{space_id}",
    response_model=DataSourceAvailabilityResponse,
    summary="Clear project-specific availability override",
)
def clear_project_catalog_entry_availability(
    catalog_entry_id: str,
    space_id: UUID,
    activation_service: DataSourceActivationService = Depends(get_activation_service),
    session: Session = Depends(get_session),
) -> DataSourceAvailabilityResponse:
    get_catalog_entry(session, catalog_entry_id)
    activation_service.clear_project_activation(
        catalog_entry_id=catalog_entry_id,
        research_space_id=space_id,
    )
    summary = activation_service.get_availability_summary(catalog_entry_id)
    return _availability_summary_to_response(summary)


__all__ = [
    "catalog_router",
    "CatalogEntryResponse",
    "DataSourceAvailabilityResponse",
]
