from __future__ import annotations

from src.domain.entities.user_data_source import (
    SourceConfiguration,
    SourceType,
)

from .base import SourcePlugin


class FileUploadSourcePlugin(SourcePlugin):
    """Plugin for validating file upload sources."""

    source_type = SourceType.FILE_UPLOAD

    def validate_configuration(
        self,
        configuration: SourceConfiguration,
    ) -> SourceConfiguration:
        if not configuration.file_path:
            msg = "file_path is required for file upload sources"
            raise ValueError(msg)
        if not configuration.format:
            msg = "format is required for file upload sources"
            raise ValueError(msg)
        metadata = configuration.metadata or {}
        metadata.setdefault("ingest_mode", "batch")
        return configuration.model_copy(update={"metadata": metadata})


class APISourcePlugin(SourcePlugin):
    """Plugin for validating API-backed sources."""

    source_type = SourceType.API

    def validate_configuration(
        self,
        configuration: SourceConfiguration,
    ) -> SourceConfiguration:
        if not configuration.url:
            msg = "url is required for API sources"
            raise ValueError(msg)
        if configuration.requests_per_minute is None:
            msg = "requests_per_minute is required for API sources"
            raise ValueError(msg)
        metadata = configuration.metadata or {}
        metadata.setdefault("auth_type", configuration.auth_type or "none")
        return configuration.model_copy(update={"metadata": metadata})


class DatabaseSourcePlugin(SourcePlugin):
    """Plugin for validating database replication sources."""

    source_type = SourceType.DATABASE

    def validate_configuration(
        self,
        configuration: SourceConfiguration,
    ) -> SourceConfiguration:
        connection = (
            configuration.metadata.get("connection_string")
            if configuration.metadata
            else None
        )
        if not connection:
            msg = "metadata.connection_string is required for database sources"
            raise ValueError(msg)
        metadata = dict(configuration.metadata or {})
        metadata.setdefault("driver", "postgresql")
        return configuration.model_copy(update={"metadata": metadata})


__all__ = [
    "APISourcePlugin",
    "DatabaseSourcePlugin",
    "FileUploadSourcePlugin",
]
