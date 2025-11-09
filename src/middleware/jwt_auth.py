"""
JWT Authentication middleware for MED13 Resource Library.

Provides FastAPI middleware for JWT token validation and user authentication.
"""

import logging
from collections.abc import Awaitable, Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.application.container import container
from src.application.services.authentication_service import (
    AuthenticationError,
    AuthenticationService,
)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    JWT Authentication middleware for FastAPI.

    Automatically validates JWT tokens on protected routes and adds user context.
    """

    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: list[str] | None = None,
        auth_service: AuthenticationService | None = None,
    ) -> None:
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
            "/auth/test",
            "/auth/debug",
            "/auth/routes",
        ]
        self.auth_service = auth_service

    def _get_cors_headers(self, request: Request) -> dict[str, str]:
        """Get CORS headers for the request origin."""
        origin = request.headers.get("origin")
        cors_headers = {"WWW-Authenticate": "Bearer"}
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:8050",
            "http://localhost:8080",
            "https://med13foundation.org",
            "https://curate.med13foundation.org",
            "https://admin.med13foundation.org",
        ]
        if origin and origin in allowed_origins:
            cors_headers.update(
                {
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
                },
            )
        return cors_headers

    def _get_error_code(self, error_detail: str) -> str:
        """Determine error code from error detail."""
        error_lower = error_detail.lower()
        if "expired" in error_lower:
            return "AUTH_TOKEN_EXPIRED"
        if "invalid" in error_lower:
            return "AUTH_TOKEN_MALFORMED"
        if "offset-naive" in error_lower or "offset-aware" in error_lower:
            return "AUTH_TOKEN_DATETIME_ERROR"
        return "AUTH_TOKEN_INVALID"

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """
        Process each request through JWT authentication middleware.

        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler

        Returns:
            Response from next handler or authentication error
        """
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

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
                headers=self._get_cors_headers(request),
            )

        # Validate token
        logger = logging.getLogger(__name__)

        try:
            logger.debug(
                "[JWTAuthMiddleware] Validating token for path: %s",
                request.url.path,
            )
            logger.debug(
                "[JWTAuthMiddleware] Token (first 20 chars): %s...",
                token[:20] if token else None,
            )

            user = await self.auth_service.validate_token(token)
            logger.debug(
                "[JWTAuthMiddleware] Token validation successful for user: %s",
                user.id,
            )

            # Add user to request state for use in route handlers
            request.state.user = user
            request.state.token = token

        except AuthenticationError as e:
            error_detail = str(e)
            error_code = self._get_error_code(error_detail)

            # Log expected authentication failures at debug level (no traceback)
            # These are normal 401 responses for invalid/expired tokens
            logger.debug(
                "[JWTAuthMiddleware] Authentication failed: %s",
                error_detail,
            )

            if error_code == "AUTH_TOKEN_DATETIME_ERROR":
                logger.warning(
                    "[JWTAuthMiddleware] Datetime comparison error detected: %s",
                    error_detail,
                )

            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Authentication failed",
                    "detail": error_detail,
                    "code": error_code,
                },
                headers=self._get_cors_headers(request),
            )

        # Continue with request
        return await call_next(request)

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
        return any(path.startswith(exclude_path) for exclude_path in self.exclude_paths)

    def _extract_token(self, request: Request) -> str | None:
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
