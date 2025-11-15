"""Tests for the PubMed source gateway."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.domain.entities.data_source_configs import PubMedQueryConfig
from src.infrastructure.data_sources.pubmed_gateway import PubMedSourceGateway


@pytest.mark.asyncio
async def test_gateway_passes_query_parameters() -> None:
    """Gateway should forward per-source configuration to the ingestor."""
    ingestor = AsyncMock()
    ingestor.fetch_data.return_value = []
    gateway = PubMedSourceGateway(ingestor=ingestor)
    config = PubMedQueryConfig(
        query="BRCA1",
        date_from="2023/01/01",
        date_to="2024/01/01",
        publication_types=["journal_article"],
        max_results=123,
        relevance_threshold=3,
    )

    await gateway.fetch_records(config)

    ingestor.fetch_data.assert_awaited_once_with(
        query="BRCA1",
        publication_types=["journal_article"],
        mindate="2023/01/01",
        maxdate="2024/01/01",
        publication_date_from="2023/01/01",
        max_results=123,
    )


@pytest.mark.asyncio
async def test_gateway_filters_by_relevance_threshold() -> None:
    """Records below the per-source relevance threshold should be excluded."""
    ingestor = AsyncMock()
    ingestor.fetch_data.return_value = [
        {
            "pubmed_id": "1",
            "med13_relevance": {"score": 2, "is_relevant": False},
        },
        {
            "pubmed_id": "2",
            "med13_relevance": {"score": 7, "is_relevant": True},
        },
    ]
    gateway = PubMedSourceGateway(ingestor=ingestor)
    config = PubMedQueryConfig(query="MED13", relevance_threshold=5)

    records = await gateway.fetch_records(config)

    assert len(records) == 1
    assert records[0]["pubmed_id"] == "2"
