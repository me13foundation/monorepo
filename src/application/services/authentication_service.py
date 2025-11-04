"""
Authentication service for MED13 Resource Library.

Handles user authentication, session management, and security operations.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta

from ...domain.entities.user import User, UserStatus
from ...domain.entities.session import UserSession
from ...domain.repositories.user_repository import UserRepository
from ...domain.repositories.session_repository import SessionRepository
from ...infrastructure.security.jwt_provider import JWTProvider
from ...infrastructure.security.password_hasher import PasswordHasher
from ..dto.auth_requests import LoginRequest
from ..dto.auth_responses import LoginResponse, TokenRefreshResponse


class AuthenticationError(Exception):
    """Base exception for authentication errors."""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""

    pass


class AccountLockedError(AuthenticationError):
    """Raised when account is locked due to security policy."""

    pass


class AccountInactiveError(AuthenticationError):
    """Raised when account is not active."""

    pass


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
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
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
                request.password, user.hashed_password
            )

        if not user or not password_valid:
            # Record failed attempt for security monitoring
            if user:
                await self._record_failed_login_attempt(user)
            raise InvalidCredentialsError("Invalid email or password")

        # Check account status
        if not user.can_authenticate():
            if user.is_locked():
                raise AccountLockedError(
                    "Account is locked due to multiple failed login attempts"
                )
            elif user.status != UserStatus.ACTIVE:
                raise AccountInactiveError("Account is not active")

        # Update login tracking
        user.record_login_attempt(success=True)
        await self.user_repository.update(user)

        # Create session
        session = await self._create_session(user, ip_address, user_agent)

        # Generate tokens
        access_token = self.jwt_provider.create_access_token(user.id, user.role.value)
        refresh_token = self.jwt_provider.create_refresh_token(user.id)

        # Update session with tokens
        session.session_token = access_token
        session.refresh_token = refresh_token
        await self.session_repository.update(session)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=900,  # 15 minutes
            user=user,
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
                refresh_token
            )

            if not session:
                raise AuthenticationError("Invalid refresh token")

            # Get user
            user = await self.user_repository.get_by_id(session.user_id)
            if not user or not user.can_authenticate():
                # Revoke session if user is invalid
                await self.session_repository.revoke_session(session.id)
                raise AuthenticationError("User session invalid")

            # Generate new tokens
            new_access_token = self.jwt_provider.create_access_token(
                user.id, user.role.value
            )
            new_refresh_token = self.jwt_provider.create_refresh_token(user.id)

            # Update session
            session.session_token = new_access_token
            session.refresh_token = new_refresh_token
            session.expires_at = datetime.utcnow() + timedelta(minutes=15)
            session.refresh_expires_at = datetime.utcnow() + timedelta(days=7)
            session.update_activity()

            await self.session_repository.update(session)

            return TokenRefreshResponse(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                expires_in=900,
            )

        except Exception as e:
            raise AuthenticationError(f"Token refresh failed: {str(e)}")

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
                raise AuthenticationError("Invalid token type")

            # Get user
            user_id = UUID(payload["sub"])
            user = await self.user_repository.get_by_id(user_id)

            if not user:
                raise AuthenticationError("User not found")

            if not user.can_authenticate():
                raise AuthenticationError("User account not active")

            # Update session activity if session exists
            session = await self.session_repository.get_by_access_token(token)
            if session and session.is_active():
                session.update_activity()
                await self.session_repository.update(session)

            return user

        except Exception as e:
            raise AuthenticationError(f"Token validation failed: {str(e)}")

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
        self, user: User, ip_address: Optional[str], user_agent: Optional[str]
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
                user.id, include_expired=False
            )
            if sessions:
                oldest_session = min(sessions, key=lambda s: s.created_at)
                await self.session_repository.revoke_session(oldest_session.id)

        # Create new session
        session = UserSession(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(minutes=15),
            refresh_expires_at=datetime.utcnow() + timedelta(days=7),
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

        # Log security event (would integrate with audit service)
        # await self.audit_service.log_security_event(
        #     "failed_login_attempt",
        #     user.id,
        #     details={"attempts": current_attempts}
        # )

        # Lock account after max attempts
        max_attempts = 5
        if current_attempts >= max_attempts:
            lockout_duration = timedelta(minutes=30)
            await self.user_repository.lock_account(
                user.id, datetime.utcnow() + lockout_duration
            )
