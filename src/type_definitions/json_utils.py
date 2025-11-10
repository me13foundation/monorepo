"""
Helpers for working with JSON-like payloads in a type-safe way.

These utilities narrow `JSONValue` unions to concrete Python types so that
parsers and normalizers can operate without falling back to `Any`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .common import JSONObject, JSONValue  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import Iterable


def as_object(value: JSONValue | None) -> JSONObject:
    """Return the value as a JSON object or an empty dict when not a mapping."""
    if isinstance(value, dict):
        return value
    return {}


def as_list(value: JSONValue | None) -> list[JSONValue]:
    """Return the value as a JSON list or an empty list when not a list."""
    if isinstance(value, list):
        return value
    return []


def list_of_objects(value: JSONValue | None) -> list[JSONObject]:
    """Return a list containing only dict entries from the provided value."""
    return [item for item in as_list(value) if isinstance(item, dict)]


def list_of_strings(value: JSONValue | None) -> list[str]:
    """Return a list of stringified entries from the provided value."""
    result: list[str] = []
    for item in as_list(value):
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, (int, float)):
            result.append(str(item))
    return result


def as_str(value: JSONValue | None, *, fallback: str | None = None) -> str | None:
    """Return the value as a string if possible."""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return str(value)
    return fallback


def as_int(value: JSONValue | None) -> int | None:
    """Return the value as an integer when coercion is safe."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def as_float(value: JSONValue | None) -> float | None:
    """Return the value as a float when coercion is safe."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def extend_unique(collection: list[str], new_values: Iterable[str]) -> None:
    """Extend a list with new values while preserving uniqueness."""
    for value in new_values:
        if value not in collection:
            collection.append(value)
