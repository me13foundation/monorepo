"""Infrastructure gateway for PubMed data sources."""

from __future__ import annotations

from src.domain.entities.data_source_configs import PubMedQueryConfig  # noqa: TCH001
from src.domain.services.pubmed_ingestion import PubMedGateway
from src.infrastructure.ingest.pubmed_ingestor import PubMedIngestor
from src.type_definitions.common import JSONValue, RawRecord  # noqa: TCH001


class PubMedSourceGateway(PubMedGateway):
    """Adapter that executes PubMed queries per data source configuration."""

    def __init__(self, ingestor: PubMedIngestor | None = None) -> None:
        self._ingestor = ingestor or PubMedIngestor()

    async def fetch_records(self, config: PubMedQueryConfig) -> list[RawRecord]:
        """Fetch PubMed records using per-source query parameters."""
        params: dict[str, JSONValue] = {
            "query": config.query,
            "publication_types": config.publication_types,
            "mindate": config.date_from,
            "maxdate": config.date_to,
            "publication_date_from": config.date_from,
            "max_results": config.max_results,
        }

        raw_records = await self._ingestor.fetch_data(**params)
        return self._apply_relevance_threshold(raw_records, config.relevance_threshold)

    def _apply_relevance_threshold(
        self,
        records: list[RawRecord],
        threshold: int,
    ) -> list[RawRecord]:
        if threshold <= 0:
            return records

        filtered: list[RawRecord] = []
        for record in records:
            relevance = record.get("med13_relevance")
            score = None
            if isinstance(relevance, dict):
                score_value = relevance.get("score")
                if isinstance(score_value, int | float):
                    score = int(score_value)
            if score is None or score >= threshold:
                filtered.append(record)
        return filtered
