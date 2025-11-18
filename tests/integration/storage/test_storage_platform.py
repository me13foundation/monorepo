from __future__ import annotations

from pathlib import Path

import pytest

from src.application.services.storage_configuration_requests import (
    CreateStorageConfigurationRequest,
)
from src.application.services.storage_configuration_service import (
    StorageConfigurationService,
)
from src.application.services.storage_operation_coordinator import (
    StorageOperationCoordinator,
)
from src.domain.services.storage_providers import StoragePluginRegistry
from src.infrastructure.repositories.storage_repository import (
    SqlAlchemyStorageConfigurationRepository,
    SqlAlchemyStorageOperationRepository,
)
from src.infrastructure.storage.providers.google_cloud import (
    GoogleCloudStorageProvider,
)
from src.infrastructure.storage.providers.local_filesystem import (
    LocalFilesystemStorageProvider,
)
from src.models.database.base import Base
from src.type_definitions.storage import (
    GoogleCloudStorageConfig,
    LocalFilesystemConfig,
    StorageOperationStatus,
    StorageProviderCapability,
    StorageProviderName,
    StorageUseCase,
)

pytestmark = pytest.mark.integration


class _FakeBlob:
    def __init__(self, bucket: dict[str, bytes], name: str):
        self._bucket = bucket
        self._name = name

    @property
    def public_url(self) -> str:
        return f"https://fake-storage/{self._name}"

    def upload_from_filename(
        self,
        filename: str,
        content_type: str | None = None,
    ) -> None:
        del content_type
        self._bucket[self._name] = Path(filename).read_bytes()

    def generate_signed_url(
        self,
        expiration,
        version: str = "v4",
    ) -> str:
        del expiration, version
        return f"https://signed.fake/{self._name}"

    def delete(self) -> None:
        self._bucket.pop(self._name, None)


class _FakeBucket:
    def __init__(self, buckets: dict[str, dict[str, bytes]], name: str):
        self._buckets = buckets
        self._name = name
        self._bucket = self._buckets.setdefault(name, {})

    def blob(self, name: str) -> _FakeBlob:
        return _FakeBlob(self._bucket, name)


class _FakeStorageClient:
    project = "test"

    def __init__(self):
        self._buckets: dict[str, dict[str, bytes]] = {}

    def bucket(self, name: str) -> _FakeBucket:
        return _FakeBucket(self._buckets, name)

    def list_blobs(self, bucket_name: str, prefix: str | None = None):
        bucket = self._buckets.get(bucket_name, {})
        for blob_name in bucket:
            if prefix is None or blob_name.startswith(prefix):
                yield type("BlobInfo", (), {"name": blob_name})()

    def lookup_bucket(self, bucket_name: str) -> dict[str, str]:
        self._buckets.setdefault(bucket_name, {})
        return {"name": bucket_name}


@pytest.mark.asyncio
async def test_storage_platform_end_to_end_local_and_gcs(tmp_path, db_session):
    Base.metadata.create_all(bind=db_session.get_bind())
    registry = StoragePluginRegistry()
    local_provider = LocalFilesystemStorageProvider()
    registry.register(local_provider, override=True)

    fake_client = _FakeStorageClient()
    gcs_provider = GoogleCloudStorageProvider()
    gcs_provider._client_factory = lambda _: fake_client  # noqa: SLF001
    registry.register(gcs_provider, override=True)

    configuration_repository = SqlAlchemyStorageConfigurationRepository(db_session)
    operation_repository = SqlAlchemyStorageOperationRepository(db_session)
    service = StorageConfigurationService(
        configuration_repository=configuration_repository,
        operation_repository=operation_repository,
        plugin_registry=registry,
    )
    coordinator = StorageOperationCoordinator(service)

    local_base_path = tmp_path / "local-storage"
    creds_file = tmp_path / "gcs-creds.json"
    creds_file.write_text("{}")

    local_request = CreateStorageConfigurationRequest(
        name="Local Storage",
        provider=StorageProviderName.LOCAL_FILESYSTEM,
        config=LocalFilesystemConfig(
            provider=StorageProviderName.LOCAL_FILESYSTEM,
            base_path=str(local_base_path),
            create_directories=True,
            expose_file_urls=True,
        ),
        supported_capabilities={StorageProviderCapability.PDF},
        default_use_cases={StorageUseCase.PDF},
    )
    gcs_request = CreateStorageConfigurationRequest(
        name="Cloud Storage",
        provider=StorageProviderName.GOOGLE_CLOUD_STORAGE,
        config=GoogleCloudStorageConfig(
            provider=StorageProviderName.GOOGLE_CLOUD_STORAGE,
            bucket_name="med13-tests",
            base_path="exports",
            credentials_secret_name=str(creds_file),
            public_read=False,
            signed_url_ttl_seconds=600,
        ),
        supported_capabilities={StorageProviderCapability.EXPORT},
        default_use_cases={StorageUseCase.EXPORT},
    )

    local_config = await service.create_configuration(local_request)
    cloud_config = await service.create_configuration(gcs_request)

    pdf_source = tmp_path / "note.pdf"
    pdf_source.write_text("pdf-bytes")
    export_source = tmp_path / "bulk.csv"
    export_source.write_text("id,value\n1,42")

    pdf_operation = await coordinator.store_for_use_case(
        StorageUseCase.PDF,
        key="pdfs/report.pdf",
        file_path=pdf_source,
    )
    export_operation = await coordinator.store_for_use_case(
        StorageUseCase.EXPORT,
        key="/exports/run.csv",
        file_path=export_source,
    )

    assert pdf_operation.status == StorageOperationStatus.SUCCESS
    assert export_operation.status == StorageOperationStatus.SUCCESS

    local_operations = service.list_operations(local_config.id)
    cloud_operations = service.list_operations(cloud_config.id)
    assert len(local_operations) == 1
    assert len(cloud_operations) == 1

    overview = service.get_overview()
    assert overview.totals.total_configurations == 2
    assert overview.totals.total_files >= 2

    # Soft delete disables configuration
    await service.delete_configuration(local_config.id)
    disabled_model = service.get_configuration(local_config.id)
    assert disabled_model.enabled is False

    # Force delete removes record
    await service.delete_configuration(local_config.id, force=True)
    with pytest.raises(ValueError):
        service.get_configuration(local_config.id)
