"""
Runtime compatibility hooks for tests and local tooling.

Python <3.11 does not expose ``datetime.UTC``. Our codebase relies on the
standard name, so we polyfill it here before application modules import
``from datetime import UTC``. The ``sitecustomize`` module is automatically
imported by Python during startup, making this a safe central place for the
patch without touching every call site.
"""

from __future__ import annotations

import datetime as _datetime

if not hasattr(_datetime, "UTC"):
    _datetime.UTC = _datetime.timezone.utc  # type: ignore[attr-defined]  # noqa: UP017
