"""
Admin API routes for MED13 Resource Library.

These endpoints provide administrative functionality for managing users,
data sources, system monitoring, and audit logging.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from src.application.services.data_source_activation_service import (
    DataSourceActivationService,
    DataSourceAvailabilitySummary,
)
from src.application.services.data_source_authorization_service import (
    DataSourceAuthorizationService,
)
from src.application.services.source_management_service import (
    CreateSourceRequest,
    SourceManagementService,
    UpdateSourceRequest,
)
from src.application.services.template_management_service import (
    CreateTemplateRequest as ServiceCreateTemplateRequest,
)
from src.application.services.template_management_service import (
    TemplateManagementService,
)
from src.application.services.template_management_service import (
    UpdateTemplateRequest as ServiceUpdateTemplateRequest,
)
from src.database.session import SessionLocal, get_session
from src.domain.entities.data_discovery_session import SourceCatalogEntry
from src.domain.entities.data_source_activation import (
    ActivationScope,
    DataSourceActivation,
)
from src.domain.entities.source_template import (
    SourceTemplate,
    TemplateCategory,
    TemplateUIConfig,
    ValidationRule,
)
from src.domain.entities.user_data_source import (
    IngestionSchedule,
    QualityMetrics,
    SourceConfiguration,
    SourceStatus,
)
from src.domain.entities.user_data_source import (
    SourceType as DomainSourceType,
)
from src.infrastructure.repositories.data_discovery_repository_impl import (
    SQLAlchemySourceCatalogRepository,
)
from src.infrastructure.repositories.data_source_activation_repository import (
    SqlAlchemyDataSourceActivationRepository,
)
from src.infrastructure.repositories.source_template_repository import (
    SqlAlchemySourceTemplateRepository,
)
from src.infrastructure.repositories.user_data_source_repository import (
    SqlAlchemyUserDataSourceRepository,
)
from src.type_definitions.common import JSONObject

# Create router
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        500: {"description": "Internal Server Error"},
    },
)


def get_db_session() -> Session:
    """Get database session."""
    return SessionLocal()


# Dependency injection functions
def get_source_service() -> SourceManagementService:
    """Get source management service instance."""
    session = get_db_session()
    user_repo = SqlAlchemyUserDataSourceRepository(session)
    template_repo = SqlAlchemySourceTemplateRepository(session)
    return SourceManagementService(user_repo, template_repo)


def get_template_service() -> TemplateManagementService:
    """Get template management service instance."""
    session = get_db_session()
    template_repo = SqlAlchemySourceTemplateRepository(session)
    return TemplateManagementService(template_repo)


def get_activation_service() -> DataSourceActivationService:
    """Get data source activation service instance."""
    session = get_db_session()
    activation_repo = SqlAlchemyDataSourceActivationRepository(session)
    return DataSourceActivationService(activation_repo)


def _get_catalog_entry(session: Session, catalog_entry_id: str) -> SourceCatalogEntry:
    repo = SQLAlchemySourceCatalogRepository(session)
    entry = repo.find_by_id(catalog_entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Catalog entry not found")
    return entry


async def get_auth_service() -> DataSourceAuthorizationService:
    """Get authorization service instance."""
    return DataSourceAuthorizationService()


# Request/Response Models

DEFAULT_OWNER_ID = UUID("00000000-0000-0000-0000-000000000001")
SYSTEM_ACTOR_ID = DEFAULT_OWNER_ID


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
    source_type: DomainSourceType
    schema_definition: JSONObject = Field(..., description="JSON schema definition")
    validation_rules: list[ValidationRule] = Field(default_factory=list)
    ui_config: TemplateUIConfig | None = None
    tags: list[str] = Field(default_factory=list)
    is_public: bool = False


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
        description="Optional subset of catalog entries to update. Defaults to all entries.",
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


class TemplateUpdatePayload(BaseModel):
    """Request payload for updating a template."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    category: TemplateCategory | None = None
    schema_definition: JSONObject | None = None
    validation_rules: list[ValidationRule] | None = None
    ui_config: TemplateUIConfig | None = None
    tags: list[str] | None = None


