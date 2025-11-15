"""Tests for the in-memory scheduler backend."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.domain.entities.user_data_source import IngestionSchedule, ScheduleFrequency
from src.infrastructure.scheduling import InMemoryScheduler


def _build_schedule(frequency: ScheduleFrequency) -> IngestionSchedule:
    return IngestionSchedule(
        enabled=True,
        frequency=frequency,
        start_time=datetime.now(UTC),
    )


def test_register_and_due_jobs() -> None:
    scheduler = InMemoryScheduler()
    schedule = _build_schedule(ScheduleFrequency.HOURLY)
    job = scheduler.register_job(uuid4(), schedule)

    # Not due immediately because start_time is now
    assert scheduler.get_due_jobs(as_of=datetime.now(UTC)) == []

    # One hour later job is due
    due = scheduler.get_due_jobs(
        as_of=datetime.now(UTC) + timedelta(hours=1, seconds=1),
    )
    assert len(due) == 1
    assert due[0].job_id == job.job_id


def test_get_job_returns_latest_metadata() -> None:
    scheduler = InMemoryScheduler()
    schedule = _build_schedule(ScheduleFrequency.HOURLY)
    job = scheduler.register_job(uuid4(), schedule)

    stored = scheduler.get_job(job.job_id)
    assert stored is not None
    assert stored.job_id == job.job_id


def test_cron_not_supported_in_memory() -> None:
    scheduler = InMemoryScheduler()
    schedule = IngestionSchedule(
        enabled=True,
        frequency=ScheduleFrequency.CRON,
        cron_expression="0 2 * * *",
    )

    with pytest.raises(NotImplementedError):
        scheduler.register_job(uuid4(), schedule)
