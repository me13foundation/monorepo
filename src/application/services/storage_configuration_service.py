"""
Storage configuration application service.

Implements storage configuration management, validation,
and health monitoring orchestration.
"""

from __future__ import annotations

from collections.abc import Iterable  # noqa: TC003
from datetime import UTC, datetime
from pathlib import Path  # noqa: TC003
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from src.domain.entities.storage_configuration import (
    StorageConfiguration,
    StorageHealthSnapshot,
    StorageOperation,
)
from src.domain.services.storage_providers import (
    StorageOperationError,
    StoragePluginRegistry,
    StorageProviderPlugin,
    default_storage_registry,
)
from src.type_definitions.common import JSONObject  # noqa: TC001
from src.type_definitions.storage import (
    StorageConfigurationModel,
    StorageHealthReport,
    StorageHealthStatus,
    StorageOperationRecord,
    StorageOperationStatus,
    StorageOperationType,
    StorageProviderCapability,
    StorageProviderConfigModel,
    StorageProviderName,
    StorageProviderTestResult,
    StorageUsageMetrics,
    StorageUseCase,
)

if TYPE_CHECKING:
    from src.application.services.system_status_service import SystemStatusService
    from src.domain.repositories.storage_repository import (
        StorageConfigurationRepository,
        StorageOperationRepository,
    )


class StorageConfigurationValidator:
    """Business rule validation for storage configurations."""

    def ensure_unique_name(
        self,
        repository: StorageConfigurationRepository,
        *,
        name: str,
        exclude_id: UUID | None = None,
    ) -> None:
        existing = repository.list_configurations(include_disabled=True)
        for configuration in existing:
            if configuration.name.lower() != name.lower():
                continue
            if exclude_id and configuration.id == exclude_id:
                continue
            msg = f"Storage configuration '{name}' already exists"
            raise ValueError(msg)


class CreateStorageConfigurationRequest(BaseModel):
    """Request contract for creating a storage configuration."""

    name: str
    provider: StorageProviderName
    config: StorageProviderConfigModel
    supported_capabilities: set[StorageProviderCapability] | None = None
    default_use_cases: set[StorageUseCase] | None = None
    enabled: bool = True
    metadata: JSONObject = Field(default_factory=dict)
    ensure_storage_ready: bool = True

    model_config = ConfigDict(arbitrary_types_allowed=True)


