from __future__ import annotations

from typing import Final
from uuid import uuid4

from fastapi import Request  # noqa: TC002 - Needed at runtime for FastAPI DI

from src.type_definitions.common import AuditContext  # noqa: TC001

REQUEST_ID_HEADER: Final[str] = "X-Request-ID"


def resolve_request_id(request: Request) -> str:
    """Resolve or generate a request ID for traceability."""
    header_id = request.headers.get(REQUEST_ID_HEADER)
    if header_id:
        return header_id

    state_id = getattr(request.state, "request_id", None)
    if isinstance(state_id, str) and state_id:
        return state_id

    return uuid4().hex


def build_audit_context(request: Request) -> AuditContext:
    """Build request metadata for audit logging."""
    request_id = resolve_request_id(request)
    forwarded_for = request.headers.get("x-forwarded-for")
    ip_address: str | None
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    else:
        ip_address = request.client.host if request.client else None

    return {
        "request_id": request_id,
        "ip_address": ip_address,
        "user_agent": request.headers.get("user-agent"),
        "method": request.method,
        "path": request.url.path,
    }


def _merge_audit_context(request: Request, state_context: object) -> AuditContext:
    context = build_audit_context(request)
    if not isinstance(state_context, dict):
        return context

    request_id = state_context.get("request_id")
    if isinstance(request_id, str) and request_id:
        context["request_id"] = request_id

    ip_address = state_context.get("ip_address")
    if (
        isinstance(ip_address, str) or ip_address is None
    ) and "ip_address" in state_context:
        context["ip_address"] = ip_address

    user_agent = state_context.get("user_agent")
    if (
        isinstance(user_agent, str) or user_agent is None
    ) and "user_agent" in state_context:
        context["user_agent"] = user_agent

    method = state_context.get("method")
    if isinstance(method, str) and method:
        context["method"] = method

    path = state_context.get("path")
    if isinstance(path, str) and path:
        context["path"] = path

    return context


def get_audit_context(request: Request) -> AuditContext:
    """FastAPI dependency to provide audit context."""
    state_context = getattr(request.state, "audit_context", None)
    return _merge_audit_context(request, state_context)


__all__ = ["REQUEST_ID_HEADER", "build_audit_context", "get_audit_context"]
