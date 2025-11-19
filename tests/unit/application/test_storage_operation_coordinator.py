from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from src.application.services.storage_configuration_service import (
    StorageConfigurationService,
)
from src.application.services.storage_operation_coordinator import (
    StorageOperationCoordinator,
)
from src.domain.entities.storage_configuration import StorageConfiguration
from src.domain.services.storage_providers import StoragePluginRegistry
from src.infrastructure.storage.providers.local_filesystem import (
    LocalFilesystemStorageProvider,
)
from src.type_definitions.storage import (
    LocalFilesystemConfig,
    StorageProviderCapability,
    StorageProviderName,
    StorageUseCase,
)


class DummyStorageConfigurationRepository:
    def __init__(self, configuration: StorageConfiguration | None):
        self._configuration = configuration

    def list_configurations(self, *, include_disabled: bool = False):
        del include_disabled
        return [self._configuration] if self._configuration else []

    def paginate_configurations(self, **kwargs):  # pragma: no cover - not required
        del kwargs
        return [], 0

    def create(self, configuration):  # pragma: no cover - not required
        return configuration

    def update(self, configuration):  # pragma: no cover - not required
        return configuration

    def get_by_id(self, configuration_id):  # pragma: no cover
        del configuration_id

    def delete(self, configuration_id):  # pragma: no cover
        del configuration_id
        return False


class DummyStorageOperationRepository:
    def __init__(self):
        self.operations = []

    def record_operation(self, operation):
        self.operations.append(operation)
        return operation

    def record_test_result(self, result):  # pragma: no cover
        del result
        raise NotImplementedError

    def list_operations(self, configuration_id, *, limit=100):  # pragma: no cover
        del configuration_id, limit
        return []

    def list_failed_store_operations(self, *, limit=100):
        del limit
        return []

    def get_usage_metrics(self, configuration_id):  # pragma: no cover
        del configuration_id

    def upsert_health_snapshot(self, snapshot):  # pragma: no cover
        del snapshot
        raise NotImplementedError

    def get_health_snapshot(self, configuration_id):  # pragma: no cover
        del configuration_id

    def update_operation_metadata(self, operation_id, metadata):
        for index, operation in enumerate(self.operations):
            if operation.id == operation_id:
                updated = operation.model_copy(update={"metadata": metadata})
                self.operations[index] = updated
                return updated
        message = "operation not found"
        raise ValueError(message)


def _make_configuration(base_path: str) -> StorageConfiguration:
    return StorageConfiguration(
        id=uuid4(),
        name="Local",
        provider=StorageProviderName.LOCAL_FILESYSTEM,
        config=LocalFilesystemConfig(
            provider=StorageProviderName.LOCAL_FILESYSTEM,
            base_path=base_path,
            create_directories=True,
            expose_file_urls=False,
        ),
        enabled=True,
        supported_capabilities=(StorageProviderCapability.PDF,),
        default_use_cases=(StorageUseCase.PDF,),
        metadata={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_store_for_use_case_requires_configuration(tmp_path):
    configuration = _make_configuration(str(tmp_path / "storage"))
    configuration_repository = DummyStorageConfigurationRepository(configuration)
    operation_repository = DummyStorageOperationRepository()
    registry = StoragePluginRegistry()
    registry.register(LocalFilesystemStorageProvider(), override=True)
    service = StorageConfigurationService(
        configuration_repository=configuration_repository,
        operation_repository=operation_repository,
        plugin_registry=registry,
    )
    coordinator = StorageOperationCoordinator(service)

    result = await coordinator.store_for_use_case(
        StorageUseCase.PDF,
        key="discovery/test.pdf",
        file_path=Path(__file__),
    )
    assert result.key == "discovery/test.pdf"


@pytest.mark.asyncio
async def test_store_for_use_case_raises_when_missing_configuration():
    service = StorageConfigurationService(
        configuration_repository=DummyStorageConfigurationRepository(None),
        operation_repository=DummyStorageOperationRepository(),
        plugin_registry=StoragePluginRegistry(),
    )
    coordinator = StorageOperationCoordinator(service)

    with pytest.raises(RuntimeError):
        await coordinator.store_for_use_case(
            StorageUseCase.PDF,
            key="missing.pdf",
            file_path=Path(__file__),
        )


@pytest.mark.asyncio
async def test_store_for_use_case_includes_metadata(tmp_path):
    configuration = _make_configuration(str(tmp_path / "storage"))
    configuration_repository = DummyStorageConfigurationRepository(configuration)
    operation_repository = DummyStorageOperationRepository()
    registry = StoragePluginRegistry()
    registry.register(LocalFilesystemStorageProvider(), override=True)
    service = StorageConfigurationService(
        configuration_repository=configuration_repository,
        operation_repository=operation_repository,
        plugin_registry=registry,
    )
    coordinator = StorageOperationCoordinator(service)

    metadata = {
        "use_case": StorageUseCase.PDF.value,
        "extra": "context",
    }
    result = await coordinator.store_for_use_case(
        StorageUseCase.PDF,
        key="discovery/test.pdf",
        file_path=Path(__file__),
        metadata=metadata,
    )

    assert result.metadata == metadata
    assert operation_repository.operations[-1].metadata == metadata
