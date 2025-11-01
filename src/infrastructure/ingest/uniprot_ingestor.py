"""
UniProt API client for MED13 Resource Library.
Fetches protein sequence, function, and annotation data from UniProt.
"""

import asyncio
from typing import Dict, List, Any, Optional
import json

import httpx
import requests

from .base_ingestor import BaseIngestor, IngestionError


class UniProtIngestor(BaseIngestor):
    """
    UniProt API client for fetching protein data.

    UniProt provides comprehensive protein sequence and functional information.
    This ingestor focuses on MED13 protein data and related annotations.
    """

    def __init__(self):
        super().__init__(
            source_name="uniprot",
            base_url="https://www.ebi.ac.uk/proteins/api",  # Try EBI Proteins API
            requests_per_minute=30,  # UniProt allows up to 200 requests/minute
            # for programmatic access
            timeout_seconds=60,  # Protein data can be large
        )

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> httpx.Response:
        """
        Override base _make_request to handle UniProt's redirect issues.
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        for attempt in range(self.max_retries):
            try:
                # Wait for rate limit token
                await self.rate_limiter.wait_for_token()

                # Use a fresh client for each request to avoid redirect issues
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(self.timeout_seconds),
                    follow_redirects=False,  # Don't follow redirects for UniProt
                    headers={
                        "User-Agent": "MED13-Resource-Library/1.0 (research@med13.org)"
                    },
                ) as temp_client:
                    response = await temp_client.request(method, url, **kwargs)

                    # Check for rate limiting
                    if response.status_code == 429:
                        # Exponential backoff for rate limiting
                        wait_time = 2**attempt
                        await asyncio.sleep(wait_time)
                        continue

                    response.raise_for_status()
                    return response

            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    # Server error - retry
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2**attempt)
                        continue
                raise IngestionError(
                    f"HTTP {e.response.status_code}: {e.response.text}",
                    self.source_name,
                )

            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue
                raise IngestionError(
                    f"Request failed after {self.max_retries} attempts: {str(e)}",
                    self.source_name,
                )

        raise IngestionError(
            f"Request failed after {self.max_retries} attempts",
            self.source_name,
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
        # Build search query - start simple
        # UniProt might not support complex queries with AND
        full_query = query  # Just use the basic query for now

        # Use EBI Proteins API
        size = kwargs.get("max_results", 50)
        url = f"{self.base_url}/proteins"
        params = {
            "protein": full_query,  # EBI uses 'protein' parameter
            "size": size,
        }

        # Wait for rate limit
        await self.rate_limiter.wait_for_token()

        # Use requests directly
        response = requests.get(
            url,
            params=params,
            headers={"User-Agent": "MED13-Resource-Library/1.0 (research@med13.org)"},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

        # Parse XML response to extract accession numbers
        import xml.etree.ElementTree as ET

        try:
            root = ET.fromstring(response.text)

            # Extract accession numbers from XML
            accession_numbers = []
            ns = {
                "u": "http://uniprot.org/uniprot",
                "u2": "https://uniprot.org/uniprot",
            }

            # Try explicit namespaces
            for ns_name in ["u", "u2"]:
                for entry in root.findall(f".//{ns_name}:accession", ns):
                    if entry.text:
                        accession_numbers.append(entry.text.strip())

        except Exception:
            accession_numbers = []

        # Remove duplicates and limit results
        accession_numbers = list(set(accession_numbers))[:size]
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

        # Fetch detailed records from EBI API (returns XML)
        url = f"{self.base_url}/proteins"
        params = {
            "accession": accessions,  # EBI uses 'accession' parameter
        }

        # Wait for rate limit
        await self.rate_limiter.wait_for_token()

        # Use requests directly
        response = requests.get(
            url,
            params=params,
            headers={"User-Agent": "MED13-Resource-Library/1.0 (research@med13.org)"},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

        # Parse XML response
        import xml.etree.ElementTree as ET

        root = ET.fromstring(response.text)

        records = []
        ns = {"u": "http://uniprot.org/uniprot", "u2": "https://uniprot.org/uniprot"}

        # Try finding entries with different namespace approaches
        entries = []
        for ns_name in ["u", "u2"]:
            entries = root.findall(f".//{ns_name}:entry", ns)
            if entries:
                break

        for entry in entries:
            # Convert XML entry to dictionary format
            record = self._parse_xml_entry(entry)
            record.update(
                {
                    "source": "uniprot",
                    "fetched_at": response.headers.get("date", ""),
                    "accession_numbers": accession_numbers,
                }
            )
            records.append(record)

        return records

    def _parse_xml_entry(self, entry) -> Dict[str, Any]:
        """
        Parse XML entry element into dictionary format.

        Args:
            entry: XML element for a UniProt entry

        Returns:
            Dictionary representation of the entry
        """
        record = {}

        # Extract basic information - handle namespace properly
        # The entry element has xmlns="https://uniprot.org/uniprot"
        ns = {"u": "https://uniprot.org/uniprot"}

        # Primary accession
        accession_elem = entry.find("u:accession", ns)
        if accession_elem is not None:
            record["primaryAccession"] = accession_elem.text

        # UniProt ID
        name_elem = entry.find("u:name", ns)
        if name_elem is not None:
            record["uniProtkbId"] = name_elem.text

        # Protein description
        protein_elem = entry.find("u:protein", ns)
        if protein_elem is not None:
            record["proteinDescription"] = self._parse_protein_description(protein_elem)

        # Gene information
        genes = []
        for gene_elem in entry.findall("u:gene/u:name", ns):
            genes.append(
                {
                    "geneName": {"value": gene_elem.text},
                    "type": gene_elem.get("type", "primary"),
                }
            )
        if genes:
            record["genes"] = genes

        # Organism information
        organism_elem = entry.find("u:organism", ns)
        if organism_elem is not None:
            record["organism"] = self._parse_organism(organism_elem)

        # Sequence information
        sequence_elem = entry.find("u:sequence", ns)
        if sequence_elem is not None:
            record["sequence"] = {
                "length": int(sequence_elem.get("length", 0)),
                "mass": int(sequence_elem.get("mass", 0)),
                "checksum": sequence_elem.get("checksum", ""),
                "modified": sequence_elem.get("modified", ""),
                "version": int(sequence_elem.get("version", 1)),
            }

        # Comments (function, subcellular location, etc.)
        comments = []
        for comment_elem in entry.findall("u:comment", ns):
            comments.append(self._parse_comment(comment_elem))
        if comments:
            record["comments"] = comments

        # References
        references = []
        for ref_elem in entry.findall("u:reference", ns):
            references.append(self._parse_reference(ref_elem))
        if references:
            record["references"] = references

        # Features (domains, PTMs, etc.)
        features = []
        for feature_elem in entry.findall("u:feature", ns):
            features.append(self._parse_feature(feature_elem))
        if features:
            record["features"] = features

        # Database references
        db_refs = []
        for db_elem in entry.findall("u:dbReference", ns):
            db_refs.append(
                {
                    "type": db_elem.get("type"),
                    "id": db_elem.get("id"),
                    "properties": [
                        {"type": prop.get("type"), "value": prop.get("value")}
                        for prop in db_elem.findall("u:property", ns)
                    ],
                }
            )
        if db_refs:
            record["dbReferences"] = db_refs

        # Entry audit information
        audit_elem = entry.find("u:entryAudit", ns)
        if audit_elem is not None:
            record["entryAudit"] = {
                "lastAnnotationUpdateDate": audit_elem.get(
                    "lastAnnotationUpdateDate", ""
                )
            }

        return record

    def _parse_protein_description(self, protein_elem) -> Dict[str, Any]:
        """Parse protein description element."""
        ns = {"u": "https://uniprot.org/uniprot"}
        desc = {}

        # Recommended name
        rec_name = protein_elem.find("u:recommendedName", ns)
        if rec_name is not None:
            full_name = rec_name.find("u:fullName", ns)
            if full_name is not None:
                desc["recommendedName"] = {"fullName": {"value": full_name.text}}

        return desc

    def _parse_organism(self, organism_elem) -> Dict[str, Any]:
        """Parse organism element."""
        ns = {"u": "https://uniprot.org/uniprot"}
        org = {}

        # Scientific name
        sci_name = organism_elem.find('u:name[@type="scientific"]', ns)
        if sci_name is not None:
            org["scientificName"] = sci_name.text

        # Common name
        com_name = organism_elem.find('u:name[@type="common"]', ns)
        if com_name is not None:
            org["commonName"] = com_name.text

        # Taxon ID
        taxon_ref = organism_elem.find('u:dbReference[@type="NCBI Taxonomy"]', ns)
        if taxon_ref is not None:
            org["taxonId"] = taxon_ref.get("id")

        return org

    def _parse_comment(self, comment_elem) -> Dict[str, Any]:
        """Parse comment element."""
        ns = {"u": "https://uniprot.org/uniprot"}
        comment = {"commentType": comment_elem.get("type")}

        # Text content
        texts = []
        for text_elem in comment_elem.findall("u:text", ns):
            texts.append({"value": text_elem.text})
        if texts:
            comment["texts"] = texts

        # Subcellular locations
        locations = []
        for loc_elem in comment_elem.findall("u:subcellularLocation/u:location", ns):
            locations.append({"value": loc_elem.text})
        if locations:
            comment["subcellularLocations"] = [
                {"location": {"value": loc["value"]}} for loc in locations
            ]

        return comment

    def _parse_reference(self, ref_elem) -> Dict[str, Any]:
        """Parse reference element."""
        ns = {"u": "https://uniprot.org/uniprot"}
        ref = {}

        # Citation
        citation = ref_elem.find("u:citation", ns)
        if citation is not None:
            ref["citation"] = {
                "type": citation.get("type"),
                "title": (
                    citation.find("u:title", ns).text
                    if citation.find("u:title", ns) is not None
                    else None
                ),
                "publicationDate": {"value": citation.get("date")},
                "authors": [
                    {"name": author.text}
                    for author in citation.findall("u:authorList/u:person/u:name", ns)
                ],
            }

        return ref

    def _parse_feature(self, feature_elem) -> Dict[str, Any]:
        """Parse feature element."""
        ns = {"u": "https://uniprot.org/uniprot"}
        feature = {
            "type": feature_elem.get("type"),
            "description": feature_elem.get("description"),
        }

        # Location
        location = feature_elem.find("u:location", ns)
        if location is not None:
            loc_info = {}
            begin_elem = location.find("u:begin", ns)
            end_elem = location.find("u:end", ns)
            position_elem = location.find("u:position", ns)

            if begin_elem is not None and end_elem is not None:
                loc_info["start"] = {"value": int(begin_elem.get("position", 0))}
                loc_info["end"] = {"value": int(end_elem.get("position", 0))}
            elif position_elem is not None:
                loc_info["position"] = {"value": int(position_elem.get("position", 0))}

            feature["location"] = loc_info

        return feature

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
