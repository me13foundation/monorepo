from __future__ import annotations

import tempfile
from pathlib import Path

from src.domain.entities.user_data_source import SourceConfiguration, SourceType
from src.domain.services.source_plugins.base import SourcePlugin
from src.domain.services.source_plugins.registry import SourcePluginRegistry


class DummyPlugin(SourcePlugin):
    source_type = SourceType.FILE_UPLOAD

    def validate_configuration(
        self,
        configuration: SourceConfiguration,
    ) -> SourceConfiguration:
        if not configuration.file_path:
            msg = "file_path required"
            raise ValueError(msg)
        metadata = dict(configuration.metadata)
        metadata["validated_by"] = "dummy"
        return configuration.model_copy(update={"metadata": metadata})


def test_registry_registers_and_validates_configuration() -> None:
    registry = SourcePluginRegistry()
    plugin = DummyPlugin()
    registry.register(plugin)

    stored = registry.get(SourceType.FILE_UPLOAD)
    assert stored is plugin

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_file:
        tmp_path = tmp_file.name

    try:
        config = SourceConfiguration(file_path=tmp_path, format="csv")
        validated = stored.validate_configuration(config)
        assert validated.metadata["validated_by"] == "dummy"
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_registry_override_replaces_existing_plugin() -> None:
    registry = SourcePluginRegistry()
    registry.register(DummyPlugin())

    class AlternatePlugin(DummyPlugin):
        def validate_configuration(
            self,
            configuration: SourceConfiguration,
        ) -> SourceConfiguration:
            result = super().validate_configuration(configuration)
            metadata = dict(result.metadata)
            metadata["plugin"] = "alternate"
            return result.model_copy(update={"metadata": metadata})

    registry.register(AlternatePlugin(), override=True)
    config = SourceConfiguration(file_path="file.csv", format="csv")
    stored = registry.get(SourceType.FILE_UPLOAD)
    validated = stored.validate_configuration(config)
    assert validated.metadata.get("plugin") == "alternate"
