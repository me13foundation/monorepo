"""
Tests for StorageConfigurationValidator business rules.
"""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from src.application.services.storage_configuration_validator import (
    StorageConfigurationValidator,
)
from src.domain.entities.storage_configuration import StorageConfiguration
from src.domain.services.storage_providers.errors import StorageValidationError
from src.type_definitions.storage import (
    LocalFilesystemConfig,
    StorageProviderCapability,
    StorageProviderName,
    StorageUseCase,
)


class FakeStoragePlugin:
    def __init__(
        self,
        capabilities: set[StorageProviderCapability],
        use_cases: set[StorageUseCase],
    ):
        self._capabilities = capabilities
        self._use_cases = use_cases

    def capabilities(self) -> set[StorageProviderCapability]:
        return self._capabilities

    def supports_use_case(self, use_case: StorageUseCase) -> bool:
        return use_case in self._use_cases


class FakeConfigurationRepository:
    def __init__(self, configurations: list[StorageConfiguration]):
        self._configurations = configurations

    def list_configurations(
        self,
        *,
        include_disabled: bool = False,
    ) -> list[StorageConfiguration]:
        if include_disabled:
            return list(self._configurations)
        return [c for c in self._configurations if c.enabled]


def _make_config(
    name: str,
    *,
    enabled: bool = True,
    use_cases: set[StorageUseCase] | None = None,
) -> StorageConfiguration:
    return StorageConfiguration(
        id=uuid4(),
        name=name,
        provider=StorageProviderName.LOCAL_FILESYSTEM,
        config=LocalFilesystemConfig(
            provider=StorageProviderName.LOCAL_FILESYSTEM,
            base_path=Path(tempfile.gettempdir()),
            create_directories=True,
            expose_file_urls=False,
        ),
        enabled=enabled,
        supported_capabilities={StorageProviderCapability.PDF},
        default_use_cases=tuple(use_cases or []),
        metadata={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def test_ensure_unique_name_raises_on_duplicate():
    repo = FakeConfigurationRepository([_make_config(name="Existing")])
    validator = StorageConfigurationValidator()

    with pytest.raises(ValueError, match="already exists"):
        validator.ensure_unique_name(repo, name="Existing")

    # Case insensitive
    with pytest.raises(ValueError, match="already exists"):
        validator.ensure_unique_name(repo, name="EXISTING")


def test_ensure_unique_name_allows_same_id():
    config = _make_config(name="Existing")
    repo = FakeConfigurationRepository([config])
    validator = StorageConfigurationValidator()

    # Should not raise if exclude_id matches
    validator.ensure_unique_name(repo, name="Existing", exclude_id=config.id)


def test_ensure_capabilities_supported_raises_on_unsupported():
    plugin = FakeStoragePlugin(
        capabilities={StorageProviderCapability.PDF},
        use_cases=set(),
    )
    validator = StorageConfigurationValidator()

    with pytest.raises(StorageValidationError) as exc:
        validator.ensure_capabilities_supported(
            plugin=plugin,
            provider=StorageProviderName.LOCAL_FILESYSTEM,
            requested={
                StorageProviderCapability.PDF,
                StorageProviderCapability.EXPORT,
            },
        )

    assert exc.value.details["reason"] == "unsupported_capability"
    assert (
        StorageProviderCapability.EXPORT.value
        in exc.value.details["unsupported_capabilities"]
    )


def test_ensure_use_cases_supported_raises_on_unsupported():
    plugin = FakeStoragePlugin(
        capabilities=set(),
        use_cases={StorageUseCase.PDF},
    )
    validator = StorageConfigurationValidator()

    with pytest.raises(StorageValidationError) as exc:
        validator.ensure_use_cases_supported(
            plugin=plugin,
            provider=StorageProviderName.LOCAL_FILESYSTEM,
            use_cases={StorageUseCase.EXPORT},
        )

    assert exc.value.details["reason"] == "unsupported_use_case"
    assert exc.value.details["use_case"] == StorageUseCase.EXPORT.value


def test_ensure_use_case_exclusivity_detects_conflict():
    existing = _make_config(name="Primary", use_cases={StorageUseCase.PDF})
    repo = FakeConfigurationRepository([existing])
    validator = StorageConfigurationValidator()

    with pytest.raises(StorageValidationError) as exc:
        validator.ensure_use_case_exclusivity(
            repo,
            provider=StorageProviderName.GOOGLE_CLOUD_STORAGE,
            use_cases={StorageUseCase.PDF, StorageUseCase.EXPORT},
        )

    assert exc.value.details["reason"] == "use_case_already_assigned"
    assert exc.value.details["conflict_configuration_id"] == str(existing.id)
    assert StorageUseCase.PDF.value in exc.value.details["use_cases"]


def test_ensure_use_case_exclusivity_ignores_disabled():
    existing = _make_config(
        name="Disabled",
        enabled=False,
        use_cases={StorageUseCase.PDF},
    )
    repo = FakeConfigurationRepository([existing])
    validator = StorageConfigurationValidator()

    # Should not raise because existing is disabled
    validator.ensure_use_case_exclusivity(
        repo,
        provider=StorageProviderName.LOCAL_FILESYSTEM,
        use_cases={StorageUseCase.PDF},
    )
