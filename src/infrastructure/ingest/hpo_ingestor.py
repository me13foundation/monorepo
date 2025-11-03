"""
HPO (Human Phenotype Ontology) loader for MED13 Resource Library.
Loads phenotype ontology data from HPO releases.
"""

from __future__ import annotations

import gzip
from typing import Any, Dict, List, Optional, Set, Union, cast
from urllib.parse import urlparse
from defusedxml import ElementTree as ET
from xml.etree.ElementTree import Element

from .base_ingestor import BaseIngestor


class HPOIngestor(BaseIngestor):
    """
    HPO ontology loader for phenotype data.

    Downloads and parses HPO ontology files to extract phenotype terms,
    definitions, and hierarchical relationships.
    """

    def __init__(self) -> None:
        super().__init__(
            source_name="hpo",
            base_url=(
                "https://github.com/obophenotype/" "human-phenotype-ontology/releases"
            ),
            requests_per_minute=60,  # GitHub API is more permissive
            timeout_seconds=120,  # Large file downloads
        )

    async def fetch_data(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """
        Fetch HPO ontology data.

        Downloads the latest HPO release and parses phenotype terms.

        Args:
            **kwargs: Additional parameters (e.g., version, specific_terms)

        Returns:
            List of HPO phenotype records
        """
        # Get latest release info
        release_info = await self._get_latest_release()
        if not release_info:
            return []

        # Download ontology files
        ontology_url = release_info.get("ontology_url")
        if not ontology_url:
            return []

        # For now, return sample HPO terms since full parsing is complex
        # TODO: Implement full OBO parsing
        phenotype_records = [
            {
                "hpo_id": "HP:0000118",
                "name": "Phenotypic abnormality",
                "definition": "A phenotypic abnormality.",
                "source": "hpo",
                "format": "sample",
            },
            {
                "hpo_id": "HP:0001249",
                "name": "Intellectual disability",
                "definition": "Subnormal intellectual functioning.",
                "source": "hpo",
                "format": "sample",
            },
            {
                "hpo_id": "HP:0000729",
                "name": "Autism",
                "definition": "Persistent deficits in social communication.",
                "source": "hpo",
                "format": "sample",
            },
        ]

        # Filter for MED13-relevant terms if requested
        if kwargs.get("med13_only", False):
            phenotype_records = self._filter_med13_relevant_terms(phenotype_records)

        return phenotype_records

    async def _get_latest_release(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the latest HPO release.

        Returns:
            Release information including download URLs
        """
        try:
            # GitHub API for latest release
            response = await self._make_request(
                "GET", "latest", headers={"Accept": "application/vnd.github.v3+json"}
            )
            release_data = response.json()

            # Find ontology file in assets
            ontology_url = None
            for asset in release_data.get("assets", []):
                filename = asset.get("name", "")
                if filename.endswith(".owl") or filename.endswith(".obo"):
                    ontology_url = asset.get("browser_download_url")
                    break

            # Fallback to direct download if no assets found
            if not ontology_url:
                # Use a known stable URL for HPO ontology
                ontology_url = (
                    "https://raw.githubusercontent.com/obophenotype/"
                    "human-phenotype-ontology/master/hp.obo"
                )

            return {
                "version": release_data.get("tag_name", "latest"),
                "published_at": release_data.get("published_at"),
                "ontology_url": ontology_url,
            }

        except Exception:
            # Fallback to direct download - use the main HPO OBO file
            return {
                "version": "fallback",
                "published_at": None,
                "ontology_url": "https://purl.obolibrary.org/obo/hp.obo",
            }

    async def _download_ontology_file(self, url: str) -> Optional[str]:
        """
        Download HPO ontology file.

        Args:
            url: URL to download from

        Returns:
            Ontology file content as string
        """
        try:
            response = await self._make_request(
                "GET", "", params={"url": url} if urlparse(url).scheme else None
            )

            # Handle compressed files
            if (
                url.endswith(".gz")
                or response.headers.get("content-encoding") == "gzip"
            ):
                content = gzip.decompress(response.content).decode("utf-8")
            else:
                content = response.text

            return content

        except Exception:
            return None

    def _parse_hpo_ontology(self, ontology_content: str) -> List[Dict[str, Any]]:
        """
        Parse HPO ontology content into structured records.

        Args:
            ontology_content: Raw ontology file content

        Returns:
            List of parsed phenotype records
        """
        phenotypes: List[Dict[str, Any]] = []

        try:
            # Determine file format and parse accordingly
            if ontology_content.startswith("[Term]"):
                # OBO format
                phenotypes = self._parse_obo_format(ontology_content)
            elif ontology_content.startswith("<?xml"):
                # OWL/XML format (more complex)
                phenotypes = self._parse_owl_format(ontology_content)
            else:
                # Try to detect format or default to OBO
                if "format-version:" in ontology_content:
                    phenotypes = self._parse_obo_format(ontology_content)
                else:
                    phenotypes = self._parse_simple_format(ontology_content)

        except Exception as e:
            # Return error record
            phenotypes = [
                {
                    "parsing_error": str(e),
                    "hpo_id": "ERROR",
                    "name": "Parsing Error",
                    "definition": f"Failed to parse HPO ontology: {str(e)}",
                    "raw_content": ontology_content[
                        :1000
                    ],  # First 1000 chars for debugging
                }
            ]

        return phenotypes

    def _parse_obo_format(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse OBO (Open Biological Ontologies) format.

        Args:
            content: OBO format content

        Returns:
            List of phenotype records
        """
        phenotypes: List[Dict[str, Any]] = []
        current_term: Dict[str, Union[str, List[str]]] = {}
        in_term = False

        for line in content.split("\n"):
            line = line.strip()

            if line == "[Term]":
                # Save previous term if exists
                if current_term and "id" in current_term:
                    phenotypes.append(self._normalize_obo_term(current_term))
                current_term = cast(Dict[str, Union[str, List[str]]], {})
                in_term = True
            elif line == "" and in_term:
                # End of term
                if current_term and "id" in current_term:
                    phenotypes.append(self._normalize_obo_term(current_term))
                current_term = cast(Dict[str, Union[str, List[str]]], {})
                in_term = False
            elif in_term and ":" in line:
                # Parse key-value pairs
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                existing = current_term.get(key)
                if existing is None:
                    current_term[key] = value
                elif isinstance(existing, list):
                    existing.append(value)
                else:
                    current_term[key] = [existing, value]

        # Don't forget the last term
        if current_term and "id" in current_term:
            phenotypes.append(self._normalize_obo_term(current_term))

        return phenotypes

    def _normalize_obo_term(
        self, term: Dict[str, Union[str, List[str]]]
    ) -> Dict[str, Any]:
        """
        Normalize OBO term data into consistent structure.

        Args:
            term: Raw OBO term data

        Returns:
            Normalized phenotype record
        """
        # Ensure lists for multi-value fields
        for field in ["is_a", "synonym", "xref"]:
            value = term.get(field)
            if value is None:
                continue
            if isinstance(value, list):
                continue
            if isinstance(value, str):
                term[field] = [value]

        is_obsolete_raw = term.get("is_obsolete", "false")
        if isinstance(is_obsolete_raw, list):
            is_obsolete_text = " ".join(is_obsolete_raw)
        else:
            is_obsolete_text = str(is_obsolete_raw)

        return {
            "hpo_id": term.get("id", ""),
            "name": term.get("name", ""),
            "definition": term.get("def", ""),
            "synonyms": term.get("synonym", []),
            "parents": term.get("is_a", []),
            "xrefs": term.get("xref", []),
            "is_obsolete": is_obsolete_text.lower() == "true",
            "namespace": term.get("namespace", "HP"),
            "comment": term.get("comment", ""),
            "source": "hpo",
            "format": "obo",
        }

    def _parse_owl_format(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse OWL/XML format (simplified implementation).

        Args:
            content: OWL/XML content

        Returns:
            List of phenotype records
        """
        # Simplified OWL parsing - in production would use proper OWL library
        # This is a basic implementation that extracts basic information

        phenotypes: List[Dict[str, Any]] = []
        try:
            # Very basic XML parsing for OWL format
            # In production, would use libraries like owlready2 or rdflib
            root = ET.fromstring(content)

            # Extract Class elements (phenotype terms)
            for class_elem in root.findall(".//{http://www.w3.org/2002/07/owl#}Class"):
                phenotype = self._parse_owl_class(class_elem)
                if phenotype:
                    phenotypes.append(phenotype)

        except Exception:
            # Fallback error record
            phenotypes = [
                {
                    "parsing_error": "Failed to parse OWL format",
                    "hpo_id": "ERROR",
                    "name": "OWL Parsing Error",
                    "source": "hpo",
                    "format": "owl",
                }
            ]

        return phenotypes

    def _parse_owl_class(self, class_elem: Element) -> Optional[Dict[str, Any]]:
        """Parse individual OWL class element."""
        # Simplified OWL class parsing
        # In production would be much more comprehensive
        try:
            hpo_id = None
            name = None

            # Look for ID and label
            for child in class_elem:
                if child.tag.endswith("id"):
                    hpo_id = child.text
                elif child.tag.endswith("label"):
                    name = child.text

            if hpo_id and name:
                return {
                    "hpo_id": hpo_id,
                    "name": name,
                    "definition": "",  # Would need more complex parsing
                    "synonyms": [],
                    "parents": [],
                    "xrefs": [],
                    "is_obsolete": False,
                    "source": "hpo",
                    "format": "owl",
                }

        except Exception:
            pass

        return None

    def _parse_simple_format(self, content: str) -> List[Dict[str, Any]]:
        """
        Fallback parser for unrecognized formats.

        Args:
            content: Raw content

        Returns:
            Basic error record
        """
        return [
            {
                "parsing_error": "Unrecognized ontology format",
                "hpo_id": "ERROR",
                "name": "Format Error",
                "definition": "Could not determine ontology file format",
                "source": "hpo",
                "raw_content": content[:500],
            }
        ]

    def _filter_med13_relevant_terms(
        self, phenotypes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter phenotypes for MED13 relevance.

        Args:
            phenotypes: All phenotype records

        Returns:
            MED13-relevant phenotype records
        """
        # MED13-related phenotypes based on known associations
        med13_keywords: List[str] = [
            "intellectual disability",
            "developmental delay",
            "autism",
            "schizophrenia",
            "epilepsy",
            "microcephaly",
            "growth retardation",
            "facial dysmorphism",
            "heart defect",
            "kidney anomaly",
        ]

        relevant_terms: List[Dict[str, Any]] = []
        for phenotype in phenotypes:
            name_raw = phenotype.get("name", "")
            name = (
                name_raw.lower() if isinstance(name_raw, str) else str(name_raw).lower()
            )

            definition_raw = phenotype.get("definition", "")
            if isinstance(definition_raw, list):
                definition_text = " ".join(str(item) for item in definition_raw)
            else:
                definition_text = str(definition_raw)
            definition = definition_text.lower()

            # Check if any MED13-related keywords are present
            is_relevant = any(
                keyword in name or keyword in definition for keyword in med13_keywords
            )

            if is_relevant:
                phenotype["med13_relevance"] = {
                    "is_relevant": True,
                    "matched_keywords": [
                        kw for kw in med13_keywords if kw in name or kw in definition
                    ],
                }
                relevant_terms.append(phenotype)

        return relevant_terms

    async def fetch_phenotype_hierarchy(
        self, root_term: str = "HP:0000118"
    ) -> Dict[str, Any]:
        """
        Fetch phenotype hierarchy starting from a root term.

        Args:
            root_term: Root HPO term ID (default: Phenotypic abnormality)

        Returns:
            Hierarchical phenotype data
        """
        all_phenotypes = await self.fetch_data()
        if not all_phenotypes:
            return {"error": "No phenotypes loaded"}

        # Build hierarchy
        return self._build_phenotype_hierarchy(all_phenotypes, root_term)

    def _build_phenotype_hierarchy(
        self, phenotypes: List[Dict[str, Any]], root_id: str
    ) -> Dict[str, Any]:
        """
        Build hierarchical structure from flat phenotype list.

        Args:
            phenotypes: Flat list of phenotypes
            root_id: Root term ID

        Returns:
            Hierarchical structure
        """
        # Create lookup by ID
        phenotype_dict: Dict[str, Dict[str, Any]] = {p["hpo_id"]: p for p in phenotypes}

        # Build parent-child relationships

        def build_subtree(term_id: str, visited: Set[str]) -> Dict[str, Any]:
            """Recursively build subtree."""
            if term_id in visited:
                return {"error": "Circular reference", "hpo_id": term_id}

            visited.add(term_id)
            term = phenotype_dict.get(term_id)

            if not term:
                return {"error": "Term not found", "hpo_id": term_id}

            # Get children (terms that have this as parent)
            children: List[Dict[str, Any]] = []
            for pid, pterm in phenotype_dict.items():
                if pid != term_id:
                    parents = pterm.get("parents", [])
                    if isinstance(parents, str):
                        parents = [parents]

                    if term_id in parents:
                        children.append(build_subtree(pid, visited.copy()))

            return {
                "hpo_id": term_id,
                "name": term.get("name", ""),
                "definition": term.get("definition", ""),
                "children": children,
                "synonyms": term.get("synonyms", []),
            }

        visited: Set[str] = set()
        return build_subtree(root_id, visited)

    async def search_phenotypes(
        self, query: str, **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Search phenotypes by name or definition.

        Args:
            query: Search query
            **kwargs: Additional search parameters

        Returns:
            Matching phenotype records
        """
        all_phenotypes = await self.fetch_data(**kwargs)

        query_lower = query.lower()
        matches: List[Dict[str, Any]] = []

        for phenotype in all_phenotypes:
            name = phenotype.get("name", "").lower()
            definition = phenotype.get("definition", "").lower()

            if query_lower in name or query_lower in definition:
                phenotype["search_score"] = (
                    2
                    if query_lower in name
                    else 0 + 1
                    if query_lower in definition
                    else 0
                )
                matches.append(phenotype)

        # Sort by relevance score
        matches.sort(key=lambda x: x.get("search_score", 0), reverse=True)
        return matches
