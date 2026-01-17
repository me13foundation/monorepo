"""Ingestion history endpoints for admin data sources."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.domain.entities.ingestion_job import IngestionJob
from src.domain.repositories.ingestion_job_repository import IngestionJobRepository
from src.routes.admin_routes.data_sources.schemas import (
    IngestionJobHistoryResponse,
    IngestionJobResponse,
)
from src.routes.admin_routes.dependencies import get_ingestion_job_repository

router = APIRouter()


def _job_to_response(job: IngestionJob) -> IngestionJobResponse:
    metrics = job.metrics
    return IngestionJobResponse(
        id=job.id,
        status=job.status,
        trigger=job.trigger,
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        records_processed=metrics.records_processed,
        records_failed=metrics.records_failed,
        records_skipped=metrics.records_skipped,
        bytes_processed=metrics.bytes_processed,
        metadata=job.metadata,
    )


@router.get(
    "/{source_id}/ingestion-jobs",
    response_model=IngestionJobHistoryResponse,
    summary="List recent ingestion jobs",
    description="Return recent ingestion job executions for the specified data source.",
)
def list_ingestion_jobs(
    source_id: UUID,
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Maximum number of jobs to return",
    ),
    repository: IngestionJobRepository = Depends(get_ingestion_job_repository),
) -> IngestionJobHistoryResponse:
    jobs = repository.find_by_source(source_id, limit=limit)
    return IngestionJobHistoryResponse(
        source_id=source_id,
        items=[_job_to_response(job) for job in jobs],
    )


__all__ = ["router"]
