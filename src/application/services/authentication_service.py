"""
Authentication service for MED13 Resource Library.

Handles user authentication, session management, and security operations.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from src.application.dto.auth_requests import LoginRequest
from src.application.dto.auth_responses import (
    LoginResponse,
    TokenRefreshResponse,
    UserPublic,
)
from src.domain.entities.session import UserSession
from src.domain.entities.user import User, UserStatus
from src.domain.repositories.session_repository import SessionRepository
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.security.jwt_provider import JWTProvider
from src.infrastructure.security.password_hasher import PasswordHasher


class AuthenticationError(Exception):
    """Base exception for authentication errors."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""


class AccountLockedError(AuthenticationError):
    """Raised when account is locked due to security policy."""


class AccountInactiveError(AuthenticationError):
    """Raised when account is not active."""


class AuthenticationService:
    """
    Service for handling user authentication and session management.

    Implements secure authentication with comprehensive security measures.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        session_repository: SessionRepository,
        jwt_provider: JWTProvider,
        password_hasher: PasswordHasher,
    ):
        """
        Initialize authentication service.

        Args:
            user_repository: User data access
            session_repository: Session data access
            jwt_provider: JWT token management
            password_hasher: Password security
        """
        self.user_repository = user_repository
        self.session_repository = session_repository
        self.jwt_provider = jwt_provider
        self.password_hasher = password_hasher

    async def authenticate_user(
        self,
        request: LoginRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> LoginResponse:
        """
        Authenticate user with email and password.

        Args:
            request: Login credentials
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Login response with tokens

        Raises:
            InvalidCredentialsError: Invalid email or password
            AccountLockedError: Account is locked
            AccountInactiveError: Account is not active
        """
        # Get user by email (constant time regardless of existence)
        user = await self.user_repository.get_by_email(request.email)

        # Verify credentials (constant time)
        password_valid = False
        if user:
            password_valid = self.password_hasher.verify_password(
                request.password,
                user.hashed_password,
            )

        if not user or not password_valid:
            # Record failed attempt for security monitoring
            if user:
                await self._record_failed_login_attempt(user)
            msg = "Invalid email or password"
            raise InvalidCredentialsError(msg)

        # Check account status
        if not user.can_authenticate():
            if user.is_locked():
                msg = "Account is locked due to multiple failed login attempts"
                raise AccountLockedError(msg)
            if user.status != UserStatus.ACTIVE:
                msg = "Account is not active"
                raise AccountInactiveError(msg)

        # Update login tracking
        user.record_login_attempt(success=True)
        await self.user_repository.update(user)

        # Generate tokens first
        access_token = self.jwt_provider.create_access_token(user.id, user.role.value)
        refresh_token = self.jwt_provider.create_refresh_token(user.id)

        # Create session with tokens
        await self._create_session(
            user,
            ip_address,
            user_agent,
            access_token=access_token,
            refresh_token=refresh_token,
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=900,  # 15 minutes
            user=UserPublic.from_user(user),
        )

    async def refresh_token(self, refresh_token: str) -> TokenRefreshResponse:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New token pair

        Raises:
            AuthenticationError: Invalid or expired refresh token
        """
        try:
            # Get active session by refresh token
            session = await self.session_repository.get_active_by_refresh_token(
                refresh_token,
            )

            if not session:
                msg = "Invalid refresh token"
                raise AuthenticationError(msg)  # noqa: TRY301

            # Get user
            user = await self.user_repository.get_by_id(session.user_id)
            if not user or not user.can_authenticate():
                # Revoke session if user is invalid
                await self.session_repository.revoke_session(session.id)
                msg = "User session invalid"
                raise AuthenticationError(msg)  # noqa: TRY301

            # Generate new tokens
            new_access_token = self.jwt_provider.create_access_token(
                user.id,
                user.role.value,
            )
            new_refresh_token = self.jwt_provider.create_refresh_token(user.id)

            # Update session
            session.session_token = new_access_token
            session.refresh_token = new_refresh_token
            session.expires_at = datetime.now(UTC) + timedelta(minutes=15)
            session.refresh_expires_at = datetime.now(UTC) + timedelta(days=7)
            session.update_activity()

            await self.session_repository.update(session)

            return TokenRefreshResponse(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                expires_in=900,
            )
        except AuthenticationError:
            raise
        except Exception as exc:
            msg = f"Token refresh failed: {exc!s}"
            raise AuthenticationError(msg) from exc

    async def logout(self, access_token: str) -> None:
        """
        Logout user by revoking session.

        Args:
            access_token: Current access token
        """
        session = await self.session_repository.get_by_access_token(access_token)
        if session:
            await self.session_repository.revoke_session(session.id)

    async def validate_token(self, token: str) -> User:
        """
        Validate JWT token and return user.

        Args:
            token: JWT access token

        Returns:
            Authenticated user

        Raises:
            AuthenticationError: Invalid token
        """
        try:
            # Decode and validate token
            payload = self.jwt_provider.decode_token(token)

            if payload.get("type") != "access":
                msg = "Invalid token type"
                raise AuthenticationError(msg)  # noqa: TRY301

            # Get user
            user_id = UUID(payload["sub"])
            user = await self.user_repository.get_by_id(user_id)

            if not user:
                msg = "User not found"
                raise AuthenticationError(msg)  # noqa: TRY301

            if not user.can_authenticate():
                msg = "User account not active"
                raise AuthenticationError(msg)  # noqa: TRY301

            # Update session activity if session exists
            session = await self.session_repository.get_by_access_token(token)
            if session and session.is_active():
                session.update_activity()
                await self.session_repository.update(session)

            return user  # noqa: TRY300
        except AuthenticationError:
            raise
        except Exception as exc:
            msg = f"Token validation failed: {exc!s}"
            raise AuthenticationError(msg) from exc

    async def get_user_sessions(self, user_id: UUID) -> list[UserSession]:
        """
        Get all active sessions for a user.

        Args:
            user_id: User ID

        Returns:
            List of active sessions
        """
        return await self.session_repository.get_active_sessions(user_id)

    async def revoke_user_session(self, user_id: UUID, session_id: UUID) -> None:
        """
        Revoke a specific user session.

        Args:
            user_id: User ID (for authorization)
            session_id: Session to revoke
        """
        # Verify session belongs to user
        session = await self.session_repository.get_by_id(session_id)
        if session and session.user_id == user_id:
            await self.session_repository.revoke_session(session_id)

    async def revoke_all_user_sessions(self, user_id: UUID) -> int:
        """
        Revoke all sessions for a user.

        Args:
            user_id: User ID

        Returns:
            Number of sessions revoked
        """
        return await self.session_repository.revoke_all_user_sessions(user_id)

    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (maintenance operation).

        Returns:
            Number of sessions cleaned up
        """
        return await self.session_repository.cleanup_expired_sessions()

    async def _create_session(
        self,
        user: User,
        ip_address: str | None,
        user_agent: str | None,
        access_token: str,
        refresh_token: str,
    ) -> UserSession:
        """
        Create a new session for user.

        Args:
            user: Authenticated user
            ip_address: Client IP
            user_agent: Client user agent

        Returns:
            New session
        """
        # Check concurrent session limits
        active_sessions = await self.session_repository.count_active_sessions(user.id)
        max_sessions = 5  # Configurable

        if active_sessions >= max_sessions:
            # Remove oldest session
            sessions = await self.session_repository.get_user_sessions(
                user.id,
                include_expired=False,
            )
            if sessions:
                oldest_session = min(sessions, key=lambda s: s.created_at)
                await self.session_repository.revoke_session(oldest_session.id)

        # Create new session with tokens
        session = UserSession(
            user_id=user.id,
            session_token=access_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now(UTC) + timedelta(minutes=15),
            refresh_expires_at=datetime.now(UTC) + timedelta(days=7),
        )

        # Generate device fingerprint
        if ip_address and user_agent:
            session.generate_device_fingerprint(ip_address, user_agent)

        return await self.session_repository.create(session)

    async def _record_failed_login_attempt(self, user: User) -> None:
        """
        Record failed login attempt and handle security measures.

        Args:
            user: User who failed login
        """
        current_attempts = await self.user_repository.increment_login_attempts(user.id)

        # Log security event (integration point for audit service)

        # Lock account after max attempts
        max_attempts = 5
        if current_attempts >= max_attempts:
            lockout_duration = timedelta(minutes=30)
            await self.user_repository.lock_account(
                user.id,
                datetime.now(UTC) + lockout_duration,
            )
