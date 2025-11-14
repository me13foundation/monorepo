"""
ClinVar API client for MED13 Resource Library.
Fetches genetic variant data from ClinVar database.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, cast

from src.infrastructure.ingest.base_ingestor import BaseIngestor
from src.infrastructure.validation.api_response_validator import (
    APIResponseValidator,
)

if TYPE_CHECKING:
    from src.type_definitions.common import JSONValue, RawRecord
    from src.type_definitions.external_apis import (
        ClinVarSearchResponse,
        ClinVarVariantResponse,
    )

logger = logging.getLogger(__name__)


class ClinVarIngestor(BaseIngestor):
    """
    ClinVar API client for fetching genetic variant data.

    ClinVar aggregates information about genomic variation and its
    relationship to human health. This ingestor focuses on variants
    related to MED13.
    """

    def __init__(self) -> None:
        super().__init__(
            source_name="clinvar",
            base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            requests_per_minute=10,  # NCBI limits: 10 requests per second,
            # but be conservative
            timeout_seconds=60,  # NCBI can be slow
        )

    async def fetch_data(self, **kwargs: JSONValue) -> list[RawRecord]:
        """
        Fetch ClinVar data for specified gene.

        Args:
            gene_symbol: Gene symbol to search for (default: MED13)
            **kwargs: Additional search parameters

        Returns:
            List of ClinVar records
        """
        # Step 1: Search for ClinVar records
        gene_symbol_value = kwargs.get("gene_symbol")
        gene_symbol = (
            gene_symbol_value if isinstance(gene_symbol_value, str) else "MED13"
        )

        search_kwargs = dict(kwargs)
        search_kwargs.pop("gene_symbol", None)

        variant_ids = await self._search_variants(gene_symbol, **search_kwargs)
        if not variant_ids:
            return []

        # Step 2: Fetch detailed records in batches
        all_records: list[RawRecord] = []
        batch_size = 50  # ClinVar API limit

        for i in range(0, len(variant_ids), batch_size):
            batch_ids = variant_ids[i : i + batch_size]
            batch_records = await self._fetch_variant_details(batch_ids)
            all_records.extend(batch_records)

            # Small delay between batches to be respectful
            await asyncio.sleep(0.1)

        return all_records

    async def _search_variants(
        self,
        gene_symbol: str,
        **kwargs: JSONValue,
    ) -> list[str]:
        """
        Search ClinVar for variants related to a gene.

        Args:
            gene_symbol: Gene symbol to search for
            **kwargs: Additional search parameters

        Returns:
            List of ClinVar variant IDs
        """
        # Build search query - try multiple approaches for MED13
        # First try the standard gene search
        query_terms = [f"{gene_symbol}[gene]"]

        # Add organism filter
        query_terms.append("homo sapiens[organism]")

        # For MED13, also try searching by gene ID or symbol variations
        if gene_symbol.upper() == "MED13":
            # MED13 might be indexed differently - try broader search
            query_terms = [f"({gene_symbol}[gene] OR MED13[gene] OR mediator[gene])"]

        # Add additional filters if provided
        if kwargs.get("variant_type"):
            query_terms.append(f"{kwargs['variant_type']}[variant_type]")
        if kwargs.get("clinical_significance"):
            query_terms.append(
                f"{kwargs['clinical_significance']}[clinical_significance]",
            )

        query = " AND ".join(query_terms)

        # Use ESearch to find relevant records
        params = {
            "db": "clinvar",
            "term": query,
            "retmode": "json",
            "retmax": kwargs.get("max_results", 1000),  # Limit results
            "sort": "relevance",
        }

        response = await self._make_request("GET", "esearch.fcgi", params=params)
        data = cast("RawRecord", response.json())

        # Validate response structure with runtime validation
        validation_result = APIResponseValidator.validate_clinvar_search_response(data)

        if not validation_result["is_valid"]:
            logger.warning(
                "ClinVar search response validation failed: %s",
                validation_result["issues"],
            )
            # Fallback to old extraction method
            id_list_raw = data.get("esearchresult", {})
            if isinstance(id_list_raw, dict):
                ids = id_list_raw.get("idlist", [])
                if isinstance(ids, list):
                    return [str(vid) for vid in ids]
            return []

        sanitized: ClinVarSearchResponse | None = validation_result["sanitized_data"]
        if sanitized is None:
            logger.warning(
                "ClinVar search response missing sanitized payload; falling back to raw data",
            )
            esearch_fallback = data.get("esearchresult")
            if isinstance(esearch_fallback, dict):
                raw_ids = esearch_fallback.get("idlist", [])
                if isinstance(raw_ids, list):
                    return [str(vid) for vid in raw_ids]
            return []

        return [str(vid) for vid in sanitized["esearchresult"]["idlist"]]

    async def _fetch_variant_details(
        self,
        variant_ids: list[str],
    ) -> list[RawRecord]:
        """
        Fetch detailed ClinVar records for given variant IDs.

        Args:
            variant_ids: List of ClinVar variant IDs

        Returns:
            List of detailed variant records
        """
        if not variant_ids:
            return []

        # Use ESummary to get basic info, then EFetch for full details
        id_str = ",".join(variant_ids)

        # Get summaries first
        summary_params = {
            "db": "clinvar",
            "id": id_str,
            "retmode": "json",
        }

        response = await self._make_request(
            "GET",
            "esummary.fcgi",
            params=summary_params,
        )
        summary_data = cast("RawRecord", response.json())

        # Validate response structure with runtime validation
        validation_result = APIResponseValidator.validate_clinvar_variant_response(
            summary_data,
        )

        variant_response: RawRecord
        if not validation_result["is_valid"]:
            logger.warning(
                "ClinVar variant response validation failed: %s",
                validation_result["issues"],
            )
            # Fallback to old processing
            variant_response = summary_data
        else:
            sanitized_variant: ClinVarVariantResponse | None = validation_result[
                "sanitized_data"
            ]
            if sanitized_variant is None:
                logger.warning(
                    "ClinVar variant validation returned no sanitized payload despite passing validation",
                )
                variant_response = summary_data
            else:
                variant_response = cast("RawRecord", sanitized_variant)

        records: list[RawRecord] = []
        result_section = variant_response.get("result")
        if isinstance(result_section, dict):
            for uid in result_section:
                if not isinstance(uid, str) or uid == "uids":
                    continue

                # Get full record details
                try:
                    full_record = await self._fetch_single_variant(uid)
                    if full_record:
                        records.append(full_record)
                except Exception as exc:  # noqa: BLE001 - log and continue per-record
                    logger.warning("Failed to fetch full record for %s: %s", uid, exc)
                    continue

        return records

    async def _fetch_single_variant(self, variant_id: str) -> RawRecord | None:
        """
        Fetch detailed record for a single ClinVar variant.

        Args:
            variant_id: ClinVar variant ID

        Returns:
            Detailed variant record or None if failed
        """
        params = {
            "db": "clinvar",
            "id": variant_id,
            "rettype": "vcv",
            "retmode": "xml",
        }

        response = await self._make_request("GET", "efetch.fcgi", params=params)

        # Parse XML response (simplified - in production would use proper XML parsing)
        xml_content = response.text

        # For now, return basic structure - in production would parse XML properly
        return {
            "clinvar_id": variant_id,
            "raw_xml": xml_content,
            "source": "clinvar",
            "fetched_at": response.headers.get("date", ""),
            # TODO: Parse XML to extract structured data
            "parsed_data": self._parse_clinvar_xml(xml_content),
        }

    def _parse_clinvar_xml(self, _xml_content: str) -> RawRecord:
        """
        Parse ClinVar XML response into structured data.

        Args:
            xml_content: Raw XML response

        Returns:
            Parsed variant data
        """
        # Simplified XML parsing - in production would use proper XML parser
        # This is a placeholder that would be replaced with actual XML parsing logic
        try:
            # Basic extraction (would be replaced with proper XML parsing)
            parsed: RawRecord = {
                "gene_symbol": "MED13",  # Extract from XML
                "variant_type": "unknown",  # Extract from XML
                "clinical_significance": "unknown",  # Extract from XML
                "hgvs_notations": [],  # Extract from XML
                "conditions": [],  # Extract from XML
                "review_status": "unknown",  # Extract from XML
            }
        except Exception:  # noqa: BLE001
            return {"parsing_error": "Failed to parse ClinVar XML"}
        else:
            return parsed

    async def fetch_med13_variants(self, **kwargs: JSONValue) -> list[RawRecord]:
        """
        Convenience method to fetch all MED13-related variants.

        Args:
            **kwargs: Additional search parameters

        Returns:
            List of MED13 variant records
        """
        return await self.fetch_data(gene_symbol="MED13", **kwargs)

    async def fetch_by_variant_type(
        self,
        variant_types: list[str],
        **kwargs: JSONValue,
    ) -> list[RawRecord]:
        """
        Fetch variants by specific types.

        Args:
            variant_types: List of variant types to search for
            **kwargs: Additional search parameters

        Returns:
            List of variant records
        """
        all_records: list[RawRecord] = []
        for variant_type in variant_types:
            kwargs_copy: dict[str, JSONValue] = kwargs.copy()
            kwargs_copy["variant_type"] = variant_type
            records = await self.fetch_med13_variants(**kwargs_copy)
            all_records.extend(records)

        return all_records

    async def fetch_by_clinical_significance(
        self,
        significances: list[str],
        **kwargs: JSONValue,
    ) -> list[RawRecord]:
        """
        Fetch variants by clinical significance.

        Args:
            significances: List of clinical significances to search for
            **kwargs: Additional search parameters

        Returns:
            List of variant records
        """
        all_records: list[RawRecord] = []
        for significance in significances:
            kwargs_copy: dict[str, JSONValue] = kwargs.copy()
            kwargs_copy["clinical_significance"] = significance
            records = await self.fetch_med13_variants(**kwargs_copy)
            all_records.extend(records)

        return all_records
