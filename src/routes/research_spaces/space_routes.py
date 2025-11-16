"""Research space CRUD route handlers."""

from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, Query, status

from src.application.services.research_space_management_service import (
    CreateSpaceRequest,
    ResearchSpaceManagementService,
    UpdateSpaceRequest,
)
from src.domain.entities.research_space import SpaceStatus
from src.domain.entities.user import User
from src.routes.auth import get_current_active_user
from src.routes.research_spaces.dependencies import get_research_space_service
from src.routes.research_spaces.schemas import (
    CreateSpaceRequestModel,
    ResearchSpaceListResponse,
    ResearchSpaceResponse,
    UpdateSpaceRequestModel,
)

from .router import (
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
    research_spaces_router,
)


@research_spaces_router.post(
    "",
    response_model=ResearchSpaceResponse,
    summary="Create research space",
    description="Create a new research space",
    status_code=HTTP_201_CREATED,
)
def create_space(
    request: CreateSpaceRequestModel,
    current_user: User = Depends(get_current_active_user),
    service: ResearchSpaceManagementService = Depends(get_research_space_service),
) -> ResearchSpaceResponse:
    """Create a new research space."""
    try:
        create_request = CreateSpaceRequest(
            owner_id=current_user.id,
            name=request.name,
            slug=request.slug,
            description=request.description,
            settings=request.settings,
            tags=request.tags,
        )
        space = service.create_space(create_request)
        return ResearchSpaceResponse.from_entity(space)
    except ValueError as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@research_spaces_router.get(
    "",
    response_model=ResearchSpaceListResponse,
    summary="List research spaces",
    description="Get paginated list of research spaces",
)
def list_spaces(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records"),
    owner_id: UUID | None = Query(None, description="Filter by owner"),
    current_user: User = Depends(get_current_active_user),
    service: ResearchSpaceManagementService = Depends(get_research_space_service),
) -> ResearchSpaceListResponse:
    """List research spaces with pagination."""
    try:
        if owner_id:
            spaces = service.get_user_spaces(owner_id, skip, limit)
        else:
            spaces = service.get_active_spaces(skip, limit)

        return ResearchSpaceListResponse(
            spaces=[ResearchSpaceResponse.from_entity(space) for space in spaces],
            total=len(spaces),
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list spaces: {e!s}",
        ) from e


@research_spaces_router.get(
    "/{space_id}",
    response_model=ResearchSpaceResponse,
    summary="Get research space",
    description="Get a research space by ID",
)
def get_space(
    space_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: ResearchSpaceManagementService = Depends(get_research_space_service),
) -> ResearchSpaceResponse:
    """Get a research space by ID."""
    space = service.get_space(space_id, current_user.id)
    if not space:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Research space {space_id} not found",
        )
    return ResearchSpaceResponse.from_entity(space)


@research_spaces_router.get(
    "/slug/{slug}",
    response_model=ResearchSpaceResponse,
    summary="Get research space by slug",
    description="Get a research space by slug",
)
def get_space_by_slug(
    slug: str,
    current_user: User = Depends(get_current_active_user),
    service: ResearchSpaceManagementService = Depends(get_research_space_service),
) -> ResearchSpaceResponse:
    """Get a research space by slug."""
    space = service.get_space_by_slug(slug, current_user.id)
    if not space:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Research space with slug '{slug}' not found",
        )
    return ResearchSpaceResponse.from_entity(space)


@research_spaces_router.put(
    "/{space_id}",
    response_model=ResearchSpaceResponse,
    summary="Update research space",
    description="Update a research space",
)
def update_space(
    space_id: UUID,
    request: UpdateSpaceRequestModel,
    current_user: User = Depends(get_current_active_user),
    service: ResearchSpaceManagementService = Depends(get_research_space_service),
) -> ResearchSpaceResponse:
    """Update a research space."""
    try:
        status_enum = None
        if request.status:
            try:
                status_enum = SpaceStatus(request.status.lower())
            except ValueError:
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {request.status}",
                ) from None

        update_request = UpdateSpaceRequest(
            name=request.name,
            description=request.description,
            settings=request.settings,
            tags=request.tags,
            status=status_enum,
        )
        space = service.update_space(space_id, update_request, current_user.id)
        if not space:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Research space {space_id} not found or access denied",
            )
        return ResearchSpaceResponse.from_entity(space)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@research_spaces_router.delete(
    "/{space_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete research space",
    description="Delete a research space",
)
def delete_space(
    space_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: ResearchSpaceManagementService = Depends(get_research_space_service),
) -> None:
    """Delete a research space."""
    success = service.delete_space(space_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Research space {space_id} not found or access denied",
        )
