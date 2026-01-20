"""
Lifecycle management for Flujo runners.

Provides proper shutdown handling to drain connection pools
and prevent resource leaks in production deployments.
"""

from __future__ import annotations

import contextlib
import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing import Any

    from fastapi import FastAPI
    from flujo import Flujo

logger = logging.getLogger(__name__)


class FlujoLifecycleManager:
    """
    Manages Flujo runner lifecycle for FastAPI applications.

    Tracks registered runners and ensures proper cleanup
    during application shutdown.

    Usage:
        ```python
        manager = FlujoLifecycleManager()

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            yield
            await manager.shutdown()

        app = FastAPI(lifespan=lifespan)
        ```
    """

    def __init__(self) -> None:
        """Initialize the lifecycle manager."""
        self._runners: list[Flujo[Any, Any, Any]] = []
        self._closed: bool = False

    def register_runner(self, runner: Flujo[Any, Any, Any]) -> None:
        """
        Register a runner for lifecycle management.

        Args:
            runner: The Flujo runner to track
        """
        if self._closed:
            logger.warning(
                "Registering runner after shutdown. "
                "Runner may not be properly cleaned up.",
            )
        self._runners.append(runner)

    def unregister_runner(self, runner: Flujo[Any, Any, Any]) -> None:
        """
        Unregister a runner from lifecycle management.

        Args:
            runner: The Flujo runner to remove
        """
        with contextlib.suppress(ValueError):
            self._runners.remove(runner)

    async def shutdown(self) -> None:
        """
        Shutdown all registered runners.

        Drains connection pools and releases resources.
        Should be called during application shutdown.
        """
        if self._closed:
            logger.debug("Lifecycle manager already closed")
            return

        self._closed = True
        errors: list[Exception] = []

        for runner in self._runners:
            try:
                if hasattr(runner, "aclose"):
                    await runner.aclose()
            except (RuntimeError, OSError, ConnectionError) as exc:
                errors.append(exc)
                logger.exception("Error closing Flujo runner")

        self._runners.clear()

        if errors:
            logger.warning(
                "Encountered %d errors during shutdown. "
                "Some resources may not have been properly released.",
                len(errors),
            )

    @property
    def runner_count(self) -> int:
        """Return the number of registered runners."""
        return len(self._runners)

    @property
    def is_closed(self) -> bool:
        """Return whether the manager has been shut down."""
        return self._closed


# Global lifecycle manager instance
_global_lifecycle_manager: FlujoLifecycleManager | None = None


def get_lifecycle_manager() -> FlujoLifecycleManager:
    """
    Get the global lifecycle manager instance.

    Creates the manager on first access.
    """
    global _global_lifecycle_manager  # noqa: PLW0603
    if _global_lifecycle_manager is None:
        _global_lifecycle_manager = FlujoLifecycleManager()
    return _global_lifecycle_manager


@asynccontextmanager
async def flujo_lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """
    FastAPI lifespan context manager for Flujo cleanup.

    Usage:
        ```python
        from fastapi import FastAPI
        from src.infrastructure.llm.state.lifecycle import flujo_lifespan

        app = FastAPI(lifespan=flujo_lifespan)
        ```

    Args:
        app: The FastAPI application instance

    Yields:
        None
    """
    manager = get_lifecycle_manager()
    logger.info("Flujo lifecycle manager initialized")

    try:
        yield
    finally:
        logger.info(
            "Shutting down Flujo lifecycle manager (%d runners)",
            manager.runner_count,
        )
        await manager.shutdown()
        logger.info("Flujo lifecycle manager shutdown complete")
