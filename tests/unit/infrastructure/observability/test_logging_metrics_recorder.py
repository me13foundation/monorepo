"""
Tests for the LoggingStorageMetricsRecorder.
"""

import json
from datetime import UTC, datetime
from uuid import uuid4

from src.infrastructure.observability.logging_metrics_recorder import (
    LoggingStorageMetricsRecorder,
)
from src.type_definitions.storage import (
    StorageMetricEvent,
    StorageMetricEventType,
    StorageOperationStatus,
    StorageProviderName,
)


def test_records_event_to_logger(caplog) -> None:
    """Test that events are logged as structured JSON."""
    recorder = LoggingStorageMetricsRecorder()
    event_id = uuid4()
    config_id = uuid4()
    now = datetime.now(UTC)

    event = StorageMetricEvent(
        event_id=event_id,
        configuration_id=config_id,
        provider=StorageProviderName.LOCAL_FILESYSTEM,
        event_type=StorageMetricEventType.STORE,
        status=StorageOperationStatus.SUCCESS,
        duration_ms=150,
        metadata={"key": "test/file.txt"},
        emitted_at=now,
    )

    with caplog.at_level("INFO", logger="med13.metrics.storage"):
        recorder.record_event(event)

    assert len(caplog.records) == 1
    log_record = caplog.records[0]
    assert log_record.name == "med13.metrics.storage"

    payload = json.loads(log_record.message)
    assert payload["event_id"] == str(event_id)
    assert payload["metric_type"] == "storage_operation"
    assert payload["configuration_id"] == str(config_id)
    assert payload["provider"] == "local_filesystem"
    assert payload["operation"] == "store"
    assert payload["status"] == "success"
    assert payload["duration_ms"] == 150
    assert payload["metadata"] == {"key": "test/file.txt"}
    assert payload["timestamp"] == now.isoformat()
