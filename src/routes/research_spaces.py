"""
Research Spaces API routes for MED13 Resource Library.

Provides REST API endpoints for research space management and membership operations.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.application.curation.repositories.review_repository import (
    SqlAlchemyReviewRepository,
)
from src.application.curation.services.review_service import (
    ReviewQuery,
    ReviewService,
)
from src.application.services.membership_management_service import (
    InviteMemberRequest,
    MembershipManagementService,
    UpdateMemberRoleRequest,
)
from src.application.services.research_space_management_service import (
    CreateSpaceRequest,
    ResearchSpaceManagementService,
    UpdateSpaceRequest,
)
from src.application.services.source_management_service import (
    CreateSourceRequest as CreateSourceRequestService,
)
from src.application.services.source_management_service import (
    SourceManagementService,
)
from src.database.session import get_session
from src.domain.entities.research_space import ResearchSpace, SpaceStatus
from src.domain.entities.research_space_membership import (
    MembershipRole,
    ResearchSpaceMembership,
)
from src.domain.entities.user import User
from src.domain.entities.user_data_source import (
    SourceConfiguration,
    UserDataSource,
)
from src.domain.entities.user_data_source import (
    SourceType as DomainSourceType,
)
from src.infrastructure.repositories.research_space_membership_repository import (
    SqlAlchemyResearchSpaceMembershipRepository,
)
from src.infrastructure.repositories.research_space_repository import (
    SqlAlchemyResearchSpaceRepository,
)
from src.infrastructure.repositories.user_data_source_repository import (
    SqlAlchemyUserDataSourceRepository,
)
from src.routes.auth import get_current_active_user

# HTTP status codes
HTTP_201_CREATED = 201
HTTP_400_BAD_REQUEST = 400
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409
HTTP_500_INTERNAL_SERVER_ERROR = 500

# Create router
research_spaces_router = APIRouter(
    prefix="/research-spaces",
    tags=["research-spaces"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not Found"},
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"},
    },
)


# Pydantic response models
class ResearchSpaceResponse(BaseModel):
    """Response model for research space."""

    id: UUID
    slug: str
    name: str
    description: str
    owner_id: UUID
    status: str
    settings: dict[str, Any]
    tags: list[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_entity(cls, space: ResearchSpace) -> "ResearchSpaceResponse":
        """Create response from domain entity."""
        return cls(
            id=space.id,
            slug=space.slug,
            name=space.name,
            description=space.description,
            owner_id=space.owner_id,
            status=space.status.value,
            settings=dict(space.settings),
            tags=space.tags,
            created_at=space.created_at.isoformat(),
            updated_at=space.updated_at.isoformat(),
        )


class ResearchSpaceListResponse(BaseModel):
    """Response model for list of research spaces."""

    spaces: list[ResearchSpaceResponse]
    total: int
    skip: int
    limit: int


class MembershipResponse(BaseModel):
    """Response model for research space membership."""

    id: UUID
    space_id: UUID
    user_id: UUID
    role: str
    invited_by: UUID | None
    invited_at: str | None
    joined_at: str | None
    is_active: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_entity(
        cls,
        membership: ResearchSpaceMembership,
    ) -> "MembershipResponse":
        """Create response from domain entity."""
        return cls(
            id=membership.id,
            space_id=membership.space_id,
            user_id=membership.user_id,
            role=membership.role.value,
            invited_by=membership.invited_by,
            invited_at=(
                membership.invited_at.isoformat() if membership.invited_at else None
            ),
            joined_at=(
                membership.joined_at.isoformat() if membership.joined_at else None
            ),
            is_active=membership.is_active,
            created_at=membership.created_at.isoformat(),
            updated_at=membership.updated_at.isoformat(),
        )


class MembershipListResponse(BaseModel):
    """Response model for list of memberships."""

    memberships: list[MembershipResponse]
    total: int
    skip: int
    limit: int


# Pydantic request models
class CreateSpaceRequestModel(BaseModel):
    """Request model for creating a research space."""

    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=3, max_length=50)
    description: str = Field(default="", max_length=500)
    settings: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class UpdateSpaceRequestModel(BaseModel):
    """Request model for updating a research space."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    settings: dict[str, Any] | None = None
    tags: list[str] | None = None
    status: str | None = None


class InviteMemberRequestModel(BaseModel):
    """Request model for inviting a member."""

    user_id: UUID
    role: str = Field(..., description="Membership role")


class UpdateMemberRoleRequestModel(BaseModel):
    """Request model for updating member role."""

    role: str = Field(..., description="New membership role")


# Dependency functions
def get_research_space_service(
    db: Session = Depends(get_session),
) -> ResearchSpaceManagementService:
    """Get research space management service."""
    space_repository = SqlAlchemyResearchSpaceRepository(session=db)
    return ResearchSpaceManagementService(
        research_space_repository=space_repository,
    )


