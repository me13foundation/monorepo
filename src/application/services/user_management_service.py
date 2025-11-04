"""
User management service for MED13 Resource Library.

Handles user lifecycle operations including registration, profile management, and administration.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone

from ...domain.entities.user import User, UserRole, UserStatus
from ...domain.repositories.user_repository import UserRepository
from ...infrastructure.security.password_hasher import PasswordHasher
from ..dto.auth_requests import (
    RegisterUserRequest,
    UpdateUserRequest,
    CreateUserRequest,
    AdminUpdateUserRequest,
)
from ..dto.auth_responses import UserPublic, UserListResponse, UserStatisticsResponse


class UserManagementError(Exception):
    """Base exception for user management errors."""

    pass


class UserAlreadyExistsError(UserManagementError):
    """Raised when attempting to create user that already exists."""

    pass


class UserNotFoundError(UserManagementError):
    """Raised when user doesn't exist."""

    pass


class InvalidPasswordError(UserManagementError):
    """Raised when password is invalid."""

    pass


class EmailVerificationError(UserManagementError):
    """Raised when email verification fails."""

    pass


class UserManagementService:
    """
    Service for managing user accounts and profiles.

    Handles user registration, updates, password management, and administrative operations.
    """

    def __init__(
        self, user_repository: UserRepository, password_hasher: PasswordHasher
    ):
        """
        Initialize user management service.

        Args:
            user_repository: User data access
            password_hasher: Password security
        """
        self.user_repository = user_repository
        self.password_hasher = password_hasher

    async def register_user(self, request: RegisterUserRequest) -> User:
        """
        Register a new user account.

        Args:
            request: Registration data

        Returns:
            Created user entity

        Raises:
            UserAlreadyExistsError: If email or username already exists
            ValueError: If password doesn't meet requirements
        """
        # Check for existing users
        if await self.user_repository.exists_by_email(request.email):
            raise UserAlreadyExistsError("User with this email already exists")

        if await self.user_repository.exists_by_username(request.username):
            raise UserAlreadyExistsError("User with this username already exists")

        # Validate password strength
        if not self.password_hasher.is_password_strong(request.password):
            raise ValueError("Password does not meet security requirements")

        # Create user
        user = User(
            email=request.email,
            username=request.username,
            full_name=request.full_name,
            hashed_password=self.password_hasher.hash_password(request.password),
            role=request.role,
            status=UserStatus.PENDING_VERIFICATION,
        )

        # Generate email verification token
        user.generate_email_verification_token()

        # Save user
        created_user = await self.user_repository.create(user)

        # TODO: Send verification email
        # await self.email_service.send_verification_email(created_user, user.email_verification_token)

        return created_user

    async def create_user(self, request: CreateUserRequest, created_by: UUID) -> User:
        """
        Create a user account (administrative operation).

        Args:
            request: User creation data
            created_by: ID of admin creating the user

        Returns:
            Created user entity

        Raises:
            UserAlreadyExistsError: If email or username already exists
        """
        # Check for existing users
        if await self.user_repository.exists_by_email(request.email):
            raise UserAlreadyExistsError("User with this email already exists")

        if await self.user_repository.exists_by_username(request.username):
            raise UserAlreadyExistsError("User with this username already exists")

        # Create user (admin-created users are active by default)
        user = User(
            email=request.email,
            username=request.username,
            full_name=request.full_name,
            hashed_password=self.password_hasher.hash_password(request.password),
            role=request.role,
            status=UserStatus.ACTIVE,
            email_verified=True,  # Admin-created users skip verification
        )

        return await self.user_repository.create(user)

    async def update_user(
        self,
        user_id: UUID,
        request: UpdateUserRequest,
        updated_by: Optional[UUID] = None,
    ) -> User:
        """
        Update user profile.

        Args:
            user_id: User to update
            request: Update data
            updated_by: ID of user making the update (for authorization)

        Returns:
            Updated user entity

        Raises:
            UserNotFoundError: If user doesn't exist
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")

        # Apply updates
        if request.full_name is not None:
            user.full_name = request.full_name

        if request.role is not None and updated_by:
            # Only admins can change roles
            admin_user = await self.user_repository.get_by_id(updated_by)
            if admin_user and admin_user.role == UserRole.ADMIN:
                user.role = request.role

        user.updated_at = datetime.utcnow()

        return await self.user_repository.update(user)

    async def admin_update_user(
        self, user_id: UUID, request: AdminUpdateUserRequest
    ) -> User:
        """
        Update user as administrator.

        Args:
            user_id: User to update
            request: Admin update data

        Returns:
            Updated user entity

        Raises:
            UserNotFoundError: If user doesn't exist
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")

        # Apply admin updates
        if request.full_name is not None:
            user.full_name = request.full_name

        if request.role is not None:
            user.role = request.role

        if request.status is not None:
            # Validate status
            try:
                user.status = UserStatus(request.status.lower())
            except ValueError:
                raise ValueError(f"Invalid status: {request.status}")

        user.updated_at = datetime.utcnow()

        return await self.user_repository.update(user)

    async def change_password(
        self, user_id: UUID, old_password: str, new_password: str
    ) -> None:
        """
        Change user's password.

        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password

        Raises:
            UserNotFoundError: If user doesn't exist
            InvalidPasswordError: If old password is incorrect
            ValueError: If new password doesn't meet requirements
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")

        # Verify old password
        if not self.password_hasher.verify_password(old_password, user.hashed_password):
            raise InvalidPasswordError("Current password is incorrect")

        # Validate new password
        if not self.password_hasher.is_password_strong(new_password):
            raise ValueError("New password does not meet security requirements")

        # Update password
        user.hashed_password = self.password_hasher.hash_password(new_password)
        user.updated_at = datetime.utcnow()

        await self.user_repository.update(user)

        # TODO: Send password changed notification
        # await self.email_service.send_password_changed_notification(user)

    async def request_password_reset(self, email: str) -> str:
        """
        Request password reset for user.

        Args:
            email: User's email address

        Returns:
            Masked email for confirmation

        Raises:
            UserNotFoundError: If user doesn't exist
        """
        user = await self.user_repository.get_by_email(email)
        if not user:
            # Return masked email even if user doesn't exist (security)
            return self._mask_email(email)

        # Generate reset token
        user.generate_password_reset_token()
        await self.user_repository.update(user)

        # TODO: Send password reset email
        # await self.email_service.send_password_reset_email(user, user.password_reset_token)

        return self._mask_email(email)

    async def reset_password(self, token: str, new_password: str) -> None:
        """
        Reset password using reset token.

        Args:
            token: Password reset token
            new_password: New password

        Raises:
            ValueError: If token is invalid or expired
            ValueError: If password doesn't meet requirements
        """
        # Find user with this token
        # Note: This is inefficient - in production, you'd want a token index
        # For now, we'll iterate through users (not recommended for large datasets)

        # TODO: Implement proper token lookup in repository
        # For now, this is a placeholder implementation
        users = await self.user_repository.list_all()
        user = None
        for u in users:
            if (
                u.password_reset_token == token
                and u.password_reset_expires
                and u.password_reset_expires > datetime.now(timezone.utc)
            ):
                user = u
                break

        if not user:
            raise ValueError("Invalid or expired reset token")

        # Validate password
        if not self.password_hasher.is_password_strong(new_password):
            raise ValueError("Password does not meet security requirements")

        # Update password and clear reset token
        user.hashed_password = self.password_hasher.hash_password(new_password)
        user.clear_password_reset_token()
        user.updated_at = datetime.now(timezone.utc)

        await self.user_repository.update(user)

        # Revoke all sessions for security
        # TODO: await self.session_repository.revoke_all_user_sessions(user.id)

        # TODO: Send confirmation email
        # await self.email_service.send_password_reset_confirmation(user)

    async def verify_email(self, token: str) -> None:
        """
        Verify user's email address.

        Args:
            token: Email verification token

        Raises:
            EmailVerificationError: If token is invalid
        """
        # Find user with this token
        # TODO: Implement proper token lookup

        user = None  # Placeholder
        if not user or user.email_verification_token != token:
            raise EmailVerificationError("Invalid verification token")

        # Verify email
        user.mark_email_verified()
        await self.user_repository.update(user)

        # TODO: Send welcome email
        # await self.email_service.send_welcome_email(user)

    async def delete_user(self, user_id: UUID) -> None:
        """
        Delete a user account.

        Args:
            user_id: User to delete

        Raises:
            UserNotFoundError: If user doesn't exist
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")

        # TODO: Soft delete instead of hard delete for compliance
        # user.status = UserStatus.DELETED
        # await self.user_repository.update(user)

        # For now, hard delete
        await self.user_repository.delete(user_id)

        # TODO: Clean up related data (sessions, audit logs)
        # await self.session_repository.revoke_all_user_sessions(user_id)

    async def get_user(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User entity or None
        """
        return await self.user_repository.get_by_id(user_id)

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
    ) -> UserListResponse:
        """
        List users with filtering and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            role: Filter by role
            status: Filter by status

        Returns:
            Paginated user list response
        """
        users = await self.user_repository.list_users(
            skip=skip, limit=limit, role=role.value if role else None, status=status
        )

        total = await self.user_repository.count_users(
            role=role.value if role else None, status=status
        )

        return UserListResponse(
            users=[UserPublic.from_user(user) for user in users],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_user_statistics(self) -> UserStatisticsResponse:
        """
        Get comprehensive user statistics.

        Returns:
            User statistics response
        """
        # Count by status
        active_count = await self.user_repository.count_users_by_status(
            UserStatus.ACTIVE
        )
        inactive_count = await self.user_repository.count_users_by_status(
            UserStatus.INACTIVE
        )
        suspended_count = await self.user_repository.count_users_by_status(
            UserStatus.SUSPENDED
        )
        pending_count = await self.user_repository.count_users_by_status(
            UserStatus.PENDING_VERIFICATION
        )

        total_users = active_count + inactive_count + suspended_count + pending_count

        # Count by role
        role_counts = {}
        for role in UserRole:
            count = await self.user_repository.count_users(role=role.value)
            role_counts[role.value] = count

        # Recent activity (simplified - would need proper date filtering)
        recent_registrations = 0  # TODO: Implement date-based queries
        recent_logins = 0  # TODO: Implement date-based queries

        return UserStatisticsResponse(
            total_users=total_users,
            active_users=active_count,
            inactive_users=inactive_count,
            suspended_users=suspended_count,
            pending_verification=pending_count,
            by_role=role_counts,
            recent_registrations=recent_registrations,
            recent_logins=recent_logins,
        )

    async def lock_user_account(
        self, user_id: UUID, reason: str = "Administrative action"
    ) -> None:
        """
        Lock a user account.

        Args:
            user_id: User to lock
            reason: Reason for locking
        """
        await self.user_repository.lock_account(
            user_id,
            datetime.utcnow() + timedelta(days=30),  # 30 day lock
        )

        # TODO: Log security event
        # TODO: Send notification email

    async def unlock_user_account(self, user_id: UUID) -> None:
        """
        Unlock a user account.

        Args:
            user_id: User to unlock
        """
        await self.user_repository.unlock_account(user_id)

        # TODO: Log security event
        # TODO: Send notification email

    def _mask_email(self, email: str) -> str:
        """
        Mask email address for privacy.

        Args:
            email: Email to mask

        Returns:
            Masked email (e.g., "u***@example.com")
        """
        try:
            local, domain = email.split("@", 1)
            if len(local) > 2:
                masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
            else:
                masked_local = local[0] + "*" * (len(local) - 1)

            return f"{masked_local}@{domain}"
        except Exception:
            return "***@***.***"
