"""
Global exception handlers for uniform API error responses.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.domain.services.storage_providers.errors import (
    StorageConnectionError,
    StorageOperationError,
    StorageQuotaError,
    StorageValidationError,
)

if TYPE_CHECKING:
    from src.type_definitions.common import ApiErrorResponse


async def storage_error_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle generic storage backend failures."""
    if not isinstance(exc, StorageOperationError | StorageConnectionError):
        msg = f"Unexpected exception type: {type(exc)!r}"
        raise TypeError(msg)
    response: ApiErrorResponse = {
        "success": False,
        "error_type": "storage_error",
        "message": str(exc),
        "details": None,
    }
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content=response,
    )


async def storage_quota_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle storage quota violations."""
    if not isinstance(exc, StorageQuotaError):
        msg = f"Unexpected exception type: {type(exc)!r}"
        raise TypeError(msg)
    response: ApiErrorResponse = {
        "success": False,
        "error_type": "storage_quota_exceeded",
        "message": str(exc),
        "details": None,
    }
    return JSONResponse(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        content=response,
    )


async def storage_validation_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle storage configuration validation errors."""
    if not isinstance(exc, StorageValidationError):
        msg = f"Unexpected exception type: {type(exc)!r}"
        raise TypeError(msg)
    response: ApiErrorResponse = {
        "success": False,
        "error_type": "storage_validation_error",
        "message": str(exc),
        "details": None,
    }
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers."""
    app.add_exception_handler(
        StorageOperationError,
        storage_error_handler,
    )
    app.add_exception_handler(
        StorageConnectionError,
        storage_error_handler,
    )
    app.add_exception_handler(
        StorageQuotaError,
        storage_quota_handler,
    )
    app.add_exception_handler(
        StorageValidationError,
        storage_validation_handler,
    )