def get_membership_service(
    db: Session = Depends(get_session),
) -> MembershipManagementService:
    """Get membership management service."""
    membership_repository = SqlAlchemyResearchSpaceMembershipRepository(session=db)
    space_repository = SqlAlchemyResearchSpaceRepository(session=db)
    return MembershipManagementService(
        membership_repository=membership_repository,
        research_space_repository=space_repository,
    )


def get_source_service_for_space(
    session: Session = Depends(get_session),
) -> SourceManagementService:
    """Get source management service instance."""
    source_repository = SqlAlchemyUserDataSourceRepository(session)
    # TODO: Add template repository when needed
    return SourceManagementService(source_repository, None)


def verify_space_membership(
    space_id: UUID,
    user_id: UUID,
    membership_service: MembershipManagementService,
    session: Session,
) -> None:
    """
    Verify that a user is a member of a research space.

    Checks both explicit membership and ownership.
    Raises HTTPException if user is not a member or owner.
    """
    # Check if user is an explicit member
    if membership_service.is_user_member(space_id, user_id):
        return

    # Check if user is the owner of the space
    space_repository = SqlAlchemyResearchSpaceRepository(session=session)
    space = space_repository.find_by_id(space_id)
    if space and space.owner_id == user_id:
        return

    # User is neither a member nor the owner
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN,
        detail="User is not a member of this research space",
    )


# Research Space Routes
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


# Membership Routes
@research_spaces_router.post(
    "/{space_id}/members",
    response_model=MembershipResponse,
    summary="Invite member",
    description="Invite a user to join a research space",
    status_code=HTTP_201_CREATED,
)
def invite_member(
    space_id: UUID,
    request: InviteMemberRequestModel,
    current_user: User = Depends(get_current_active_user),
    service: MembershipManagementService = Depends(get_membership_service),
) -> MembershipResponse:
    """Invite a user to join a research space."""
    try:
        try:
            role = MembershipRole(request.role.lower())
        except ValueError:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {request.role}",
            ) from None

        invite_request = InviteMemberRequest(
            space_id=space_id,
            user_id=request.user_id,
            role=role,
            invited_by=current_user.id,
        )
        membership = service.invite_member(invite_request)
        return MembershipResponse.from_entity(membership)
    except ValueError as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@research_spaces_router.get(
    "/{space_id}/members",
    response_model=MembershipListResponse,
    summary="List space members",
    description="Get all members of a research space",
)
def list_space_members(
    space_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    service: MembershipManagementService = Depends(get_membership_service),
) -> MembershipListResponse:
    """List all members of a research space."""
    memberships = service.get_space_members(space_id, skip, limit)
    return MembershipListResponse(
        memberships=[MembershipResponse.from_entity(m) for m in memberships],
        total=len(memberships),
        skip=skip,
        limit=limit,
    )


@research_spaces_router.put(
    "/{space_id}/members/{membership_id}/role",
    response_model=MembershipResponse,
    summary="Update member role",
    description="Update a member's role in a research space",
)
def update_member_role(
    space_id: UUID,
    membership_id: UUID,
    request: UpdateMemberRoleRequestModel,
    current_user: User = Depends(get_current_active_user),
    service: MembershipManagementService = Depends(get_membership_service),
) -> MembershipResponse:
    """Update a member's role in a research space."""
    try:
        try:
            role = MembershipRole(request.role.lower())
        except ValueError:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {request.role}",
            ) from None

        update_request = UpdateMemberRoleRequest(role=role)
        membership = service.update_member_role(
            membership_id,
            update_request,
            current_user.id,
        )
        if not membership:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Membership not found or access denied",
            )
        return MembershipResponse.from_entity(membership)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@research_spaces_router.delete(
    "/{space_id}/members/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove member",
    description="Remove a member from a research space",
)
def remove_member(
    space_id: UUID,
    membership_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: MembershipManagementService = Depends(get_membership_service),
) -> None:
    """Remove a member from a research space."""
    success = service.remove_member(membership_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Membership not found or access denied",
        )


@research_spaces_router.post(
    "/memberships/{membership_id}/accept",
    response_model=MembershipResponse,
    summary="Accept invitation",
    description="Accept a pending invitation to join a research space",
)
def accept_invitation(
    membership_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: MembershipManagementService = Depends(get_membership_service),
) -> MembershipResponse:
    """Accept a pending invitation."""
    membership = service.accept_invitation(membership_id, current_user.id)
    if not membership:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Invitation not found or already accepted",
        )
    return MembershipResponse.from_entity(membership)


@research_spaces_router.get(
    "/memberships/pending",
    response_model=MembershipListResponse,
    summary="Get pending invitations",
    description="Get all pending invitations for the current user",
)
def get_pending_invitations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    service: MembershipManagementService = Depends(get_membership_service),
) -> MembershipListResponse:
    """Get all pending invitations for the current user."""
    memberships = service.get_pending_invitations(current_user.id, skip, limit)
    return MembershipListResponse(
        memberships=[MembershipResponse.from_entity(m) for m in memberships],
        total=len(memberships),
        skip=skip,
        limit=limit,
    )


