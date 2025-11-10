"""
SQLite configuration helpers for local development.

These utilities harden our SQLite usage so concurrent FastAPI requests
can operate without hitting ``database is locked`` errors. We enable WAL
mode, relax synchronous durability for dev, and raise the busy timeout so
short-lived write contention resolves automatically.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any, TypeVar

from sqlalchemy import event
from sqlalchemy.exc import OperationalError

if TYPE_CHECKING:  # pragma: no cover - import only for typings
    from collections.abc import Callable

    from sqlalchemy.engine import Engine
else:  # pragma: no cover - runtime fallback type
    Engine = Any

logger = logging.getLogger(__name__)

DEFAULT_BUSY_TIMEOUT_MS = 5_000
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 0.1  # 100ms

T = TypeVar("T")


def configure_sqlite_engine(
    engine: Engine,
    *,
    busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
    synchronous_level: str = "NORMAL",
) -> None:
    """
    Attach PRAGMA configuration to an SQLAlchemy engine for SQLite.

    Args:
        engine: SQLAlchemy engine (sync engine for async usage)
        busy_timeout_ms: Busy timeout in milliseconds before raising ``OperationalError``
        synchronous_level: Synchronous mode value (e.g., ``OFF``, ``NORMAL``)
    """

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(
        dbapi_connection: Any,
        _: Any,  # pragma: no cover - signature required by SQLAlchemy
    ) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute(f"PRAGMA synchronous={synchronous_level};")
        cursor.execute(f"PRAGMA busy_timeout={busy_timeout_ms};")
        cursor.execute("PRAGMA journal_mode=WAL;")
        # Consume result row so journal_mode change persists
        cursor.fetchone()
        cursor.close()


def build_sqlite_connect_args(
    timeout_seconds: int = 5,
    *,
    include_thread_check: bool = True,
) -> dict[str, Any]:
    """
    Build default connection arguments for SQLite engines.

    Args:
        timeout_seconds: Number of seconds SQLite waits before raising a lock error.
        include_thread_check: Whether to set ``check_same_thread`` (sync driver only).
    """
    connect_args: dict[str, Any] = {"timeout": timeout_seconds}
    if include_thread_check:
        connect_args["check_same_thread"] = False
    return connect_args


def retry_on_sqlite_lock[T](
    operation: Callable[[], T],
    max_retries: int = MAX_RETRIES,
    initial_delay: float = INITIAL_RETRY_DELAY,
) -> T:
    """
    Retry a database operation on SQLite lock errors with exponential backoff.

    Args:
        operation: Callable that performs the database operation
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry

    Returns:
        Result of the operation

    Raises:
        OperationalError: If all retries fail or a non-lock error occurs
    """
    last_exception: Exception | None = None
    delay = initial_delay

    for attempt in range(max_retries + 1):
        try:
            return operation()
        except OperationalError as e:
            error_str = str(e.orig) if hasattr(e, "orig") else str(e)
            if "database is locked" not in error_str.lower():
                # Not a lock error, re-raise immediately
                raise

            last_exception = e

            if attempt < max_retries:
                logger.debug(
                    "SQLite lock detected, retrying in %.3fs (attempt %d/%d)",
                    delay,
                    attempt + 1,
                    max_retries + 1,
                )
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                logger.warning(
                    "SQLite lock error persisted after %d attempts",
                    max_retries + 1,
                )

    # All retries exhausted
    if last_exception:
        raise last_exception
    error_message = "Retry logic failed without exception"
    raise RuntimeError(error_message)
