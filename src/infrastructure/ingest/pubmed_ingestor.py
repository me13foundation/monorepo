"""
PubMed API client for MED13 Resource Library.
Fetches scientific literature and publication data from PubMed.
"""

import asyncio
from typing import Dict, List, Any, Optional
from xml.etree import ElementTree as ET

from .base_ingestor import BaseIngestor


class PubMedIngestor(BaseIngestor):
    """
    PubMed API client for fetching scientific literature data.

    PubMed provides access to biomedical literature citations and abstracts.
    This ingestor focuses on publications related to MED13 gene and
    associated conditions.
    """

    def __init__(self):
        super().__init__(
            source_name="pubmed",
            base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            requests_per_minute=10,  # NCBI limits: 10 requests per second
            timeout_seconds=60,  # PubMed can be slow
        )

    async def fetch_data(self, query: str = "MED13", **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch PubMed data for specified search query.

        Args:
            query: Search query (default: MED13)
            **kwargs: Additional search parameters

        Returns:
            List of PubMed article records
        """
        # Step 1: Search for publications
        article_ids = await self._search_publications(query, **kwargs)
        if not article_ids:
            return []

        # Step 2: Fetch detailed records in batches
        all_records = []
        batch_size = 50  # PubMed API limit

        for i in range(0, len(article_ids), batch_size):
            batch_ids = article_ids[i : i + batch_size]
            batch_records = await self._fetch_article_details(batch_ids)
            all_records.extend(batch_records)

            # Small delay between batches
            await asyncio.sleep(0.1)

        return all_records

    async def _search_publications(self, query: str, **kwargs) -> List[str]:
        """
        Search PubMed for publications matching the query.

        Args:
            query: PubMed search query
            **kwargs: Additional search parameters

        Returns:
            List of PubMed article IDs
        """
        # Build comprehensive search query
        query_terms = [query]

        # Add filters if provided
        if kwargs.get("publication_date_from"):
            query_terms.append(f"{kwargs['publication_date_from']}[pdat]")
        if kwargs.get("publication_types"):
            pub_types = " OR ".join(f'"{pt}"[pt]' for pt in kwargs["publication_types"])
            query_terms.append(f"({pub_types})")

        full_query = " AND ".join(f"({term})" for term in query_terms)

        # Use ESearch to find relevant records
        params = {
            "db": "pubmed",
            "term": full_query,
            "retmode": "json",
            "retmax": kwargs.get("max_results", 500),  # Limit results
            "sort": "relevance",
            "datetype": "pdat",
            "mindate": kwargs.get("mindate", "2000"),  # Default to 2000 onwards
        }

        response = await self._make_request("GET", "esearch.fcgi", params=params)
        data = response.json()

        # Extract article IDs from search results
        id_list = data.get("esearchresult", {}).get("idlist", [])
        return [str(aid) for aid in id_list]

    async def _fetch_article_details(
        self, article_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Fetch detailed PubMed records for given article IDs.

        Args:
            article_ids: List of PubMed article IDs

        Returns:
            List of detailed article records
        """
        if not article_ids:
            return []

        id_str = ",".join(article_ids)

        # Get detailed records using EFetch
        params = {
            "db": "pubmed",
            "id": id_str,
            "rettype": "medline",
            "retmode": "xml",
        }

        response = await self._make_request("GET", "efetch.fcgi", params=params)

        # Parse XML response
        xml_content = response.text
        records = self._parse_pubmed_xml(xml_content)

        # Add source metadata
        for record in records:
            record.update(
                {
                    "pubmed_ids": article_ids,
                    "source": "pubmed",
                    "fetched_at": response.headers.get("date", ""),
                }
            )

        return records

    def _parse_pubmed_xml(self, xml_content: str) -> List[Dict[str, Any]]:
        """
        Parse PubMed XML response into structured data.

        Args:
            xml_content: Raw XML response

        Returns:
            List of parsed article records
        """
        try:
            root = ET.fromstring(xml_content)
            records = []

            # PubMed XML structure: MedlineCitation elements
            for citation in root.findall(".//MedlineCitation"):
                record = self._parse_single_citation(citation)
                if record:
                    records.append(record)

            return records
        except Exception as e:
            # Return error record for debugging
            return [
                {
                    "parsing_error": str(e),
                    "raw_xml": xml_content[:1000],  # First 1000 chars for debugging
                }
            ]

    def _parse_single_citation(self, citation: ET.Element) -> Optional[Dict[str, Any]]:
        """
        Parse a single MedlineCitation element.

        Args:
            citation: XML element containing citation data

        Returns:
            Parsed article record
        """
        try:
            # Extract PMID
            pmid_elem = citation.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else None

            if not pmid:
                return None

            # Extract basic metadata
            record = {
                "pubmed_id": pmid,
                "title": self._extract_text(citation, ".//ArticleTitle"),
                "abstract": self._extract_text(citation, ".//AbstractText"),
                "journal": self._extract_journal_info(citation),
                "authors": self._extract_authors(citation),
                "publication_date": self._extract_publication_date(citation),
                "publication_types": self._extract_publication_types(citation),
                "keywords": self._extract_keywords(citation),
                "doi": self._extract_doi(citation),
                "pmc_id": self._extract_pmc_id(citation),
            }

            # Extract MED13-specific information
            record["med13_relevance"] = self._assess_med13_relevance(record)

            return record

        except Exception:
            return None

    def _extract_text(self, element: ET.Element, xpath: str) -> Optional[str]:
        """Extract text content from XML element."""
        elem = element.find(xpath)
        return elem.text.strip() if elem is not None and elem.text else None

    def _extract_journal_info(self, citation: ET.Element) -> Optional[Dict[str, str]]:
        """Extract journal information."""
        journal_elem = citation.find(".//Journal")
        if journal_elem is None:
            return None

        return {
            "title": self._extract_text(journal_elem, ".//Title"),
            "iso_abbreviation": self._extract_text(journal_elem, ".//ISOAbbreviation"),
            "issn": self._extract_text(journal_elem, ".//ISSN"),
        }

    def _extract_authors(self, citation: ET.Element) -> List[Dict[str, str]]:
        """Extract author information."""
        authors = []
        for author_elem in citation.findall(".//Author"):
            author = {
                "last_name": self._extract_text(author_elem, ".//LastName"),
                "first_name": self._extract_text(author_elem, ".//ForeName"),
                "initials": self._extract_text(author_elem, ".//Initials"),
                "affiliation": self._extract_text(
                    author_elem, ".//AffiliationInfo/Affiliation"
                ),
            }
            if author["last_name"]:  # Only include if we have at least a last name
                authors.append(author)

        return authors

    def _extract_publication_date(self, citation: ET.Element) -> Optional[str]:
        """Extract publication date."""
        # Try different date fields in order of preference
        date_fields = [
            ".//PubDate",
            ".//Article/Journal/JournalIssue/PubDate",
        ]

        for xpath in date_fields:
            date_elem = citation.find(xpath)
            if date_elem is not None:
                # Extract year, month, day
                year = self._extract_text(date_elem, ".//Year")
                month = self._extract_text(date_elem, ".//Month")
                day = self._extract_text(date_elem, ".//Day")

                if year:
                    date_parts = [year]
                    if month:
                        date_parts.append(month)
                    if day:
                        date_parts.append(day)
                    return "-".join(date_parts)

        return None

    def _extract_publication_types(self, citation: ET.Element) -> List[str]:
        """Extract publication types."""
        types = []
        for type_elem in citation.findall(".//PublicationType"):
            if type_elem.text:
                types.append(type_elem.text.strip())
        return types

    def _extract_keywords(self, citation: ET.Element) -> List[str]:
        """Extract keywords."""
        keywords = []
        for kw_elem in citation.findall(".//Keyword"):
            if kw_elem.text:
                keywords.append(kw_elem.text.strip())
        return keywords

    def _extract_doi(self, citation: ET.Element) -> Optional[str]:
        """Extract DOI if available."""
        # DOI is typically in ArticleId elements
        for id_elem in citation.findall(".//ArticleId"):
            id_type = id_elem.get("IdType")
            if id_type == "doi" and id_elem.text:
                return id_elem.text.strip()
        return None

    def _extract_pmc_id(self, citation: ET.Element) -> Optional[str]:
        """Extract PMC ID if available."""
        for id_elem in citation.findall(".//ArticleId"):
            id_type = id_elem.get("IdType")
            if id_type == "pmc" and id_elem.text:
                return id_elem.text.strip()
        return None

    def _assess_med13_relevance(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess how relevant this publication is to MED13 research.

        Args:
            record: Parsed publication record

        Returns:
            Relevance assessment
        """
        relevance_score = 0
        reasons = []

        # Check title for MED13 mentions
        title = (record.get("title") or "").lower()
        if "med13" in title:
            relevance_score += 10
            reasons.append("MED13 in title")

        # Check abstract for MED13 mentions
        abstract = (record.get("abstract") or "").lower()
        if "med13" in abstract:
            relevance_score += 5
            reasons.append("MED13 in abstract")

        # Check keywords
        keywords = [kw.lower() for kw in record.get("keywords", [])]
        med13_keywords = [kw for kw in keywords if "med13" in kw]
        if med13_keywords:
            relevance_score += 3
            reasons.append(f"MED13 keywords: {', '.join(med13_keywords)}")

        return {
            "score": relevance_score,
            "reasons": reasons,
            "is_relevant": relevance_score >= 5,
        }

    async def fetch_med13_publications(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Convenience method to fetch MED13-related publications.

        Args:
            **kwargs: Additional search parameters

        Returns:
            List of MED13-related publication records
        """
        records = await self.fetch_data("MED13", **kwargs)

        # Filter for highly relevant publications
        relevant_records = [
            record
            for record in records
            if record.get("med13_relevance", {}).get("is_relevant", False)
        ]

        return relevant_records

    async def fetch_recent_publications(
        self, days_back: int = 365, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent publications related to MED13.

        Args:
            days_back: Number of days to look back
            **kwargs: Additional search parameters

        Returns:
            List of recent publication records
        """
        # Calculate date range
        from datetime import datetime, timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        kwargs["mindate"] = start_date.strftime("%Y/%m/%d")
        kwargs["maxdate"] = end_date.strftime("%Y/%m/%d")

        return await self.fetch_med13_publications(**kwargs)
