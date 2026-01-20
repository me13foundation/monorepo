"""
State backend management for Flujo.

Provides thread-safe singleton management of the Flujo state backend
to ensure consistent state handling across the application.
"""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING

from flujo.application.core.runtime.factories import BackendFactory

from src.infrastructure.llm.config.flujo_config import resolve_flujo_state_uri

if TYPE_CHECKING:
    from flujo.state.backends.base import StateBackend

logger = logging.getLogger(__name__)


@dataclass
class _StateBackendHolder:
    """Thread-safe holder for the state backend singleton."""

    value: StateBackend | None = None


_STATE_BACKEND_LOCK = threading.Lock()
_STATE_BACKEND_HOLDER = _StateBackendHolder()
_STATE_BACKEND_FACTORY = BackendFactory()


def _build_state_backend() -> StateBackend:
    """Build a new state backend instance."""
    state_uri = resolve_flujo_state_uri()
    os.environ["FLUJO_STATE_URI"] = state_uri
    logger.info("Initializing Flujo state backend with URI: %s", _mask_uri(state_uri))
    return _STATE_BACKEND_FACTORY.create_state_backend()


def _mask_uri(uri: str) -> str:
    """Mask sensitive parts of the URI for logging."""
    if "://" not in uri or "@" not in uri:
        return uri

    # Mask password in postgresql://user:pass@host/db
    scheme, _, rest = uri.partition("://")
    if not rest or "@" not in rest:
        return uri

    auth_part, _, host_part = rest.rpartition("@")
    if ":" in auth_part:
        user = auth_part.split(":")[0]
        return f"{scheme}://{user}:***@{host_part}"

    return uri


def get_state_backend() -> StateBackend:
    """
    Get the singleton state backend instance.

    Thread-safe lazy initialization ensures only one backend
    is created regardless of concurrent access.

    Returns:
        The shared StateBackend instance
    """
    existing = _STATE_BACKEND_HOLDER.value
    if existing is not None:
        return existing

    with _STATE_BACKEND_LOCK:
        existing = _STATE_BACKEND_HOLDER.value
        if existing is None:
            existing = _build_state_backend()
            _STATE_BACKEND_HOLDER.value = existing
        return existing


def reset_state_backend() -> None:
    """
    Reset the state backend singleton.

    Use for testing or when reconfiguring the backend.
    Should not be called during normal operation.
    """
    with _STATE_BACKEND_LOCK:
        _STATE_BACKEND_HOLDER.value = None


class StateBackendManager:
    """
    Manager for Flujo state backend with lifecycle support.

    Provides explicit lifecycle management for the state backend
    to ensure proper cleanup during application shutdown.
    """

    def __init__(self) -> None:
        """Initialize the manager."""
        self._backend: StateBackend | None = None

    @property
    def backend(self) -> StateBackend:
        """
        Get the managed state backend.

        Lazily initializes the backend on first access.
        """
        if self._backend is None:
            self._backend = get_state_backend()
        return self._backend

    async def close(self) -> None:
        """
        Close the state backend and release resources.

        Should be called during application shutdown.
        """
        if self._backend is not None:
            try:
                # Attempt to close if the backend supports it
                if hasattr(self._backend, "close"):
                    await self._backend.close()
                elif hasattr(self._backend, "aclose"):
                    await self._backend.aclose()
            except (RuntimeError, OSError, ConnectionError) as exc:
                logger.warning("Error closing state backend: %s", exc)
            finally:
                self._backend = None
