"""
User management routes for MED13 Resource Library.

Provides REST API endpoints for administrative user management operations.
"""

from typing import Any, Dict, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query

from ..application.container import container
from ..application.services.user_management_service import (
    UserManagementService,
    UserManagementError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from ..application.services.authorization_service import AuthorizationService
from ..application.services.authentication_service import AuthenticationService
from .auth import get_current_active_user
from ..application.dto.auth_requests import CreateUserRequest, AdminUpdateUserRequest
from ..application.dto.auth_responses import (
    UserProfileResponse,
    UserListResponse,
    UserStatisticsResponse,
    UserPublic,
    GenericSuccessResponse,
    ErrorResponse,
    ValidationErrorResponse,
)
from ..domain.entities.user import User, UserRole, UserStatus

# HTTP status codes
HTTP_201_CREATED = 201
HTTP_400_BAD_REQUEST = 400
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409
HTTP_500_INTERNAL_SERVER_ERROR = 500


# Create router
users_router = APIRouter(
    prefix="/users",
    tags=["user-management"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not Found"},
        422: {"model": ValidationErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)


@users_router.post(
    "",
    response_model=UserProfileResponse,
    summary="Create user",
    description="Create a new user account (admin only)",
    status_code=HTTP_201_CREATED,
)
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(get_current_active_user),
    user_service: UserManagementService = Depends(
        container.get_user_management_service
    ),
    authz_service: AuthorizationService = Depends(container.get_authorization_service),
) -> UserProfileResponse:
    """
    Create a new user account (administrative operation).
    """
    try:
        # Check permission
        from ..domain.value_objects.permission import Permission

        await authz_service.require_permission(
            current_user.id, Permission("user:create")
        )
        user = await user_service.create_user(request, current_user.id)
        return UserProfileResponse(user=UserPublic.from_user(user))
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))
    except UserManagementError as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User creation failed: {str(e)}",
        )


@users_router.get(
    "",
    response_model=UserListResponse,
    summary="List users",
    description="Get paginated list of users with optional filtering",
)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    role: Optional[str] = Query(None, description="Filter by role"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_active_user),
    user_service: UserManagementService = Depends(
        container.get_user_management_service
    ),
) -> UserListResponse:
    """
    List users with pagination and filtering.
    """
    try:
        # Validate role parameter
        user_role = None
        if role:
            try:
                user_role = UserRole(role.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid role: {role}",
                )

        # Validate status parameter
        user_status = None
        if status_filter:
            try:
                user_status = UserStatus(status_filter.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {status_filter}",
                )

        response = await user_service.list_users(
            skip=skip, limit=limit, role=user_role, status=user_status
        )

        return response
    except UserManagementError as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}",
        )


@users_router.get(
    "/{user_id}",
    response_model=UserProfileResponse,
    summary="Get user by ID",
    description="Get detailed information about a specific user",
)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    user_service: UserManagementService = Depends(
        container.get_user_management_service
    ),
) -> UserProfileResponse:
    """
    Get user by ID.
    """
    try:
        # Check if user can access this user's information
        if current_user.role not in [UserRole.ADMIN, UserRole.CURATOR]:
            # Users can only see their own information
            if str(current_user.id) != user_id:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Access denied"
                )

        user = await user_service.get_user(UUID(user_id))
        if not user:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")

        return UserProfileResponse(user=UserPublic.from_user(user))
    except UserManagementError as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}",
        )


@users_router.put(
    "/{user_id}",
    response_model=UserProfileResponse,
    summary="Update user",
    description="Update user information (admin only)",
)
async def update_user(
    user_id: str,
    request: AdminUpdateUserRequest,
    current_user: User = Depends(get_current_active_user),
    user_service: UserManagementService = Depends(
        container.get_user_management_service
    ),
    authz_service: AuthorizationService = Depends(container.get_authorization_service),
) -> UserProfileResponse:
    """
    Update user information (administrative operation).
    """
    try:
        # Check permission
        from ..domain.value_objects.permission import Permission

        await authz_service.require_permission(
            current_user.id, Permission("user:update")
        )
        updated_user = await user_service.admin_update_user(UUID(user_id), request)
        return UserProfileResponse(user=UserPublic.from_user(updated_user))
    except UserNotFoundError:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")
    except ValueError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))
    except UserManagementError as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User update failed: {str(e)}",
        )


