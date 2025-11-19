"""
Deterministic PubMed gateway implementations for development environments.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from src.application.services.pubmed_query_builder import PubMedQueryBuilder
from src.domain.entities.data_discovery_parameters import (
    AdvancedQueryParameters,  # noqa: TC001
)
from src.domain.services.pubmed_search import (
    PubMedPdfGateway,
    PubMedSearchGateway,
    PubMedSearchPayload,
)
from src.type_definitions.common import JSONObject  # noqa: TC001


class DeterministicPubMedSearchGateway(PubMedSearchGateway):
    """
    Generates deterministic PubMed search payloads without external API calls.

    This keeps tests hermetic while providing realistic-looking metadata.
    """

    def __init__(self, query_builder: PubMedQueryBuilder | None = None):
        self._query_builder = query_builder or PubMedQueryBuilder()

    async def run_search(
        self,
        parameters: AdvancedQueryParameters,
    ) -> PubMedSearchPayload:
        query = self._query_builder.build_query(parameters)
        digest = hashlib.sha256(query.encode("utf-8")).hexdigest()
        total_results = max(5, min(parameters.max_results, 25))
        article_ids = [
            f"{digest[:12]}{index:03d}" for index in range(1, total_results + 1)
        ]
        preview_records: list[JSONObject] = []
        for idx, article_id in enumerate(article_ids[:10]):
            preview_records.append(
                {
                    "pmid": article_id,
                    "title": f"{parameters.search_term or parameters.gene_symbol or 'MED13'} result {idx + 1}",
                    "query": query,
                    "generated_at": datetime.now(UTC).isoformat(),
                },
            )
        return PubMedSearchPayload(
            article_ids=article_ids,
            total_count=total_results,
            preview_records=preview_records,
        )


class SimplePubMedPdfGateway(PubMedPdfGateway):
    """Creates lightweight PDF-like payloads for download orchestration tests."""

    async def fetch_pdf(self, article_id: str) -> bytes:
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        content = (
            "MED13 Resource Library - PubMed Article\n"
            f"Article ID: {article_id}\n"
            f"Generated at: {timestamp}\n"
            "\n"
            "This is a placeholder document generated for development environments.\n"
        )
        return content.encode("utf-8")


__all__ = ["DeterministicPubMedSearchGateway", "SimplePubMedPdfGateway"]