class UpdateStorageConfigurationRequest(BaseModel):
    """Request contract for updating storage configurations."""

    name: str | None = None
    config: StorageProviderConfigModel | None = None
    supported_capabilities: set[StorageProviderCapability] | None = None
    default_use_cases: set[StorageUseCase] | None = None
    metadata: JSONObject | None = None
    enabled: bool | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class StorageConfigurationService:
    """Application service orchestrating storage configuration use cases."""

    def __init__(
        self,
        configuration_repository: StorageConfigurationRepository,
        operation_repository: StorageOperationRepository,
        plugin_registry: StoragePluginRegistry | None = None,
        validator: StorageConfigurationValidator | None = None,
        system_status_service: SystemStatusService | None = None,
    ):
        self._configuration_repository = configuration_repository
        self._operation_repository = operation_repository
        self._plugin_registry = plugin_registry or default_storage_registry
        self._validator = validator or StorageConfigurationValidator()
        self._system_status_service = system_status_service

    async def create_configuration(
        self,
        request: CreateStorageConfigurationRequest,
    ) -> StorageConfiguration:
        """Create a new storage configuration."""

        self._validator.ensure_unique_name(
            self._configuration_repository,
            name=request.name,
        )
        plugin = self._require_plugin(request.provider)
        validated_config = await plugin.validate_config(request.config)

        configuration = StorageConfiguration(
            id=uuid4(),
            name=request.name,
            provider=request.provider,
            config=validated_config,
            enabled=request.enabled,
            supported_capabilities=tuple(
                request.supported_capabilities or plugin.capabilities(),
            ),
            default_use_cases=tuple(
                request.default_use_cases or {StorageUseCase.PDF},
            ),
            metadata=request.metadata,
        )
        persisted = self._configuration_repository.create(configuration)

        if request.ensure_storage_ready:
            await plugin.ensure_storage_exists(validated_config)

        return persisted

    async def update_configuration(
        self,
        configuration_id: UUID,
        request: UpdateStorageConfigurationRequest,
    ) -> StorageConfiguration:
        """Update an existing configuration."""

        current = self._require_configuration(configuration_id)
        requires_maintenance = request.config is not None
        if requires_maintenance:
            await self._require_maintenance_mode()

        updated_config_model = request.config or current.config
        plugin = self._require_plugin(current.provider)
        validated_config = await plugin.validate_config(updated_config_model)
        update_payload = current.model_copy(
            update={
                "name": request.name or current.name,
                "config": validated_config,
                "supported_capabilities": tuple(
                    request.supported_capabilities or current.supported_capabilities,
                ),
                "default_use_cases": tuple(
                    request.default_use_cases or current.default_use_cases,
                ),
                "metadata": request.metadata or current.metadata,
                "enabled": (
                    request.enabled if request.enabled is not None else current.enabled
                ),
                "updated_at": datetime.now(UTC),
            },
        )
        self._validator.ensure_unique_name(
            self._configuration_repository,
            name=update_payload.name,
            exclude_id=configuration_id,
        )
        return self._configuration_repository.update(update_payload)

    def list_configurations(
        self,
        *,
        include_disabled: bool = False,
    ) -> list[StorageConfiguration]:
        """List stored configurations."""

        return self._configuration_repository.list_configurations(
            include_disabled=include_disabled,
        )

    def get_configuration(self, configuration_id: UUID) -> StorageConfigurationModel:
        """Retrieve a configuration."""

        configuration = self._require_configuration(configuration_id)
        return StorageConfigurationModel(
            id=configuration.id,
            name=configuration.name,
            provider=configuration.provider,
            config=configuration.config,
            enabled=configuration.enabled,
            supported_capabilities=set(configuration.supported_capabilities),
            default_use_cases=set(configuration.default_use_cases),
            metadata=configuration.metadata,
            created_at=configuration.created_at,
            updated_at=configuration.updated_at,
        )

    def get_default_for_use_case(
        self,
        use_case: StorageUseCase,
    ) -> StorageConfiguration | None:
        """Resolve the first enabled configuration mapped to the use case."""

        for configuration in self._configuration_repository.list_configurations():
            if not configuration.enabled:
                continue
            if configuration.applies_to_use_case(use_case):
                return configuration
        return None

    def assign_use_cases(
        self,
        configuration_id: UUID,
        use_cases: Iterable[StorageUseCase],
    ) -> StorageConfiguration:
        """Assign default use cases to a configuration."""

        configuration = self._require_configuration(configuration_id)
        updated = configuration.with_updated_use_cases(use_cases)
        return self._configuration_repository.update(updated)

    async def test_configuration(
        self,
        configuration_id: UUID,
    ) -> StorageProviderTestResult:
        """Execute a provider connection test and record results."""

        configuration = self._require_configuration(configuration_id)
        plugin = self._require_plugin(configuration.provider)
        validated_config = await plugin.validate_config(configuration.config)
        result = await plugin.test_connection(
            validated_config,
            configuration_id=configuration.id,
        )
        self._operation_repository.record_test_result(result)
        snapshot = StorageHealthSnapshot(
            configuration_id=configuration.id,
            provider=configuration.provider,
            status=(
                StorageHealthStatus.HEALTHY
                if result.success
                else StorageHealthStatus.DEGRADED
            ),
            last_checked_at=result.checked_at,
            details=result.metadata,
        )
        self._operation_repository.upsert_health_snapshot(snapshot)
        return result

    async def record_store_operation(
        self,
        configuration: StorageConfiguration,
        *,
        key: str,
        file_path: Path,
        content_type: str | None,
        user_id: UUID | None,
    ) -> StorageOperationRecord:
        """Store a file using the provider and record the operation."""

        plugin = self._require_plugin(configuration.provider)
        validated_config = await plugin.validate_config(configuration.config)
        operation = StorageOperation(
            id=uuid4(),
            configuration_id=configuration.id,
            user_id=user_id,
            operation_type=StorageOperationType.STORE,
            key=key,
            status=StorageOperationStatus.PENDING,
            created_at=datetime.now(UTC),
        )
        try:
            storage_key = await plugin.store_file(
                validated_config,
                file_path=file_path,
                key=key,
                content_type=content_type,
            )
            success_operation = operation.model_copy(
                update={
                    "key": storage_key,
                    "status": StorageOperationStatus.SUCCESS,
                },
            )
            return self._operation_repository.record_operation(success_operation)
        except StorageOperationError as exc:
            failure_operation = operation.model_copy(
                update={
                    "status": StorageOperationStatus.FAILED,
                    "error_message": str(exc),
                },
            )
            self._operation_repository.record_operation(failure_operation)
            raise

    def get_usage_metrics(self, configuration_id: UUID) -> StorageUsageMetrics | None:
        """Return aggregated usage metrics for a configuration."""

        self._require_configuration(configuration_id)
        return self._operation_repository.get_usage_metrics(configuration_id)

    def get_health_report(self, configuration_id: UUID) -> StorageHealthReport | None:
        """Return the latest health snapshot for the configuration."""

        self._require_configuration(configuration_id)
        snapshot = self._operation_repository.get_health_snapshot(configuration_id)
        if snapshot is None:
            return None
        return snapshot.as_report()

    def list_operations(
        self,
        configuration_id: UUID,
        *,
        limit: int = 100,
    ) -> list[StorageOperationRecord]:
        """List recent storage operations for a configuration."""

        self._require_configuration(configuration_id)
        return self._operation_repository.list_operations(
            configuration_id,
            limit=limit,
        )

    def _require_plugin(
        self,
        provider: StorageProviderName,
    ) -> StorageProviderPlugin:
        plugin = self._plugin_registry.get(provider)
        if plugin is None:
            msg = f"No storage provider plugin registered for {provider.value}"
            raise RuntimeError(msg)
        return plugin

    def _require_configuration(self, configuration_id: UUID) -> StorageConfiguration:
        configuration = self._configuration_repository.get_by_id(configuration_id)
        if configuration is None:
            msg = f"Storage configuration {configuration_id} not found"
            raise ValueError(msg)
        return configuration

    async def _require_maintenance_mode(self) -> None:
        """Ensure maintenance mode is active when a risky operation is requested."""
        if self._system_status_service is None:
            return
        await self._system_status_service.require_active()
