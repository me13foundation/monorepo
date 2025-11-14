from __future__ import annotations

import os
from contextlib import contextmanager
from typing import TYPE_CHECKING

from schemathesis import openapi

if TYPE_CHECKING:
    from collections.abc import Iterator

    from schemathesis.schemas import APIOperation

from src.main import create_app


@contextmanager
def _temporary_skip_startup_tasks() -> Iterator[None]:
    original = os.environ.get("MED13_SKIP_STARTUP_TASKS")
    os.environ["MED13_SKIP_STARTUP_TASKS"] = "1"
    try:
        yield
    finally:
        if original is None:
            os.environ.pop("MED13_SKIP_STARTUP_TASKS", None)
        else:
            os.environ["MED13_SKIP_STARTUP_TASKS"] = original


with _temporary_skip_startup_tasks():
    schema = openapi.from_asgi("/openapi.json", create_app())


def _get_health_operation() -> APIOperation:
    for result in schema.get_all_operations():
        operation = result._value
        if operation.path == "/health/" and operation.method.upper() == "GET":
            return operation
    message = "Health operation not found in OpenAPI schema"
    raise AssertionError(message)


HEALTH_OPERATION: APIOperation = _get_health_operation()


def test_health_contract() -> None:
    """Run a deterministic schemathesis smoke test against the health endpoint."""
    with _temporary_skip_startup_tasks():
        case = schema.make_case(
            operation=HEALTH_OPERATION,
            method=HEALTH_OPERATION.method,
            path=HEALTH_OPERATION.path,
        )
        response = case.call()
        case.validate_response(response)
