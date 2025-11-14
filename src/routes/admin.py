"""
Backward-compatible entrypoint for admin routes.

The full implementation has been decomposed into modular routers under
``src.routes.admin_routes`` to keep responsibilities focused.
"""

from __future__ import annotations

from .admin_routes import router
from .admin_routes.dependencies import (
    DEFAULT_OWNER_ID,
    SYSTEM_ACTOR_ID,
    get_activation_service,
    get_auth_service,
    get_catalog_entry,
    get_db_session,
    get_source_service,
    get_template_service,
)

__all__ = [
    "DEFAULT_OWNER_ID",
    "SYSTEM_ACTOR_ID",
    "get_activation_service",
    "get_auth_service",
    "get_catalog_entry",
    "get_db_session",
    "get_source_service",
    "get_template_service",
    "router",
]
