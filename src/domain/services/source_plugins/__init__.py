from __future__ import annotations

from .base import SourcePlugin
from .plugins import (
    APISourcePlugin,
    DatabaseSourcePlugin,
    FileUploadSourcePlugin,
    PubMedSourcePlugin,
)
from .registry import SourcePluginRegistry, default_registry

default_registry.register_many(
    [
        FileUploadSourcePlugin(),
        APISourcePlugin(),
        DatabaseSourcePlugin(),
        PubMedSourcePlugin(),
    ],
    override=True,
)

__all__ = [
    "APISourcePlugin",
    "DatabaseSourcePlugin",
    "FileUploadSourcePlugin",
    "PubMedSourcePlugin",
    "SourcePlugin",
    "SourcePluginRegistry",
    "default_registry",
]
