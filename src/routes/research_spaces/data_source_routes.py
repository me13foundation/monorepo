"""Data source routes scoped to research spaces."""

from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.application.services.membership_management_service import (
    MembershipManagementService,
)
from src.application.services.source_management_service import (
    CreateSourceRequest as CreateSourceRequestService,
)
from src.application.services.source_management_service import SourceManagementService
from src.database.session import get_session
from src.domain.entities.user import User
from src.domain.entities.user_data_source import SourceType as DomainSourceType
from src.infrastructure.repositories.user_data_source_repository import (
    SqlAlchemyUserDataSourceRepository,
)
from src.routes.auth import get_current_active_user
from src.routes.research_spaces.dependencies import (
    get_membership_service,
    get_source_service_for_space,
    verify_space_membership,
)
from src.routes.research_spaces.schemas import (
    CreateDataSourceRequest,
    DataSourceListResponse,
    DataSourceResponse,
)

from .router import (
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_500_INTERNAL_SERVER_ERROR,
    research_spaces_router,
)


@research_spaces_router.get(
    "/{space_id}/data-sources",
    response_model=DataSourceListResponse,
    summary="List data sources in space",
    description="Get all data sources in a research space",
)
def list_space_data_sources(
    space_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    membership_service: MembershipManagementService = Depends(get_membership_service),
    source_service: SourceManagementService = Depends(get_source_service_for_space),
    session: Session = Depends(get_session),
) -> DataSourceListResponse:
    """List all data sources in a research space."""
    verify_space_membership(space_id, current_user.id, membership_service, session)

    source_repo = SqlAlchemyUserDataSourceRepository(session)
    sources = source_repo.find_by_research_space(space_id, skip=skip, limit=limit)

    return DataSourceListResponse(
        data_sources=[DataSourceResponse.from_entity(s) for s in sources],
        total=len(sources),
        skip=skip,
        limit=limit,
    )


@research_spaces_router.post(
    "/{space_id}/data-sources",
    response_model=DataSourceResponse,
    status_code=HTTP_201_CREATED,
    summary="Create data source in space",
    description="Create a new data source in a research space",
)
def create_space_data_source(
    space_id: UUID,
    request: CreateDataSourceRequest,
    current_user: User = Depends(get_current_active_user),
    membership_service: MembershipManagementService = Depends(get_membership_service),
    source_service: SourceManagementService = Depends(get_source_service_for_space),
    session: Session = Depends(get_session),
) -> DataSourceResponse:
    """Create a new data source in a research space."""
    verify_space_membership(space_id, current_user.id, membership_service, session)

    try:
        create_request = CreateSourceRequestService(
            owner_id=current_user.id,
            name=request.name,
            source_type=DomainSourceType(request.source_type),
            description=request.description,
            configuration=request.config,
            tags=request.tags,
            research_space_id=space_id,
        )
        data_source = source_service.create_source(create_request)
        return DataSourceResponse.from_entity(data_source)
    except ValueError as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create data source: {e!s}",
        ) from e
