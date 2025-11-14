"""Application service for presenting curated MED13 resources."""

from collections.abc import Sequence

from src.models.resource import Resource


def list_resources() -> Sequence[Resource]:
    """Return curated resources. Placeholder until database integration is added."""
    return [
        Resource(
            id=1,
            title="MED13 Syndrome Foundation",
            url="https://med13foundation.org",
            summary="Central information hub for the MED13 Foundation.",
        ),
    ]


__all__ = ["list_resources"]
