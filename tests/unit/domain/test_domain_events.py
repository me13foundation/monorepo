from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

from src.domain.entities.user_data_source import (
    IngestionSchedule,
    SourceConfiguration,
    SourceStatus,
    SourceType,
    UserDataSource,
)
from src.domain.events import (
    SourceCreatedEvent,
    SourceStatusChangedEvent,
    domain_event_bus,
)


@pytest.fixture
def sample_source() -> UserDataSource:
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_file:
        tmp_path = tmp_file.name

    source = UserDataSource(
        id=uuid4(),
        owner_id=uuid4(),
        name="Test Source",
        source_type=SourceType.FILE_UPLOAD,
        configuration=SourceConfiguration(file_path=tmp_path),
        ingestion_schedule=IngestionSchedule(),
    )

    yield source

    Path(tmp_path).unlink(missing_ok=True)


def test_source_created_event_publishes_payload(sample_source: UserDataSource) -> None:
    events: list[str] = []

    def handler(event):
        events.append(event.payload["owner_id"])

    domain_event_bus.subscribe("source.created", handler)
    event = SourceCreatedEvent.from_source(sample_source)
    domain_event_bus.publish(event)

    assert events, "Expected handler to receive created event"
    assert events[0] == str(sample_source.owner_id)
    domain_event_bus.unsubscribe("source.created", handler)


def test_status_changed_event_includes_previous_state(
    sample_source: UserDataSource,
) -> None:
    transitions: list[tuple[str, str]] = []

    def handler(event):
        transitions.append((event.payload["from_status"], event.payload["to_status"]))

    domain_event_bus.subscribe("source.status_changed", handler)
    updated = sample_source.update_status(SourceStatus.ACTIVE)
    event = SourceStatusChangedEvent.from_source(
        updated,
        previous_status=SourceStatus.DRAFT,
    )
    domain_event_bus.publish(event)

    assert transitions == [("draft", "active")]
    domain_event_bus.unsubscribe("source.status_changed", handler)
