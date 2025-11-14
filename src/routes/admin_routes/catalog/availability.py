"""Availability endpoints for catalog entries."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.application.services.data_source_activation_service import (
    DataSourceActivationService,
)
from src.database.session import get_session
from src.infrastructure.repositories.data_discovery_repository_impl import (
    SQLAlchemySourceCatalogRepository,
)
from src.routes.admin_routes.dependencies import (
    SYSTEM_ACTOR_ID,
    get_activation_service,
    get_catalog_entry,
)

from .mappers import availability_summary_to_response
from .schemas import (
    ActivationUpdateRequest,
    BulkActivationUpdateRequest,
    DataSourceAvailabilityResponse,
)

router = APIRouter()


@router.get(
    "/availability",
    response_model=list[DataSourceAvailabilityResponse],
    summary="List catalog availability summaries",
)
def list_catalog_availability(
    session: Session = Depends(get_session),
    activation_service: DataSourceActivationService = Depends(get_activation_service),
) -> list[DataSourceAvailabilityResponse]:
    """Return availability summaries for all catalog entries."""
    repo = SQLAlchemySourceCatalogRepository(session)
    entries = repo.find_all()
    summaries = activation_service.get_availability_summaries(
        [entry.id for entry in entries],
    )
    return [availability_summary_to_response(summary) for summary in summaries]


@router.get(
    "/{catalog_entry_id}/availability",
    response_model=DataSourceAvailabilityResponse,
    summary="Get catalog entry availability",
)
def get_catalog_entry_availability(
    catalog_entry_id: str,
    activation_service: DataSourceActivationService = Depends(get_activation_service),
    session: Session = Depends(get_session),
) -> DataSourceAvailabilityResponse:
    """Get availability summary for a single entry."""
    get_catalog_entry(session, catalog_entry_id)
    summary = activation_service.get_availability_summary(catalog_entry_id)
    return availability_summary_to_response(summary)


@router.put(
    "/availability/global",
    response_model=list[DataSourceAvailabilityResponse],
    summary="Bulk set global catalog entry availability",
)
def bulk_set_global_catalog_entry_availability(
    request: BulkActivationUpdateRequest,
    session: Session = Depends(get_session),
    activation_service: DataSourceActivationService = Depends(get_activation_service),
) -> list[DataSourceAvailabilityResponse]:
    """Apply a global activation state to multiple entries."""
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
    return [availability_summary_to_response(summary) for summary in summaries]


@router.put(
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
    """Set global availability for a single entry."""
    get_catalog_entry(session, catalog_entry_id)
    activation_service.set_global_activation(
        catalog_entry_id=catalog_entry_id,
        is_active=request.is_active,
        updated_by=SYSTEM_ACTOR_ID,
    )
    summary = activation_service.get_availability_summary(catalog_entry_id)
    return availability_summary_to_response(summary)


@router.delete(
    "/{catalog_entry_id}/availability/global",
    response_model=DataSourceAvailabilityResponse,
    summary="Clear global availability override",
)
def clear_global_catalog_entry_availability(
    catalog_entry_id: str,
    activation_service: DataSourceActivationService = Depends(get_activation_service),
    session: Session = Depends(get_session),
) -> DataSourceAvailabilityResponse:
    """Remove the global availability override for an entry."""
    get_catalog_entry(session, catalog_entry_id)
    activation_service.clear_global_activation(catalog_entry_id)
    summary = activation_service.get_availability_summary(catalog_entry_id)
    return availability_summary_to_response(summary)


@router.put(
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
    """Set research-space-specific availability."""
    get_catalog_entry(session, catalog_entry_id)
    activation_service.set_project_activation(
        catalog_entry_id=catalog_entry_id,
        research_space_id=space_id,
        is_active=request.is_active,
        updated_by=SYSTEM_ACTOR_ID,
    )
    summary = activation_service.get_availability_summary(catalog_entry_id)
    return availability_summary_to_response(summary)


@router.delete(
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
    """Remove the research-space override for an entry."""
    get_catalog_entry(session, catalog_entry_id)
    activation_service.clear_project_activation(
        catalog_entry_id=catalog_entry_id,
        research_space_id=space_id,
    )
    summary = activation_service.get_availability_summary(catalog_entry_id)
    return availability_summary_to_response(summary)


__all__ = ["router"]
