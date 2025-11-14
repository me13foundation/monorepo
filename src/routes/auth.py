"""
Authentication routes for MED13 Resource Library.

Provides REST API endpoints for user authentication, session management,
and user registration.
"""

import secrets
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.dto.auth_requests import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterUserRequest,
    ResetPasswordRequest,
    UpdateProfileRequest,
    UpdateUserRequest,
)
from src.application.dto.auth_responses import (
    ErrorResponse,
    GenericSuccessResponse,
    LoginResponse,
    TokenRefreshResponse,
    UserProfileResponse,
    UserPublic,
    ValidationErrorResponse,
)
from src.application.services.authentication_service import (
    AccountInactiveError,
    AccountLockedError,
    AuthenticationError,
    AuthenticationService,
    InvalidCredentialsError,
)
from src.application.services.authorization_service import (
    AuthorizationError,
    AuthorizationService,
)
from src.application.services.user_management_service import (
    UserAlreadyExistsError,
    UserManagementError,
    UserManagementService,
)
from src.domain.entities.user import User, UserRole, UserStatus
from src.domain.value_objects.permission import Permission
from src.infrastructure.dependency_injection.container import (
    container,
    get_authentication_service_dependency,
)
from src.infrastructure.security.password_hasher import PasswordHasher
from src.models.database.user import UserModel

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


@auth_router.get("/test")
async def test_endpoint() -> dict[str, str]:
    """Simple test endpoint to check if auth routes are working."""
    return {"message": "Auth routes are working!"}


@auth_router.get("/routes")
async def list_routes() -> dict[str, list[dict[str, Any]]]:
    """List all auth routes."""
    routes = [
        {
            "path": getattr(route, "path", str(route)),
            "methods": getattr(route, "methods", None),
            "name": getattr(route, "name", None),
        }
        for route in auth_router.routes
    ]
    return {"routes": routes}


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    auth_service: AuthenticationService = Depends(
        get_authentication_service_dependency,
    ),
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
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active",
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
    role: str,
    current_user: User = Depends(get_current_active_user),
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
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return current_user
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {role}",
        )


@auth_router.post(
    "/login",
    response_model=LoginResponse,
    summary="User login",
    description="Authenticate user with email and password",
)
async def login(
    request: LoginRequest,
    http_request: Request,
    auth_service: AuthenticationService = Depends(
        get_authentication_service_dependency,
    ),
) -> LoginResponse:
    """
    Authenticate user and return access/refresh tokens.
    """
    try:
        # Extract IP address and user agent from request
        ip_address = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("user-agent")

        # Use the actual authentication service
        response = await auth_service.authenticate_user(
            request,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return response
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AccountLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except AccountInactiveError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {e!s}",
        )


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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
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
        # TODO: Get token from request and revoke it via service
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
) -> GenericSuccessResponse:
    """
    Register a new user account.
    """
    try:
        # Create user directly using SQLAlchemy model
        password_hasher = PasswordHasher()

        # Create user model
        user = UserModel(
            email=request.email,
            username=request.username,
            full_name=request.full_name,
            hashed_password=password_hasher.hash_password(request.password),
            role=UserRole.VIEWER,
            status=UserStatus.PENDING_VERIFICATION,
            email_verification_token=secrets.token_urlsafe(32),
        )

        # Save to database
        session = container.async_session_factory()
        async with session:
            session.add(user)
            await session.commit()
            await session.refresh(user)

        # TODO: Send verification email in background

        return GenericSuccessResponse(
            message="User registered successfully. Please check your email for verification instructions.",
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserManagementError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {e!s}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {e!s}",
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
    return UserProfileResponse(user=UserPublic.from_user(current_user))


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
        container.get_user_management_service,
    ),
) -> UserProfileResponse:
    """
    Update current user's profile.
    """
    try:
        update_request = UpdateUserRequest(
            full_name=request.full_name,
            role=None,  # Users cannot change their own role
        )

        updated_user = await user_service.update_user(
            user_id=current_user.id,
            request=update_request,
            updated_by=current_user.id,
        )

        return UserProfileResponse(user=UserPublic.from_user(updated_user))
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
        container.get_user_management_service,
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
        container.get_user_management_service,
    ),
) -> GenericSuccessResponse:
    """
    Request password reset for user.
    """
    try:
        masked_email = await user_service.request_password_reset(request.email)

        # TODO: Send password reset email in background

        return GenericSuccessResponse(
            message=f"Password reset email sent to {masked_email}",
        )
    except UserManagementError:
        # Don't reveal if email exists or not for security
        return GenericSuccessResponse(
            message="If the email exists, a password reset link has been sent.",
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
        container.get_user_management_service,
    ),
) -> GenericSuccessResponse:
    """
    Reset user password using reset token.
    """
    try:
        await user_service.reset_password(
            token=request.token,
            new_password=request.new_password,
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
        container.get_user_management_service,
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )
