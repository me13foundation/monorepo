"""
Data source type definitions for MED13 Resource Library.

Provides typed contracts for data source testing results.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, Field


class DataSourceAiTestResult(BaseModel):
    """Result payload from testing an AI-managed data source configuration."""

    model_config = ConfigDict(extra="forbid")

    source_id: UUID
    success: bool
    message: str
    executed_query: str | None = None
    fetched_records: int = Field(ge=0)
    sample_size: int = Field(ge=1)
    checked_at: datetime


__all__ = ["DataSourceAiTestResult"]