@users_router.delete(
    "/{user_id}",
    response_model=GenericSuccessResponse,
    summary="Delete user",
    description="Delete a user account (admin only)",
)
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    user_service: UserManagementService = Depends(
        container.get_user_management_service
    ),
    authz_service: AuthorizationService = Depends(container.get_authorization_service),
) -> GenericSuccessResponse:
    """
    Delete a user account (administrative operation).
    """
    try:
        # Check permission
        from ..domain.value_objects.permission import Permission

        await authz_service.require_permission(
            current_user.id, Permission("user:delete")
        )

        # Prevent users from deleting themselves
        if str(current_user.id) == user_id:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account",
            )

        await user_service.delete_user(UUID(user_id))
        return GenericSuccessResponse(message="User deleted successfully")
    except UserNotFoundError:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")
    except UserManagementError as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User deletion failed: {str(e)}",
        )


@users_router.post(
    "/{user_id}/lock",
    response_model=GenericSuccessResponse,
    summary="Lock user account",
    description="Lock a user account (admin only)",
)
async def lock_user_account(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    user_service: UserManagementService = Depends(
        container.get_user_management_service
    ),
    authz_service: AuthorizationService = Depends(container.get_authorization_service),
) -> GenericSuccessResponse:
    """
    Lock a user account (administrative operation).
    """
    try:
        # Check permission
        from ..domain.value_objects.permission import Permission

        await authz_service.require_permission(
            current_user.id, Permission("user:update")
        )

        # Prevent users from locking themselves
        if str(current_user.id) == user_id:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Cannot lock your own account",
            )

        await user_service.lock_user_account(UUID(user_id))
        return GenericSuccessResponse(message="User account locked successfully")
    except UserNotFoundError:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")
    except UserManagementError as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Account lock failed: {str(e)}",
        )


@users_router.post(
    "/{user_id}/unlock",
    response_model=GenericSuccessResponse,
    summary="Unlock user account",
    description="Unlock a user account (admin only)",
)
async def unlock_user_account(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    user_service: UserManagementService = Depends(
        container.get_user_management_service
    ),
    authz_service: AuthorizationService = Depends(container.get_authorization_service),
) -> GenericSuccessResponse:
    """
    Unlock a user account (administrative operation).
    """
    try:
        # Check permission
        from ..domain.value_objects.permission import Permission

        await authz_service.require_permission(
            current_user.id, Permission("user:update")
        )
        await user_service.unlock_user_account(UUID(user_id))
        return GenericSuccessResponse(message="User account unlocked successfully")
    except UserNotFoundError:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")
    except UserManagementError as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Account unlock failed: {str(e)}",
        )


@users_router.get(
    "/stats/overview",
    response_model=UserStatisticsResponse,
    summary="Get user statistics",
    description="Get comprehensive user statistics",
)
async def get_user_statistics(
    current_user: User = Depends(get_current_active_user),
    user_service: UserManagementService = Depends(
        container.get_user_management_service
    ),
) -> UserStatisticsResponse:
    """
    Get user statistics overview.
    """
    try:
        stats = await user_service.get_user_statistics()
        return stats
    except UserManagementError as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user statistics: {str(e)}",
        )


# Session management endpoints


@users_router.get(
    "/sessions",
    summary="Get user sessions",
    description="Get all active sessions for the current user",
)
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthenticationService = Depends(container.get_authentication_service),
) -> Dict[str, Any]:
    """
    Get all active sessions for the current user.
    """
    try:
        sessions = await auth_service.get_user_sessions(current_user.id)
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(e)}",
        )


@users_router.delete(
    "/sessions/{session_id}",
    response_model=GenericSuccessResponse,
    summary="Revoke user session",
    description="Revoke a specific user session",
)
async def revoke_user_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthenticationService = Depends(container.get_authentication_service),
) -> GenericSuccessResponse:
    """
    Revoke a specific user session.
    """
    try:
        from uuid import UUID

        session_uuid = UUID(session_id)

        await auth_service.revoke_user_session(current_user.id, session_uuid)
        return GenericSuccessResponse(message="Session revoked successfully")
    except ValueError:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Invalid session ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke session: {str(e)}",
        )


@users_router.delete(
    "/sessions",
    response_model=GenericSuccessResponse,
    summary="Revoke all user sessions",
    description="Revoke all sessions for the current user",
)
async def revoke_all_user_sessions(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthenticationService = Depends(container.get_authentication_service),
) -> GenericSuccessResponse:
    """
    Revoke all sessions for the current user.
    """
    try:
        count = await auth_service.revoke_all_user_sessions(current_user.id)
        return GenericSuccessResponse(
            message=f"All sessions revoked successfully ({count} sessions)"
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke sessions: {str(e)}",
        )