# Data Source Integration Routes
class DataSourceResponse(BaseModel):
    """Response model for data source."""

    id: UUID
    owner_id: UUID
    research_space_id: UUID | None
    name: str
    description: str
    source_type: str
    status: str
    created_at: str
    updated_at: str

    @classmethod
    def from_entity(cls, source: Any) -> "DataSourceResponse":
        """Create response from domain entity."""

        if isinstance(source, UserDataSource):
            return cls(
                id=source.id,
                owner_id=source.owner_id,
                research_space_id=source.research_space_id,
                name=source.name,
                description=source.description,
                source_type=source.source_type.value,
                status=source.status.value,
                created_at=source.created_at.isoformat(),
                updated_at=source.updated_at.isoformat(),
            )
        invalid_entity_msg = "Invalid source entity"
        raise ValueError(invalid_entity_msg)


class DataSourceListResponse(BaseModel):
    """Response model for list of data sources."""

    data_sources: list[DataSourceResponse]
    total: int
    skip: int
    limit: int


class CreateDataSourceRequest(BaseModel):
    """Request model for creating a data source in a space."""

    name: str
    description: str = ""
    source_type: str
    config: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


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
    # Verify user is a member of the space
    verify_space_membership(space_id, current_user.id, membership_service, session)

    # Get data sources for this space
    source_repo = SqlAlchemyUserDataSourceRepository(session)
    sources = source_repo.find_by_research_space(space_id, skip=skip, limit=limit)

    return DataSourceListResponse(
        data_sources=[DataSourceResponse.from_entity(s) for s in sources],
        total=len(sources),  # TODO: Add count method
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
    # Verify user is a member of the space
    verify_space_membership(space_id, current_user.id, membership_service, session)

    try:
        # Create source configuration
        config = SourceConfiguration(**request.config)

        # Create source request
        create_request = CreateSourceRequestService(
            owner_id=current_user.id,
            name=request.name,
            source_type=DomainSourceType(request.source_type),
            description=request.description,
            configuration=config,
            tags=request.tags,
            research_space_id=space_id,
        )

        # Create the data source
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


# Curation Integration Routes
class CurationStatsResponse(BaseModel):
    """Response model for curation statistics."""

    total: int
    pending: int
    approved: int
    rejected: int


class CurationQueueItemResponse(BaseModel):
    """Response model for curation queue item."""

    id: int
    entity_type: str
    entity_id: str
    status: str
    priority: str
    quality_score: float | None
    issues: int
    last_updated: str | None


class CurationQueueResponse(BaseModel):
    """Response model for curation queue."""

    items: list[CurationQueueItemResponse]
    total: int
    skip: int
    limit: int


def get_curation_service(session: Session = Depends(get_session)) -> ReviewService:
    """Get curation review service instance."""
    repository = SqlAlchemyReviewRepository()
    return ReviewService(repository)


@research_spaces_router.get(
    "/{space_id}/curation/stats",
    response_model=CurationStatsResponse,
    summary="Get curation statistics",
    description="Get curation statistics for a research space",
)
def get_space_curation_stats(
    space_id: UUID,
    current_user: User = Depends(get_current_active_user),
    membership_service: MembershipManagementService = Depends(get_membership_service),
    curation_service: ReviewService = Depends(get_curation_service),
    session: Session = Depends(get_session),
) -> CurationStatsResponse:
    """Get curation statistics for a research space."""
    # Verify user is a member of the space
    verify_space_membership(space_id, current_user.id, membership_service, session)

    try:
        stats = curation_service.get_stats(session, str(space_id))
        return CurationStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get curation stats: {e!s}",
        ) from e


@research_spaces_router.get(
    "/{space_id}/curation/queue",
    response_model=CurationQueueResponse,
    summary="List curation queue",
    description="Get curation queue items for a research space",
)
def list_space_curation_queue(
    space_id: UUID,
    entity_type: str | None = Query(None, description="Filter by entity type"),
    status: str | None = Query(None, description="Filter by status"),
    priority: str | None = Query(None, description="Filter by priority"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    membership_service: MembershipManagementService = Depends(get_membership_service),
    curation_service: ReviewService = Depends(get_curation_service),
    session: Session = Depends(get_session),
) -> CurationQueueResponse:
    """List curation queue items for a research space."""
    # Verify user is a member of the space
    verify_space_membership(space_id, current_user.id, membership_service, session)

    try:
        query = ReviewQuery(
            entity_type=entity_type,
            status=status,
            priority=priority,
            research_space_id=str(space_id),
            limit=limit,
            offset=skip,
        )
        items = curation_service.list_queue(session, query)

        return CurationQueueResponse(
            items=[
                CurationQueueItemResponse(
                    id=item.id,
                    entity_type=item.entity_type,
                    entity_id=item.entity_id,
                    status=item.status,
                    priority=item.priority,
                    quality_score=item.quality_score,
                    issues=item.issues,
                    last_updated=(
                        item.last_updated.isoformat() if item.last_updated else None
                    ),
                )
                for item in items
            ],
            total=len(items),
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get curation queue: {e!s}",
        ) from e
