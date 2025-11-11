"""
Database URL resolution helpers.

These utilities centralize how the application derives synchronous and
asynchronous SQLAlchemy URLs from environment variables. They let us
switch between SQLite and Postgres (or other engines) without touching
call sites throughout the codebase.
"""

from __future__ import annotations

import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_ALLOWED_INSECURE_ENV = os.getenv("MED13_ALLOW_INSECURE_DEFAULTS") == "1"
_ENVIRONMENT = os.getenv("MED13_ENV", "development").lower()
_POSTGRES_PREFIXES = (
    "postgresql://",
    "postgresql+psycopg2://",
    "postgresql+psycopg://",
    "postgresql+asyncpg://",
)


def _validate_url_security(url: str) -> None:
    """Ensure we do not boot with insecure defaults in production-like environments."""
    if _ALLOWED_INSECURE_ENV:
        return
    if _ENVIRONMENT not in {"production", "staging"}:
        return

    insecure_markers = ("med13_dev_password", "sqlite:///med13.db")
    if any(marker in url for marker in insecure_markers):
        msg = (
            "Insecure default database credentials detected in a production/staging "
            "environment. Provide secure DATABASE_URL/ASYNC_DATABASE_URL values."
        )
        raise RuntimeError(msg)


def _enforce_tls_requirements(url: str) -> str:
    """
    Ensure TLS is required for Postgres connections in production-like environments.

    Adds sslmode=require when missing, unless insecure defaults are explicitly allowed.
    """
    if _ALLOWED_INSECURE_ENV or _ENVIRONMENT not in {"production", "staging"}:
        return url
    if not url.startswith(_POSTGRES_PREFIXES):
        return url

    split = urlsplit(url)
    query_items = parse_qsl(split.query, keep_blank_values=True)
    lowercase_keys = {key.lower() for key, _ in query_items}
    if "sslmode" not in lowercase_keys:
        query_items.append(("sslmode", "require"))
    rebuilt_query = urlencode(query_items, doseq=True)
    return urlunsplit(
        (
            split.scheme,
            split.netloc,
            split.path,
            rebuilt_query,
            split.fragment,
        ),
    )


DEFAULT_SQLITE_SYNC_URL = "sqlite:///med13.db"


def resolve_sync_database_url() -> str:
    """Return the sync SQLAlchemy URL, defaulting to local SQLite."""
    url = os.getenv("DATABASE_URL", DEFAULT_SQLITE_SYNC_URL)
    _validate_url_security(url)
    return _enforce_tls_requirements(url)


def to_async_database_url(sync_url: str) -> str:
    """
    Convert a synchronous SQLAlchemy URL into its async counterpart.

    Examples:
        sqlite:///db -> sqlite+aiosqlite:///db
        postgresql:// -> postgresql+asyncpg://
        postgresql+psycopg2:// -> postgresql+asyncpg://
    """
    passthrough_prefixes = ("sqlite+aiosqlite", "postgresql+asyncpg")
    if sync_url.startswith(passthrough_prefixes):
        return sync_url

    replacements = (
        ("sqlite://", "sqlite+aiosqlite://"),
        ("postgresql+psycopg2://", "postgresql+asyncpg://"),
        ("postgresql+psycopg://", "postgresql+asyncpg://"),
        ("postgresql://", "postgresql+asyncpg://"),
    )

    for prefix, replacement in replacements:
        if sync_url.startswith(prefix):
            return sync_url.replace(prefix, replacement, 1)

    return sync_url


def resolve_async_database_url() -> str:
    """Return the async SQLAlchemy URL, deriving from sync URL when needed."""
    async_override = os.getenv("ASYNC_DATABASE_URL")
    if async_override:
        _validate_url_security(async_override)
        return _enforce_tls_requirements(async_override)
    sync_url = resolve_sync_database_url()
    return to_async_database_url(sync_url)
