"""
Synthetic performance tests for storage operations.
"""

import asyncio
import logging
import os
import tempfile
import time
from pathlib import Path
from uuid import uuid4

import pytest

from src.application.services.storage_configuration_service import (
    StorageConfigurationService,
)
from src.domain.entities.storage_configuration import StorageConfiguration
from src.domain.services.storage_providers import StoragePluginRegistry
from src.infrastructure.repositories.storage_repository import (
    SqlAlchemyStorageConfigurationRepository,
    SqlAlchemyStorageOperationRepository,
)
from src.infrastructure.storage.providers.local_filesystem import (
    LocalFilesystemStorageProvider,
)
from src.type_definitions.storage import (
    LocalFilesystemConfig,
    StorageOperationStatus,
    StorageProviderCapability,
    StorageProviderName,
    StorageUseCase,
)

logger = logging.getLogger(__name__)


@pytest.fixture
def performance_storage_service(db_session):
    """Create a storage service backed by a real temporary directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Register local plugin pointing to temp dir
        registry = StoragePluginRegistry()
        registry.register(LocalFilesystemStorageProvider())

        # Create repo and service
        config_repo = SqlAlchemyStorageConfigurationRepository(db_session)
        op_repo = SqlAlchemyStorageOperationRepository(db_session)

        service = StorageConfigurationService(
            configuration_repository=config_repo,
            operation_repository=op_repo,
            plugin_registry=registry,
        )

        # Create a test configuration
        config_id = uuid4()
        config_model = LocalFilesystemConfig(
            provider=StorageProviderName.LOCAL_FILESYSTEM,
            base_path=tmp_dir,
            create_directories=True,
        )

        storage_config = StorageConfiguration(
            id=config_id,
            name="Performance Test Storage",
            provider=StorageProviderName.LOCAL_FILESYSTEM,
            config=config_model,
            enabled=True,
            supported_capabilities={
                StorageProviderCapability.PDF,
                StorageProviderCapability.EXPORT,
                StorageProviderCapability.RAW_SOURCE,
            },
            default_use_cases={StorageUseCase.RAW_SOURCE},
            metadata={},
        )

        config_repo.create(storage_config)

        yield service, storage_config


@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_storage_operations(performance_storage_service):
    """Test concurrent storage operations (>=10 parallel)."""
    service, config = performance_storage_service
    concurrency = 10
    file_size_kb = 100  # Small files for concurrency test

    # Create temp files
    files = []
    for i in range(concurrency):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(os.urandom(file_size_kb * 1024))
            files.append(Path(f.name))

    try:
        start_time = time.time()

        async def upload_task(path, index):
            key = f"perf/concurrent/file_{index}.bin"
            return await service.record_store_operation(
                configuration=config,
                key=key,
                file_path=path,
                content_type="application/octet-stream",
                user_id=None,
            )

        tasks = [upload_task(files[i], i) for i in range(concurrency)]
        results = await asyncio.gather(*tasks)

        duration = time.time() - start_time

        assert len(results) == concurrency
        for res in results:
            assert res.status == StorageOperationStatus.SUCCESS

        logger.info("Concurrent uploads: %s files", concurrency)
        logger.info("Total time: %.4fs", duration)
        logger.info("Average time per op: %.4fs", duration / concurrency)

    finally:
        for f in files:
            f.unlink(missing_ok=True)


@pytest.mark.performance
@pytest.mark.asyncio
@pytest.mark.skipif(
    os.environ.get("MED13_RUN_HEAVY_PERF_TESTS") != "1",
    reason="Skipping heavy 100MB upload test by default",
)
async def test_large_file_upload_throughput(performance_storage_service):
    """Test 100MB upload throughput."""
    service, config = performance_storage_service
    target_size_mb = 100
    target_time_seconds = 10.0

    # Create 100MB file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        # Write in chunks to avoid memory issues
        chunk_size = 1024 * 1024  # 1MB
        for _ in range(target_size_mb):
            f.write(os.urandom(chunk_size))
        file_path = Path(f.name)

    try:
        start_time = time.time()

        await service.record_store_operation(
            configuration=config,
            key="perf/large/100mb_file.bin",
            file_path=file_path,
            content_type="application/octet-stream",
            user_id=None,
        )

        duration = time.time() - start_time

        throughput_mbps = target_size_mb / duration

        logger.info("Large file upload: %sMB", target_size_mb)
        logger.info("Upload time: %.4fs", duration)
        logger.info("Throughput: %.2f MB/s", throughput_mbps)

        assert (
            duration < target_time_seconds
        ), f"Upload took {duration:.2f}s, expected < {target_time_seconds}s"

    finally:
        file_path.unlink(missing_ok=True)
