"""
Common API schemas for MED13 Resource Library.

Shared Pydantic models for pagination, errors, and health checks.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for paginated endpoints."""

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: str | None = Field(None, description="Field to sort by")
    sort_order: str = Field(
        default="asc",
        pattern="^(asc|desc)$",
        description="Sort order",
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Response wrapper for paginated results."""

    model_config = ConfigDict(strict=True)

    items: list[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class ErrorDetail(BaseModel):
    """Detailed error information."""

    field: str | None = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: str | None = Field(None, description="Error code")


class ErrorResponse(BaseModel):
    """Standard error response format."""

    model_config = ConfigDict(strict=True)

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: list[ErrorDetail] | None = Field(
        None,
        description="Detailed error information",
    )
    request_id: str | None = Field(
        None,
        description="Request identifier for debugging",
    )


class HealthComponent(BaseModel):
    """Health status of a system component."""

    status: str = Field(
        ...,
        pattern="^(healthy|degraded|unhealthy)$",
        description="Component health status",
    )
    message: str | None = Field(None, description="Status message")
    details: dict[str, Any] | None = Field(None, description="Additional details")


class HealthResponse(BaseModel):
    """Health check response for the API."""

    model_config = ConfigDict(strict=True)

    status: str = Field(
        ...,
        pattern="^(healthy|degraded|unhealthy)$",
        description="Overall system health",
    )
    timestamp: str = Field(..., description="Health check timestamp")
    version: str = Field(..., description="API version")
    uptime: str | None = Field(None, description="System uptime")
    components: dict[str, HealthComponent] | None = Field(
        None,
        description="Component health statuses",
    )
