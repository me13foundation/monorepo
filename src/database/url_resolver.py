"""
Database URL resolution helpers.

These utilities centralize how the application derives synchronous and
asynchronous SQLAlchemy URLs from environment variables. They let us
switch between SQLite and Postgres (or other engines) without touching
call sites throughout the codebase.
"""

from __future__ import annotations

import os

DEFAULT_SQLITE_SYNC_URL = "sqlite:///med13.db"


def resolve_sync_database_url() -> str:
    """Return the sync SQLAlchemy URL, defaulting to local SQLite."""
    return os.getenv("DATABASE_URL", DEFAULT_SQLITE_SYNC_URL)


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
        return async_override
    sync_url = resolve_sync_database_url()
    return to_async_database_url(sync_url)
