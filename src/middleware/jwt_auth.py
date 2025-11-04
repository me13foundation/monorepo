"""
JWT Authentication middleware for MED13 Resource Library.

Provides FastAPI middleware for JWT token validation and user authentication.
"""

from typing import Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..application.container import container
from ..application.services.authentication_service import (
    AuthenticationService,
    AuthenticationError,
)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    JWT Authentication middleware for FastAPI.

    Automatically validates JWT tokens on protected routes and adds user context.
    """

    def __init__(
        self,
        app,
        exclude_paths: Optional[list[str]] = None,
        auth_service: Optional[AuthenticationService] = None,
    ):
        """
        Initialize JWT authentication middleware.

        Args:
            app: FastAPI application
            exclude_paths: List of paths to exclude from authentication
            auth_service: Authentication service instance
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/resources",
            "/curation",
            "/auth/login",
            "/auth/register",
            "/auth/forgot-password",
            "/auth/reset-password",
            "/auth/verify-email",
        ]
        self.auth_service = auth_service

    async def dispatch(self, request: Request, call_next):
        """
        Process each request through JWT authentication middleware.

        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler

        Returns:
            Response from next handler or authentication error
        """
        # Skip authentication for excluded paths
        if self._should_skip_auth(request.url.path):
            return await call_next(request)

        # Check if user is already authenticated by previous middleware
        # (either JWT user object or legacy API key role)
        if (hasattr(request.state, "user") and request.state.user is not None) or (
            hasattr(request.state, "user_role") and request.state.user_role is not None
        ):
            return await call_next(request)

        # Get authentication service
        if not self.auth_service:
            self.auth_service = await container.get_authentication_service()

        # Extract token from Authorization header
        token = self._extract_token(request)

        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Authentication required",
                    "detail": "No authentication token provided",
                    "code": "AUTH_TOKEN_MISSING",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Validate token
        try:
            user = await self.auth_service.validate_token(token)

            # Add user to request state for use in route handlers
            request.state.user = user
            request.state.token = token

        except AuthenticationError as e:
            error_detail = str(e)
            error_code = "AUTH_TOKEN_INVALID"

            if "expired" in error_detail.lower():
                error_code = "AUTH_TOKEN_EXPIRED"
            elif "invalid" in error_detail.lower():
                error_code = "AUTH_TOKEN_MALFORMED"

            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Authentication failed",
                    "detail": error_detail,
                    "code": error_code,
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Continue with request
        response = await call_next(request)
        return response

    def _should_skip_auth(self, path: str) -> bool:
        """
        Check if authentication should be skipped for this path.

        Args:
            path: Request path

        Returns:
            True if authentication should be skipped
        """
        # Check exact matches
        if path in self.exclude_paths:
            return True

        # Check path prefixes (for dynamic routes)
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True

        return False

    def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from request.

        Supports Bearer token in Authorization header.

        Args:
            request: FastAPI request object

        Returns:
            JWT token string or None if not found
        """
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        # Check for Bearer token format
        if not auth_header.startswith("Bearer "):
            return None

        # Extract token
        token = auth_header[7:].strip()  # Remove "Bearer " prefix

        if not token:
            return None

        return token