@router.get(
    "/templates",
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


@router.get(
    "/templates/{template_id}",
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


@router.post(
    "/templates",
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


@router.put(
    "/templates/{template_id}",
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


@router.delete(
    "/templates/{template_id}",
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


class CreateDataSourceRequest(BaseModel):
    """Request model for creating a data source."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    source_type: DomainSourceType
    template_id: UUID | None = None
    config: SourceConfiguration = Field(
        ...,
        description="Data source configuration",
    )
    ingestion_schedule: IngestionSchedule | None = Field(
        None,
        description="Ingestion schedule configuration",
    )


class UpdateDataSourceRequest(BaseModel):
    """Request model for updating a data source."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    status: SourceStatus | None = None
    config: SourceConfiguration | None = Field(
        None,
        description="Updated data source configuration",
    )
    ingestion_schedule: IngestionSchedule | None = Field(
        None,
        description="Updated ingestion schedule",
    )


class DataSourceResponse(BaseModel):
    """Response model for data source information."""

    id: UUID
    owner_id: UUID
    name: str
    description: str | None
    source_type: DomainSourceType
    status: SourceStatus
    config: SourceConfiguration
    template_id: UUID | None
    ingestion_schedule: IngestionSchedule | None
    quality_metrics: QualityMetrics | None
    last_ingested_at: str | None
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class DataSourceListResponse(BaseModel):
    """Response model for data source listing."""

    data_sources: list[DataSourceResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class SystemStatsResponse(BaseModel):
    """Response model for system statistics."""

    total_data_sources: int
    active_data_sources: int
    total_records: int
    system_health: str
    last_updated: str


class DataSourceStats(BaseModel):
    """Statistics for data sources."""

    total_sources: int
    active_sources: int
    error_sources: int
    sources_by_type: dict[str, int]


# Routes


@router.get(
    "/data-sources",
    response_model=DataSourceListResponse,
    summary="List data sources",
    description="Retrieve a paginated list of all data sources with optional filtering.",
)
async def list_data_sources(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: SourceStatus | None = Query(None, description="Filter by status"),
    source_type: str | None = Query(None, description="Filter by source type"),
    research_space_id: UUID
    | None = Query(
        None,
        description="Filter by research space ID",
    ),
    service: SourceManagementService = Depends(get_source_service),
    session: Session = Depends(get_session),
) -> DataSourceListResponse:
    """List data sources with pagination and filtering."""
    try:
        source_repo = SqlAlchemyUserDataSourceRepository(session)

        # If research_space_id is provided, filter by space
        if research_space_id:
            skip = (page - 1) * limit
            data_sources = source_repo.find_by_research_space(
                research_space_id,
                skip=skip,
                limit=limit,
            )
            # TODO: Add count method to repository for accurate total
            total = len(data_sources)
        else:
            # Get all data sources (simplified for now - in real implementation would include filtering)
            all_sources = service.get_active_sources(0, 1000)  # Get a large batch

            # Apply filters (placeholder)
            data_sources = all_sources
            if status:
                data_sources = [ds for ds in data_sources if ds.status == status]
            if source_type:
                type_enum = DomainSourceType(source_type)
                data_sources = [
                    ds for ds in data_sources if ds.source_type == type_enum
                ]

            # Pagination
            total = len(data_sources)
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            data_sources = data_sources[start_idx:end_idx]

        return DataSourceListResponse(
            data_sources=[DataSourceResponse.model_validate(ds) for ds in data_sources],
            total=total,
            page=page,
            limit=limit,
            has_next=(page * limit) < total,
            has_prev=page > 1,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list data sources: {e!s}",
        )


@router.get(
    "/data-catalog",
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


@router.get(
    "/data-catalog/availability",
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


@router.get(
    "/data-catalog/{catalog_entry_id}/availability",
    response_model=DataSourceAvailabilityResponse,
    summary="Get catalog entry availability",
)
def get_catalog_entry_availability(
    catalog_entry_id: str,
    activation_service: DataSourceActivationService = Depends(get_activation_service),
    session: Session = Depends(get_session),
) -> DataSourceAvailabilityResponse:
    _get_catalog_entry(session, catalog_entry_id)
    summary = activation_service.get_availability_summary(catalog_entry_id)
    return _availability_summary_to_response(summary)


@router.put(
    "/data-catalog/availability/global",
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
            _get_catalog_entry(session, catalog_entry_id)
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


@router.put(
    "/data-catalog/{catalog_entry_id}/availability/global",
    response_model=DataSourceAvailabilityResponse,
    summary="Set global catalog entry availability",
)
def set_global_catalog_entry_availability(
    catalog_entry_id: str,
    request: ActivationUpdateRequest,
    activation_service: DataSourceActivationService = Depends(get_activation_service),
    session: Session = Depends(get_session),
) -> DataSourceAvailabilityResponse:
    _get_catalog_entry(session, catalog_entry_id)
    activation_service.set_global_activation(
        catalog_entry_id=catalog_entry_id,
        is_active=request.is_active,
        updated_by=SYSTEM_ACTOR_ID,
    )
    summary = activation_service.get_availability_summary(catalog_entry_id)
    return _availability_summary_to_response(summary)


@router.delete(
    "/data-catalog/{catalog_entry_id}/availability/global",
    response_model=DataSourceAvailabilityResponse,
    summary="Clear global availability override",
)
def clear_global_catalog_entry_availability(
    catalog_entry_id: str,
    activation_service: DataSourceActivationService = Depends(get_activation_service),
    session: Session = Depends(get_session),
) -> DataSourceAvailabilityResponse:
    _get_catalog_entry(session, catalog_entry_id)
    activation_service.clear_global_activation(catalog_entry_id)
    summary = activation_service.get_availability_summary(catalog_entry_id)
    return _availability_summary_to_response(summary)


@router.put(
    "/data-catalog/{catalog_entry_id}/availability/research-spaces/{space_id}",
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
    _get_catalog_entry(session, catalog_entry_id)
    activation_service.set_project_activation(
        catalog_entry_id=catalog_entry_id,
        research_space_id=space_id,
        is_active=request.is_active,
        updated_by=SYSTEM_ACTOR_ID,
    )
    summary = activation_service.get_availability_summary(catalog_entry_id)
    return _availability_summary_to_response(summary)


@router.delete(
    "/data-catalog/{catalog_entry_id}/availability/research-spaces/{space_id}",
    response_model=DataSourceAvailabilityResponse,
    summary="Clear project-specific availability override",
)
def clear_project_catalog_entry_availability(
    catalog_entry_id: str,
    space_id: UUID,
    activation_service: DataSourceActivationService = Depends(get_activation_service),
    session: Session = Depends(get_session),
) -> DataSourceAvailabilityResponse:
    _get_catalog_entry(session, catalog_entry_id)
    activation_service.clear_project_activation(
        catalog_entry_id=catalog_entry_id,
        research_space_id=space_id,
    )
    summary = activation_service.get_availability_summary(catalog_entry_id)
    return _availability_summary_to_response(summary)


@router.post(
    "/data-sources",
    response_model=DataSourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create data source",
    description="Create a new data source configuration.",
)
async def create_data_source(
    request: CreateDataSourceRequest,
    service: SourceManagementService = Depends(get_source_service),
    auth_service: DataSourceAuthorizationService = Depends(get_auth_service),
) -> DataSourceResponse:
    """Create a new data source."""
    try:
        # TODO: Get current user from authentication context
        owner_id = UUID("00000000-0000-0000-0000-000000000001")  # Placeholder

        # Create the data source request
        create_request = CreateSourceRequest(
            owner_id=owner_id,
            name=request.name,
            source_type=request.source_type,
            description=request.description or "",
            configuration=request.config.model_copy(),
            template_id=request.template_id,
        )

        # Create the data source
        data_source = service.create_source(create_request)

        return DataSourceResponse.model_validate(data_source)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create data source: {e!s}",
        )


@router.get(
    "/data-sources/{source_id}",
    response_model=DataSourceResponse,
    summary="Get data source",
    description="Retrieve detailed information about a specific data source.",
)
async def get_data_source(
    source_id: UUID,
    service: SourceManagementService = Depends(get_source_service),
) -> DataSourceResponse:
    """Get a specific data source by ID."""
    try:
        data_source = service.get_source(source_id)
        if not data_source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data source not found",
            )
        return DataSourceResponse.model_validate(data_source)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data source: {e!s}",
        )


@router.put(
    "/data-sources/{source_id}",
    response_model=DataSourceResponse,
    summary="Update data source",
    description="Update an existing data source configuration.",
)
async def update_data_source(
    source_id: UUID,
    request: UpdateDataSourceRequest,
    service: SourceManagementService = Depends(get_source_service),
    auth_service: DataSourceAuthorizationService = Depends(get_auth_service),
) -> DataSourceResponse:
    """Update an existing data source."""
    try:
        # TODO: Get current user from authentication context
        user_id = UUID("00000000-0000-0000-0000-000000000001")  # Placeholder

        # Create update request
        update_request = UpdateSourceRequest(
            name=request.name,
            description=request.description,
            configuration=(request.config.model_copy() if request.config else None),
            ingestion_schedule=(
                request.ingestion_schedule.model_copy()
                if request.ingestion_schedule
                else None
            ),
        )

        # Update the data source
        data_source = service.update_source(source_id, update_request, user_id)

        if not data_source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data source not found",
            )

        return DataSourceResponse.model_validate(data_source)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update data source: {e!s}",
        )


@router.delete(
    "/data-sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete data source",
    description="Delete an existing data source.",
)
async def delete_data_source(
    source_id: UUID,
    service: SourceManagementService = Depends(get_source_service),
    auth_service: DataSourceAuthorizationService = Depends(get_auth_service),
) -> None:
    """Delete a data source."""
    try:
        # TODO: Get current user from authentication context
        user_id = UUID("00000000-0000-0000-0000-000000000001")  # Placeholder

        success = service.delete_source(source_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data source not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete data source: {e!s}",
        )


@router.get(
    "/stats",
    response_model=SystemStatsResponse,
    summary="Get system statistics",
    description="Retrieve overall system statistics for the admin dashboard.",
)
async def get_system_stats(
    service: SourceManagementService = Depends(get_source_service),
) -> SystemStatsResponse:
    """Get system-wide statistics."""
    try:
        # Get data source statistics
        stats = service.get_statistics()
        data_sources = service.get_active_sources(0, 1000)
        active_sources = len(
            [ds for ds in data_sources if ds.status == SourceStatus.ACTIVE],
        )

        return SystemStatsResponse(
            total_data_sources=stats.get("total_sources", 0),
            active_data_sources=active_sources,
            total_records=0,  # TODO: Implement record counting
            system_health="healthy",
            last_updated="2024-01-01T00:00:00Z",  # TODO: Implement real timestamp
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system stats: {e!s}",
        )


@router.get(
    "/data-sources/stats",
    response_model=DataSourceStats,
    summary="Get data source statistics",
    description="Retrieve statistics about data sources grouped by type and status.",
)
async def get_data_source_stats(
    service: SourceManagementService = Depends(get_source_service),
) -> DataSourceStats:
    """Get data source statistics."""
    try:
        # Get statistics from service
        stats = service.get_statistics()

        # Get all sources to calculate additional stats
        all_sources = service.get_active_sources(0, 1000)
        # TODO: Get sources by status when service supports it
        active_sources = len(
            [ds for ds in all_sources if ds.status == SourceStatus.ACTIVE],
        )
        # For now, assume no error sources (TODO: add error status filtering)
        error_sources = 0

        # Count by type from all sources
        sources_by_type: dict[str, int] = {}
        for ds in all_sources:
            source_type = ds.source_type.value
            sources_by_type[source_type] = sources_by_type.get(source_type, 0) + 1

        total_sources = stats.get("total_sources", len(all_sources))

        return DataSourceStats(
            total_sources=total_sources,
            active_sources=active_sources,
            error_sources=error_sources,
            sources_by_type=sources_by_type,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data source stats: {e!s}",
        )


@router.post(
    "/templates/{template_id}/public",
    response_model=TemplateResponse,
    summary="Make a template public",
)
async def make_template_public(
    template_id: UUID,
    service: TemplateManagementService = Depends(get_template_service),
) -> TemplateResponse:
    template = service.make_template_public(template_id, DEFAULT_OWNER_ID)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateResponse.from_entity(template)


@router.post(
    "/templates/{template_id}/approve",
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
