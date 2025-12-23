from __future__ import annotations

from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.infrastructure.observability.request_context import (
    REQUEST_ID_HEADER,
    build_audit_context,
    resolve_request_id,
)

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from fastapi import Request, Response
    from starlette.types import ASGIApp


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach request IDs and audit context to the request lifecycle."""

    def __init__(self, app: ASGIApp, header_name: str = REQUEST_ID_HEADER) -> None:
        super().__init__(app)
        self._header_name = header_name

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = resolve_request_id(request)
        request.state.request_id = request_id
        request.state.audit_context = build_audit_context(request)

        response = await call_next(request)

        if self._header_name not in response.headers:
            response.headers[self._header_name] = request_id

        return response


__all__ = ["RequestContextMiddleware"]
