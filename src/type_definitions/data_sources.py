"""
Data source type definitions for MED13 Resource Library.

Provides typed contracts for data source testing results.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, Field


class DataSourceAiTestLink(BaseModel):
    """Reference link to a finding surfaced during AI testing."""

    model_config = ConfigDict(extra="forbid")

    label: str
    url: str


class DataSourceAiTestFinding(BaseModel):
    """Lightweight finding record surfaced during AI test execution."""

    model_config = ConfigDict(extra="forbid")

    title: str
    pubmed_id: str | None = None
    doi: str | None = None
    pmc_id: str | None = None
    publication_date: str | None = None
    journal: str | None = None
    links: list[DataSourceAiTestLink] = Field(default_factory=list)


class DataSourceAiTestResult(BaseModel):
    """Result payload from testing an AI-managed data source configuration."""

    model_config = ConfigDict(extra="forbid")

    source_id: UUID
    model: str | None = None
    success: bool
    message: str
    executed_query: str | None = None
    search_terms: list[str] = Field(default_factory=list)
    fetched_records: int = Field(ge=0)
    sample_size: int = Field(ge=1)
    findings: list[DataSourceAiTestFinding] = Field(default_factory=list)
    checked_at: datetime


__all__ = [
    "DataSourceAiTestFinding",
    "DataSourceAiTestLink",
    "DataSourceAiTestResult",
]
