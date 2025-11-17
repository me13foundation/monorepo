"""
Storage configuration admin endpoints.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.application.services.storage_configuration_service import (
    CreateStorageConfigurationRequest,
    StorageConfigurationService,
    UpdateStorageConfigurationRequest,
)
from src.domain.entities.storage_configuration import StorageConfiguration
from src.routes.admin_routes.dependencies import get_storage_configuration_service
from src.type_definitions.storage import (
    StorageConfigurationModel,
    StorageHealthReport,
    StorageOperationRecord,
    StorageProviderTestResult,
    StorageUsageMetrics,
)

router = APIRouter(prefix="/storage", tags=["storage"])


def _serialize_configuration(
    configuration: StorageConfiguration,
) -> StorageConfigurationModel:
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


def _handle_not_found(exc: ValueError) -> None:
    raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/configurations",
    response_model=list[StorageConfigurationModel],
    summary="List storage configurations",
)
async def list_storage_configurations(
    *,
    include_disabled: Annotated[
        bool,
        Query(description="Include disabled configurations"),
    ] = False,
    service: Annotated[
        StorageConfigurationService,
        Depends(get_storage_configuration_service),
    ],
) -> list[StorageConfigurationModel]:
    configurations = service.list_configurations(include_disabled=include_disabled)
    return [_serialize_configuration(configuration) for configuration in configurations]


@router.get(
    "/configurations/{configuration_id}",
    response_model=StorageConfigurationModel,
    summary="Get storage configuration",
)
async def get_storage_configuration(
    configuration_id: UUID,
    service: Annotated[
        StorageConfigurationService,
        Depends(get_storage_configuration_service),
    ],
) -> StorageConfigurationModel:
    try:
        return service.get_configuration(configuration_id)
    except ValueError as exc:  # pragma: no cover - handled by FastAPI
        _handle_not_found(exc)
        raise  # unreachable


@router.post(
    "/configurations",
    response_model=StorageConfigurationModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create storage configuration",
)
async def create_storage_configuration(
    request: CreateStorageConfigurationRequest,
    service: Annotated[
        StorageConfigurationService,
        Depends(get_storage_configuration_service),
    ],
) -> StorageConfigurationModel:
    configuration = await service.create_configuration(request)
    return _serialize_configuration(configuration)


@router.put(
    "/configurations/{configuration_id}",
    response_model=StorageConfigurationModel,
    summary="Update storage configuration",
)
async def update_storage_configuration(
    configuration_id: UUID,
    request: UpdateStorageConfigurationRequest,
    service: Annotated[
        StorageConfigurationService,
        Depends(get_storage_configuration_service),
    ],
) -> StorageConfigurationModel:
    try:
        configuration = await service.update_configuration(configuration_id, request)
    except ValueError as exc:  # pragma: no cover
        _handle_not_found(exc)
        raise
    return _serialize_configuration(configuration)


@router.post(
    "/configurations/{configuration_id}/test",
    response_model=StorageProviderTestResult,
    summary="Test storage configuration connectivity",
)
async def test_storage_configuration(
    configuration_id: UUID,
    service: Annotated[
        StorageConfigurationService,
        Depends(get_storage_configuration_service),
    ],
) -> StorageProviderTestResult:
    try:
        return await service.test_configuration(configuration_id)
    except ValueError as exc:  # pragma: no cover
        _handle_not_found(exc)
        raise


@router.get(
    "/configurations/{configuration_id}/metrics",
    response_model=StorageUsageMetrics | None,
    summary="Get storage usage metrics",
)
async def get_storage_metrics(
    configuration_id: UUID,
    service: Annotated[
        StorageConfigurationService,
        Depends(get_storage_configuration_service),
    ],
) -> StorageUsageMetrics | None:
    try:
        return service.get_usage_metrics(configuration_id)
    except ValueError as exc:  # pragma: no cover
        _handle_not_found(exc)
        raise


@router.get(
    "/configurations/{configuration_id}/health",
    response_model=StorageHealthReport | None,
    summary="Get storage health report",
)
async def get_storage_health(
    configuration_id: UUID,
    service: Annotated[
        StorageConfigurationService,
        Depends(get_storage_configuration_service),
    ],
) -> StorageHealthReport | None:
    try:
        return service.get_health_report(configuration_id)
    except ValueError as exc:  # pragma: no cover
        _handle_not_found(exc)
        raise


@router.get(
    "/configurations/{configuration_id}/operations",
    response_model=list[StorageOperationRecord],
    summary="List storage operations",
)
async def list_storage_operations(
    configuration_id: UUID,
    *,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    service: Annotated[
        StorageConfigurationService,
        Depends(get_storage_configuration_service),
    ],
) -> list[StorageOperationRecord]:
    try:
        return service.list_operations(configuration_id, limit=limit)
    except ValueError as exc:  # pragma: no cover
        _handle_not_found(exc)
        raise
