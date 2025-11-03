"""
ClinVar API client for MED13 Resource Library.
Fetches genetic variant data from ClinVar database.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .base_ingestor import BaseIngestor
from ...type_definitions.external_apis import ClinVarSearchResponse
from ..validation.api_response_validator import APIResponseValidator

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

    async def fetch_data(
        self, gene_symbol: str = "MED13", **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Fetch ClinVar data for specified gene.

        Args:
            gene_symbol: Gene symbol to search for (default: MED13)
            **kwargs: Additional search parameters

        Returns:
            List of ClinVar records
        """
        # Step 1: Search for ClinVar records
        variant_ids = await self._search_variants(gene_symbol, **kwargs)
        if not variant_ids:
            return []

        # Step 2: Fetch detailed records in batches
        all_records: List[Dict[str, Any]] = []
        batch_size = 50  # ClinVar API limit

        for i in range(0, len(variant_ids), batch_size):
            batch_ids = variant_ids[i : i + batch_size]
            batch_records = await self._fetch_variant_details(batch_ids)
            all_records.extend(batch_records)

            # Small delay between batches to be respectful
            await asyncio.sleep(0.1)

        return all_records

    async def _search_variants(self, gene_symbol: str, **kwargs: Any) -> List[str]:
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
                f"{kwargs['clinical_significance']}[clinical_significance]"
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
        data = response.json()

        # Validate response structure with runtime validation
        validation_result = APIResponseValidator.validate_clinvar_search_response(data)

        if not validation_result["is_valid"]:
            logger.warning(
                f"ClinVar search response validation failed: {validation_result['issues']}"
            )
            # Fallback to old extraction method
            id_list = data.get("esearchresult", {}).get("idlist", [])
            return [str(vid) for vid in id_list]

        # Use validated data
        validated_data = validation_result["sanitized_data"] or data
        search_response: ClinVarSearchResponse = validated_data
        id_list = search_response["esearchresult"]["idlist"]
        return [str(vid) for vid in id_list]

    async def _fetch_variant_details(
        self, variant_ids: List[str]
    ) -> List[Dict[str, Any]]:
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
            "GET", "esummary.fcgi", params=summary_params
        )
        summary_data = response.json()

        # Validate response structure with runtime validation
        validation_result = APIResponseValidator.validate_clinvar_variant_response(
            summary_data
        )

        if not validation_result["is_valid"]:
            logger.warning(
                f"ClinVar variant response validation failed: {validation_result['issues']}"
            )
            # Fallback to old processing
            variant_response = summary_data
        else:
            # Use validated data
            variant_response = validation_result["sanitized_data"] or summary_data

        records: List[Dict[str, Any]] = []
        for uid, summary in variant_response.get("result", {}).items():
            if uid == "uids":
                continue

            # Get full record details
            try:
                full_record = await self._fetch_single_variant(uid)
                if full_record:
                    records.append(full_record)
            except Exception:
                # Skip individual record failures
                continue

        return records

    async def _fetch_single_variant(self, variant_id: str) -> Optional[Dict[str, Any]]:
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

    def _parse_clinvar_xml(self, xml_content: str) -> Dict[str, Any]:
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
            parsed = {
                "gene_symbol": "MED13",  # Extract from XML
                "variant_type": "unknown",  # Extract from XML
                "clinical_significance": "unknown",  # Extract from XML
                "hgvs_notations": [],  # Extract from XML
                "conditions": [],  # Extract from XML
                "review_status": "unknown",  # Extract from XML
            }
            return parsed
        except Exception:
            return {"parsing_error": "Failed to parse ClinVar XML"}

    async def fetch_med13_variants(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """
        Convenience method to fetch all MED13-related variants.

        Args:
            **kwargs: Additional search parameters

        Returns:
            List of MED13 variant records
        """
        return await self.fetch_data("MED13", **kwargs)

    async def fetch_by_variant_type(
        self, variant_types: List[str], **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Fetch variants by specific types.

        Args:
            variant_types: List of variant types to search for
            **kwargs: Additional search parameters

        Returns:
            List of variant records
        """
        all_records: List[Dict[str, Any]] = []
        for variant_type in variant_types:
            kwargs_copy: Dict[str, Any] = kwargs.copy()
            kwargs_copy["variant_type"] = variant_type
            records = await self.fetch_med13_variants(**kwargs_copy)
            all_records.extend(records)

        return all_records

    async def fetch_by_clinical_significance(
        self, significances: List[str], **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Fetch variants by clinical significance.

        Args:
            significances: List of clinical significances to search for
            **kwargs: Additional search parameters

        Returns:
            List of variant records
        """
        all_records: List[Dict[str, Any]] = []
        for significance in significances:
            kwargs_copy: Dict[str, Any] = kwargs.copy()
            kwargs_copy["clinical_significance"] = significance
            records = await self.fetch_med13_variants(**kwargs_copy)
            all_records.extend(records)

        return all_records
