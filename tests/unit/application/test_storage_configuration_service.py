from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterable

from src.application.services.storage_configuration_service import (
    StorageConfigurationService,
)
from src.application.services.storage_configuration_validator import (
    StorageConfigurationValidator,
)
from src.domain.entities.storage_configuration import (
    StorageConfiguration,
    StorageHealthSnapshot,
    StorageOperation,
)
from src.domain.services.storage_providers import StoragePluginRegistry
from src.domain.services.storage_providers.errors import StorageValidationError
from src.type_definitions.storage import (
    LocalFilesystemConfig,
    StorageHealthReport,
    StorageHealthStatus,
    StorageOperationRecord,
    StorageProviderCapability,
    StorageProviderName,
    StorageProviderTestResult,
    StorageUsageMetrics,
    StorageUseCase,
)


class FakeConfigurationRepository:
    def __init__(self, configurations: list[StorageConfiguration]):
        self._configurations = configurations

    def create(self, configuration: StorageConfiguration) -> StorageConfiguration:
        self._configurations.append(configuration)
        return configuration

    def update(self, configuration: StorageConfiguration) -> StorageConfiguration:
        for index, current in enumerate(self._configurations):
            if current.id == configuration.id:
                self._configurations[index] = configuration
                return configuration
        msg = "Configuration not found"
        raise ValueError(msg)

    def get_by_id(self, configuration_id: UUID) -> StorageConfiguration | None:
        return next(
            (
                config
                for config in self._configurations
                if config.id == configuration_id
            ),
            None,
        )

    def list_configurations(
        self,
        *,
        include_disabled: bool = False,
    ) -> list[StorageConfiguration]:
        if include_disabled:
            return list(self._configurations)
        return [config for config in self._configurations if config.enabled]

    def delete(self, configuration_id: UUID) -> bool:  # pragma: no cover - not used
        del configuration_id
        return False


class FakeOperationRepository:
    def __init__(
        self,
        usage: dict[UUID, StorageUsageMetrics],
        health: dict[UUID, StorageHealthSnapshot],
    ):
        self._usage = usage
        self._health = health

    def record_operation(
        self,
        operation: StorageOperation,
    ) -> StorageOperationRecord:  # pragma: no cover
        raise NotImplementedError

    def list_operations(
        self,
        configuration_id: UUID,
        *,
        limit: int = 100,
    ) -> list[StorageOperationRecord]:  # pragma: no cover
        raise NotImplementedError

    def upsert_health_snapshot(
        self,
        snapshot: StorageHealthSnapshot,
    ) -> StorageHealthSnapshot:  # pragma: no cover
        raise NotImplementedError

    def get_health_snapshot(
        self,
        configuration_id: UUID,
    ) -> StorageHealthSnapshot | None:
        return self._health.get(configuration_id)

    def record_test_result(
        self,
        result: StorageProviderTestResult,
    ) -> StorageProviderTestResult:  # pragma: no cover
        raise NotImplementedError

    def get_usage_metrics(
        self,
        configuration_id: UUID,
    ) -> StorageUsageMetrics | None:
        return self._usage.get(configuration_id)


def _create_configuration(
    *,
    name: str,
    enabled: bool,
    use_cases: Iterable[StorageUseCase],
) -> StorageConfiguration:
    config = LocalFilesystemConfig(
        provider=StorageProviderName.LOCAL_FILESYSTEM,
        base_path="/var/med13/storage",
        create_directories=True,
        expose_file_urls=False,
    )
    return StorageConfiguration(
        id=uuid4(),
        name=name,
        provider=StorageProviderName.LOCAL_FILESYSTEM,
        config=config,
        enabled=enabled,
        supported_capabilities=(StorageProviderCapability.PDF,),
        default_use_cases=tuple(use_cases),
        metadata={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def test_validator_prevents_duplicate_use_cases() -> None:
    repository = FakeConfigurationRepository(
        [
            _create_configuration(
                name="Primary",
                enabled=True,
                use_cases=[StorageUseCase.PDF],
            ),
        ],
    )
    validator = StorageConfigurationValidator()
    with pytest.raises(StorageValidationError):
        validator.ensure_use_case_exclusivity(
            repository,
            provider=StorageProviderName.LOCAL_FILESYSTEM,
            use_cases={StorageUseCase.PDF},
        )


def test_get_overview_returns_aggregated_stats() -> None:
    config_enabled = _create_configuration(
        name="Enabled",
        enabled=True,
        use_cases=[StorageUseCase.PDF],
    )
    config_disabled = _create_configuration(
        name="Disabled",
        enabled=False,
        use_cases=[StorageUseCase.EXPORT],
    )
    config_repo = FakeConfigurationRepository([config_enabled, config_disabled])
    usage_metrics = StorageUsageMetrics(
        configuration_id=config_enabled.id,
        total_files=10,
        total_size_bytes=2048,
        last_operation_at=datetime.now(UTC),
        error_rate=0.1,
    )
    health_snapshot = StorageHealthSnapshot(
        configuration_id=config_enabled.id,
        provider=StorageProviderName.LOCAL_FILESYSTEM,
        status=StorageHealthStatus.HEALTHY,
        last_checked_at=datetime.now(UTC),
        details={},
    )
    operation_repo = FakeOperationRepository(
        usage={config_enabled.id: usage_metrics},
        health={config_enabled.id: health_snapshot},
    )
    service = StorageConfigurationService(
        configuration_repository=config_repo,
        operation_repository=operation_repo,
        plugin_registry=StoragePluginRegistry(),
    )

    overview = service.get_overview()

    assert overview.totals.total_configurations == 2
    assert overview.totals.enabled_configurations == 1
    assert overview.totals.total_files == 10
    assert overview.totals.total_size_bytes == 2048
    assert overview.configurations[0].health == StorageHealthReport(
        configuration_id=config_enabled.id,
        provider=StorageProviderName.LOCAL_FILESYSTEM,
        status=StorageHealthStatus.HEALTHY,
        last_checked_at=health_snapshot.last_checked_at,
        details={},
    )
