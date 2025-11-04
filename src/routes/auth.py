"""
Authentication routes for MED13 Resource Library.

Provides REST API endpoints for user authentication, session management,
and user registration.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..application.container import container
from ..application.services.authentication_service import (
    AuthenticationService,
    AuthenticationError,
    InvalidCredentialsError,
    AccountLockedError,
    AccountInactiveError,
)
from ..application.services.authorization_service import (
    AuthorizationService,
    AuthorizationError,
)
from ..application.services.user_management_service import (
    UserManagementService,
    UserManagementError,
    UserAlreadyExistsError,
)
from ..application.exceptions import (
    InvalidCredentialsException,
    AccountLockedException,
    AccountInactiveException,
    AuthenticationException,
)
from ..application.dto.auth_requests import (
    LoginRequest,
    RegisterUserRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UpdateProfileRequest,
)
from ..application.dto.auth_responses import (
    LoginResponse,
    TokenRefreshResponse,
    UserProfileResponse,
    GenericSuccessResponse,
    ErrorResponse,
    ValidationErrorResponse,
)
from ..domain.entities.user import User, UserRole


# Create router
auth_router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        422: {"model": ValidationErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthenticationService = Depends(container.get_authentication_service),
) -> User:
    """
    FastAPI dependency to get the current authenticated user.

    Raises HTTPException if authentication fails.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await auth_service.validate_token(credentials.credentials)
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    FastAPI dependency to get the current active user.

    Ensures the user account is active.
    """
    if not current_user.can_authenticate():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active"
        )
    return current_user


async def require_permission(
    permission: str,
    current_user: User = Depends(get_current_active_user),
    authz_service: AuthorizationService = Depends(container.get_authorization_service),
) -> User:
    """
    FastAPI dependency to require specific permission.

    Args:
        permission: Required permission string (e.g., "user:create")
        current_user: Current authenticated user
        authz_service: Authorization service

    Returns:
        User if permission granted

    Raises:
        HTTPException if permission denied
    """
    from ..domain.value_objects.permission import Permission

    try:
        # Convert string to Permission enum
        perm_enum = Permission(permission)
        await authz_service.require_permission(current_user.id, perm_enum)
        return current_user
    except (ValueError, AuthorizationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission}",
        )


async def require_role(
    role: str, current_user: User = Depends(get_current_active_user)
) -> User:
    """
    FastAPI dependency to require specific role.

    Args:
        role: Required role string (e.g., "admin")
        current_user: Current authenticated user

    Returns:
        User if role matches

    Raises:
        HTTPException if role doesn't match
    """
    try:
        required_role = UserRole(role.lower())
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"Role '{role}' required"
            )
        return current_user
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role: {role}"
        )


@auth_router.post(
    "/login",
    response_model=LoginResponse,
    summary="User login",
    description="Authenticate user with email and password",
)
async def login(
    request: LoginRequest,
    auth_service: AuthenticationService = Depends(container.get_authentication_service),
) -> LoginResponse:
    """
    Authenticate user and return access/refresh tokens.
    """
    try:
        response = await auth_service.authenticate_user(
            request=request,
            ip_address=None,  # TODO: Get from request
            user_agent=None,  # TODO: Get from request
        )
        return response
    except InvalidCredentialsError:
        raise InvalidCredentialsException()
    except AccountLockedError:
        raise AccountLockedException()
    except AccountInactiveError:
        raise AccountInactiveException()
    except AuthenticationError as e:
        raise AuthenticationException(f"Authentication failed: {str(e)}")


@auth_router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    summary="Refresh access token",
    description="Get new access token using refresh token",
)
async def refresh_token(
    refresh_token: str,
    auth_service: AuthenticationService = Depends(container.get_authentication_service),
) -> TokenRefreshResponse:
    """
    Refresh access token using valid refresh token.
    """
    try:
        response = await auth_service.refresh_token(refresh_token)
        return response
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )


@auth_router.post(
    "/logout",
    response_model=GenericSuccessResponse,
    summary="User logout",
    description="Revoke current session",
)
async def logout(
    current_user: User = Depends(get_current_user),
    auth_service: AuthenticationService = Depends(container.get_authentication_service),
) -> GenericSuccessResponse:
    """
    Logout user by revoking their session.
    """
    try:
        # TODO: Get token from request
        # await auth_service.logout(access_token)
        return GenericSuccessResponse(message="Logged out successfully")
    except AuthenticationError:
        # Even if logout fails, we return success for security
        return GenericSuccessResponse(message="Logged out successfully")


@auth_router.post(
    "/register",
    response_model=GenericSuccessResponse,
    summary="User registration",
    description="Register a new user account",
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    request: RegisterUserRequest,
    background_tasks: BackgroundTasks,
    user_service: UserManagementService = Depends(
        container.get_user_management_service
    ),
) -> GenericSuccessResponse:
    """
    Register a new user account.
    """
    try:
        await user_service.register_user(request)

        # TODO: Send verification email in background
        # user = await user_service.get_user_by_email(request.email)
        # background_tasks.add_task(send_verification_email, user)

        return GenericSuccessResponse(
            message="User registered successfully. Please check your email for verification instructions."
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserManagementError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@auth_router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user profile",
    description="Get detailed information about the current user",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserProfileResponse:
    """
    Get current user's profile information.
    """
    return UserProfileResponse(user=current_user)


@auth_router.put(
    "/me",
    response_model=UserProfileResponse,
    summary="Update user profile",
    description="Update current user's profile information",
)
async def update_user_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_active_user),
    user_service: UserManagementService = Depends(
        container.get_user_management_service
    ),
) -> UserProfileResponse:
    """
    Update current user's profile.
    """
    try:
        from ..application.dto.auth_requests import UpdateUserRequest

        update_request = UpdateUserRequest(
            full_name=request.full_name,
            role=None,  # Users cannot change their own role
        )

        updated_user = await user_service.update_user(
            user_id=current_user.id, request=update_request, updated_by=current_user.id
        )

        return UserProfileResponse(user=updated_user)
    except UserManagementError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@auth_router.post(
    "/me/change-password",
    response_model=GenericSuccessResponse,
    summary="Change password",
    description="Change current user's password",
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    user_service: UserManagementService = Depends(
        container.get_user_management_service
    ),
) -> GenericSuccessResponse:
    """
    Change current user's password.
    """
    try:
        await user_service.change_password(
            user_id=current_user.id,
            old_password=request.old_password,
            new_password=request.new_password,
        )

        # TODO: Send confirmation email
        # background_tasks.add_task(send_password_changed_email, current_user)

        return GenericSuccessResponse(message="Password changed successfully")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserManagementError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@auth_router.post(
    "/forgot-password",
    response_model=GenericSuccessResponse,
    summary="Request password reset",
    description="Send password reset email to user",
)
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    user_service: UserManagementService = Depends(
        container.get_user_management_service
    ),
) -> GenericSuccessResponse:
    """
    Request password reset for user.
    """
    try:
        masked_email = await user_service.request_password_reset(request.email)

        # TODO: Send password reset email in background
        # background_tasks.add_task(send_password_reset_email, request.email)

        return GenericSuccessResponse(
            message=f"Password reset email sent to {masked_email}"
        )
    except UserManagementError:
        # Don't reveal if email exists or not for security
        return GenericSuccessResponse(
            message="If the email exists, a password reset link has been sent."
        )


@auth_router.post(
    "/reset-password",
    response_model=GenericSuccessResponse,
    summary="Reset password",
    description="Reset user password using reset token",
)
async def reset_password(
    request: ResetPasswordRequest,
    user_service: UserManagementService = Depends(
        container.get_user_management_service
    ),
) -> GenericSuccessResponse:
    """
    Reset user password using reset token.
    """
    try:
        await user_service.reset_password(
            token=request.token, new_password=request.new_password
        )

        return GenericSuccessResponse(message="Password reset successfully")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserManagementError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired reset token",
        )


@auth_router.post(
    "/verify-email/{token}",
    response_model=GenericSuccessResponse,
    summary="Verify email address",
    description="Verify user email using verification token",
)
async def verify_email(
    token: str,
    user_service: UserManagementService = Depends(
        container.get_user_management_service
    ),
) -> GenericSuccessResponse:
    """
    Verify user email address using token.
    """
    try:
        await user_service.verify_email(token)
        return GenericSuccessResponse(message="Email verified successfully")
    except UserManagementError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token"
        )
