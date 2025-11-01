"""
UniProt API client for MED13 Resource Library.
Fetches protein sequence, function, and annotation data from UniProt.
"""

import asyncio
from typing import Dict, List, Any, Optional
import json

from .base_ingestor import BaseIngestor


class UniProtIngestor(BaseIngestor):
    """
    UniProt API client for fetching protein data.

    UniProt provides comprehensive protein sequence and functional information.
    This ingestor focuses on MED13 protein data and related annotations.
    """

    def __init__(self):
        super().__init__(
            source_name="uniprot",
            base_url="https://rest.uniprot.org",
            requests_per_minute=30,  # UniProt allows up to 200 requests/minute
            # for programmatic access
            timeout_seconds=60,  # Protein data can be large
        )

    async def fetch_data(self, query: str = "MED13", **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch UniProt data for specified protein query.

        Args:
            query: Protein search query (default: MED13)
            **kwargs: Additional search parameters

        Returns:
            List of UniProt protein records
        """
        # Step 1: Search for proteins
        protein_ids = await self._search_proteins(query, **kwargs)
        if not protein_ids:
            return []

        # Step 2: Fetch detailed records
        all_records = []
        batch_size = 25  # UniProt batch limit

        for i in range(0, len(protein_ids), batch_size):
            batch_ids = protein_ids[i : i + batch_size]
            batch_records = await self._fetch_protein_details(batch_ids)
            all_records.extend(batch_records)

            # Small delay between batches
            await asyncio.sleep(0.1)

        return all_records

    async def _search_proteins(self, query: str, **kwargs) -> List[str]:
        """
        Search UniProt for proteins matching the query.

        Args:
            query: Protein search query
            **kwargs: Additional search parameters

        Returns:
            List of UniProt accession numbers
        """
        # Build search query
        search_terms = [query]

        # Add organism filter (human by default for MED13)
        if kwargs.get("organism", "human").lower() in ["human", "homo sapiens", "9606"]:
            search_terms.append("organism_id:9606")

        # Add reviewed filter if requested
        if kwargs.get("reviewed_only", True):
            search_terms.append("reviewed:true")

        full_query = " AND ".join(search_terms)

        # Use UniProt search API
        params = {
            "query": full_query,
            "format": "list",  # Just accession numbers
            "size": kwargs.get("max_results", 50),  # Limit results
        }

        response = await self._make_request("GET", "/uniprotkb/search", params=params)
        content = response.text.strip()

        # Parse accession numbers (one per line)
        accession_numbers = [
            line.strip() for line in content.split("\n") if line.strip()
        ]
        return accession_numbers

    async def _fetch_protein_details(
        self, accession_numbers: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Fetch detailed UniProt records for given accession numbers.

        Args:
            accession_numbers: List of UniProt accession numbers

        Returns:
            List of detailed protein records
        """
        if not accession_numbers:
            return []

        # Join accessions for batch request
        accessions = ",".join(accession_numbers)

        # Fetch detailed records in JSON format
        params = {
            "accessions": accessions,
            "format": "json",
        }

        response = await self._make_request("GET", "/uniprotkb/search", params=params)

        try:
            data = response.json()
            records = data.get("results", [])

            # Enrich records with source metadata
            for record in records:
                record.update(
                    {
                        "source": "uniprot",
                        "fetched_at": response.headers.get("date", ""),
                        "accession_numbers": accession_numbers,
                    }
                )

            return records

        except json.JSONDecodeError:
            # Return error record
            return [
                {
                    "parsing_error": "Failed to parse UniProt JSON response",
                    "accession_numbers": accession_numbers,
                    "raw_response": response.text[
                        :1000
                    ],  # First 1000 chars for debugging
                }
            ]

    def _parse_uniprot_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and normalize UniProt record data.

        Args:
            record: Raw UniProt record

        Returns:
            Normalized protein record
        """
        try:
            # Extract basic information
            parsed = {
                "uniprot_id": record.get("primaryAccession", ""),
                "entry_name": record.get("uniProtkbId", ""),
                "protein_name": self._extract_protein_name(record),
                "gene_name": self._extract_gene_name(record),
                "organism": self._extract_organism(record),
                "sequence": self._extract_sequence(record),
                "function": self._extract_function(record),
                "subcellular_location": self._extract_subcellular_location(record),
                "pathway": self._extract_pathway(record),
                "disease_associations": self._extract_disease_associations(record),
                "isoforms": self._extract_isoforms(record),
                "domains": self._extract_domains(record),
                "ptm_sites": self._extract_ptm_sites(record),
                "interactions": self._extract_interactions(record),
                "references": self._extract_references(record),
                "last_updated": record.get("entryAudit", {}).get(
                    "lastAnnotationUpdateDate", ""
                ),
            }

            # Add MED13-specific analysis
            parsed["med13_analysis"] = self._analyze_med13_relevance(parsed)

            return parsed

        except Exception as e:
            return {
                "parsing_error": str(e),
                "uniprot_id": record.get("primaryAccession", "unknown"),
                "raw_record": json.dumps(record)[:1000],  # First 1000 chars
            }

    def _extract_protein_name(self, record: Dict[str, Any]) -> Optional[str]:
        """Extract recommended protein name."""
        try:
            protein_desc = record.get("proteinDescription", {})
            recommended_name = protein_desc.get("recommendedName", {})

            if recommended_name:
                return recommended_name.get("fullName", {}).get("value")

            # Fallback to submitted names
            submitted_names = protein_desc.get("submissionNames", [])
            if submitted_names:
                return submitted_names[0].get("fullName", {}).get("value")

        except Exception:
            pass
        return None

    def _extract_gene_name(self, record: Dict[str, Any]) -> Optional[str]:
        """Extract primary gene name."""
        try:
            genes = record.get("genes", [])
            for gene in genes:
                if gene.get("type") == "primary":
                    return gene.get("geneName", {}).get("value")
            # Fallback to first gene name
            if genes:
                return genes[0].get("geneName", {}).get("value")
        except Exception:
            pass
        return None

    def _extract_organism(self, record: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Extract organism information."""
        try:
            organism = record.get("organism", {})
            return {
                "scientific_name": organism.get("scientificName"),
                "common_name": organism.get("commonName"),
                "taxon_id": organism.get("taxonId"),
            }
        except Exception:
            pass
        return None

    def _extract_sequence(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract protein sequence information."""
        try:
            sequence = record.get("sequence", {})
            return {
                "length": sequence.get("length"),
                "mol_weight": sequence.get("molWeight"),
                "crc64": sequence.get("crc64"),
                "md5": sequence.get("md5"),
                # Note: Full sequence would be in separate endpoint if needed
            }
        except Exception:
            pass
        return None

    def _extract_function(self, record: Dict[str, Any]) -> List[str]:
        """Extract protein function descriptions."""
        functions = []
        try:
            comments = record.get("comments", [])
            for comment in comments:
                if comment.get("commentType") == "FUNCTION":
                    texts = comment.get("texts", [])
                    for text in texts:
                        if text.get("value"):
                            functions.append(text["value"])
        except Exception:
            pass
        return functions

    def _extract_subcellular_location(self, record: Dict[str, Any]) -> List[str]:
        """Extract subcellular location information."""
        locations = []
        try:
            comments = record.get("comments", [])
            for comment in comments:
                if comment.get("commentType") == "SUBCELLULAR LOCATION":
                    subcellular_locations = comment.get("subcellularLocations", [])
                    for location in subcellular_locations:
                        location_desc = location.get("location", {}).get("value")
                        if location_desc:
                            locations.append(location_desc)
        except Exception:
            pass
        return locations

    def _extract_pathway(self, record: Dict[str, Any]) -> List[str]:
        """Extract pathway information."""
        pathways = []
        try:
            comments = record.get("comments", [])
            for comment in comments:
                if comment.get("commentType") == "PATHWAY":
                    texts = comment.get("texts", [])
                    for text in texts:
                        if text.get("value"):
                            pathways.append(text["value"])
        except Exception:
            pass
        return pathways

    def _extract_disease_associations(
        self, record: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract disease associations."""
        diseases = []
        try:
            comments = record.get("comments", [])
            for comment in comments:
                if comment.get("commentType") == "DISEASE":
                    disease = comment.get("disease", {})
                    if disease:
                        diseases.append(
                            {
                                "name": disease.get("diseaseName"),
                                "description": disease.get("description"),
                                "acronym": disease.get("acronym"),
                                "id": disease.get("diseaseId"),
                            }
                        )
        except Exception:
            pass
        return diseases

    def _extract_isoforms(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract isoform information."""
        isoforms = []
        try:
            isoform_refs = record.get("isoforms", [])
            for isoform_ref in isoform_refs:
                isoform = isoform_ref.get("isoformIds", [{}])[0]
                if isoform:
                    isoforms.append(
                        {
                            "name": isoform.get("value"),
                            "sequence_ids": isoform_ref.get("isoformSequenceIds", []),
                        }
                    )
        except Exception:
            pass
        return isoforms

    def _extract_domains(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract domain information."""
        domains = []
        try:
            features = record.get("features", [])
            for feature in features:
                if feature.get("type") == "DOMAIN":
                    domains.append(
                        {
                            "name": feature.get("description"),
                            "start": feature.get("location", {})
                            .get("start", {})
                            .get("value"),
                            "end": feature.get("location", {})
                            .get("end", {})
                            .get("value"),
                        }
                    )
        except Exception:
            pass
        return domains

    def _extract_ptm_sites(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract post-translational modification sites."""
        ptm_sites = []
        try:
            features = record.get("features", [])
            ptm_types = ["MODIFIED RESIDUE", "CROSSLNK", "LIPID BINDING SITE"]
            for feature in features:
                if feature.get("type") in ptm_types:
                    ptm_sites.append(
                        {
                            "type": feature.get("type"),
                            "description": feature.get("description"),
                            "position": feature.get("location", {})
                            .get("position", {})
                            .get("value"),
                        }
                    )
        except Exception:
            pass
        return ptm_sites

    def _extract_interactions(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract protein interaction information."""
        interactions = []
        try:
            comments = record.get("comments", [])
            for comment in comments:
                if comment.get("commentType") == "INTERACTION":
                    interactants = comment.get("interactions", [])
                    for interaction in interactants:
                        interactions.append(
                            {
                                "interactant": interaction.get("interactant", {}).get(
                                    "value"
                                ),
                                "label": interaction.get("label"),
                            }
                        )
        except Exception:
            pass
        return interactions

    def _extract_references(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract reference information."""
        references = []
        try:
            citations = record.get("references", [])
            for citation in citations:
                ref = citation.get("citation", {})
                if ref:
                    references.append(
                        {
                            "title": ref.get("title"),
                            "authors": [
                                author.get("name") for author in ref.get("authors", [])
                            ],
                            "journal": ref.get("journal"),
                            "publication_date": ref.get("publicationDate", {}).get(
                                "value"
                            ),
                            "pubmed_id": ref.get("pubmedId"),
                            "doi": ref.get("doiId"),
                        }
                    )
        except Exception:
            pass
        return references

    def _analyze_med13_relevance(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze MED13 relevance of protein record.

        Args:
            record: Parsed protein record

        Returns:
            Relevance analysis
        """
        relevance_score = 0
        reasons = []

        # Check gene name
        gene_name = (record.get("gene_name") or "").lower()
        if "med13" in gene_name:
            relevance_score += 10
            reasons.append("MED13 gene")

        # Check protein name
        protein_name = (record.get("protein_name") or "").lower()
        if "mediator" in protein_name and "13" in protein_name:
            relevance_score += 8
            reasons.append("Mediator complex subunit 13")

        # Check function descriptions
        functions = record.get("function", [])
        for func in functions:
            func_lower = func.lower()
            if "mediator" in func_lower and "transcription" in func_lower:
                relevance_score += 5
                reasons.append("Mediator complex function")
                break

        # Check disease associations
        diseases = record.get("disease_associations", [])
        med13_diseases = ["intellectual disability", "developmental disorder", "autism"]
        for disease in diseases:
            disease_name = disease.get("name", "").lower()
            if any(d in disease_name for d in med13_diseases):
                relevance_score += 3
                reasons.append(f"Disease association: {disease.get('name')}")

        return {
            "score": relevance_score,
            "reasons": reasons,
            "is_relevant": relevance_score >= 5,
        }

    async def fetch_med13_protein(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Convenience method to fetch MED13 protein data.

        Args:
            **kwargs: Additional search parameters

        Returns:
            List of MED13 protein records
        """
        records = await self.fetch_data("MED13", **kwargs)
        return [self._parse_uniprot_record(record) for record in records]

    async def fetch_protein_by_accession(
        self, accession: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch specific protein by UniProt accession number.

        Args:
            accession: UniProt accession number

        Returns:
            Protein record or None if not found
        """
        records = await self._fetch_protein_details([accession])
        if records:
            return self._parse_uniprot_record(records[0])
        return None

    async def fetch_protein_sequence(self, accession: str) -> Optional[str]:
        """
        Fetch protein sequence for given accession.

        Args:
            accession: UniProt accession number

        Returns:
            Protein sequence as string or None if not found
        """
        try:
            response = await self._make_request("GET", f"/uniprotkb/{accession}.fasta")
            # Parse FASTA format (skip header line)
            lines = response.text.strip().split("\n")
            if lines and lines[0].startswith(">"):
                return "".join(lines[1:])  # Join sequence lines
        except Exception:
            pass
        return None
