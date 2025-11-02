"""
Authentication middleware for MED13 Resource Library API.

Implements API key-based authentication with role-based access control.
"""

import os
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class APIKeyAuth:
    """API key authentication handler."""

    def __init__(self) -> None:
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
        # In production, these would come from environment variables or a database
        self.valid_api_keys: Dict[str, str] = {
            os.getenv("ADMIN_API_KEY", "admin-key-123"): "admin",
            os.getenv("READ_API_KEY", "read-key-456"): "read",
            os.getenv("WRITE_API_KEY", "write-key-789"): "write",
        }

    async def authenticate(self, request: Request) -> Optional[str]:
        """
        Authenticate the request using API key.

        Returns the user role if authenticated, None otherwise.
        """
        api_key = await self.api_key_header(request)

        if not api_key:
            return None

        role = self.valid_api_keys.get(api_key)
        return role

    def require_role(self, required_role: str) -> Callable[[Request], Awaitable[str]]:
        """
        Create a dependency that requires a specific role.

        Usage: Depends(auth.require_role("admin"))
        """

        async def role_checker(request: Request) -> str:
            role = await self.authenticate(request)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key required",
                    headers={"WWW-Authenticate": "APIKey"},
                )

            # Role hierarchy: admin > write > read
            role_hierarchy = {"read": 1, "write": 2, "admin": 3}

            if role_hierarchy.get(role, 0) < role_hierarchy.get(required_role, 999):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {required_role}, Got: {role}",
                )

            return role

        return role_checker


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to handle authentication for all requests."""

    def __init__(
        self,
        app: Callable[..., Any],
        exclude_paths: Optional[List[str]] = None,
    ) -> None:
        super().__init__(app)
        self.auth = APIKeyAuth()
        self.exclude_paths: List[str] = exclude_paths or [
            "/health/",
            "/docs",
            "/openapi.json",
            "/",
        ]

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process each request through authentication middleware."""

        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # For read operations (GET), allow with any valid key
        # For write operations (POST, PUT, DELETE), require write or admin
        if request.method in ["POST", "PUT", "DELETE"]:
            required_role = "write"
        else:
            required_role = "read"

        role = await self.auth.authenticate(request)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
                headers={"WWW-Authenticate": "APIKey"},
            )

        # Check role permissions
        role_hierarchy = {"read": 1, "write": 2, "admin": 3}
        if role_hierarchy.get(role, 0) < role_hierarchy.get(required_role, 999):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_role}",
            )

        # Add user info to request state
        request.state.user_role = role

        response = await call_next(request)
        return response


# Global auth instance
auth = APIKeyAuth()
