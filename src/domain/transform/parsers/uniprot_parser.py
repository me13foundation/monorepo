"""
UniProt XML parser for protein data.

Parses UniProt XML data into structured protein records with
sequence information, annotations, functions, and cross-references.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ProteinExistence(Enum):
    """Protein existence evidence levels."""

    EVIDENCE_AT_PROTEIN_LEVEL = 1
    EVIDENCE_AT_TRANSCRIPT_LEVEL = 2
    INFERRED_FROM_HOMOLOGY = 3
    PREDICTED = 4
    UNCERTAIN = 5


class UniProtStatus(Enum):
    """UniProt entry status."""

    REVIEWED = "reviewed"
    UNREVIEWED = "unreviewed"


@dataclass
class UniProtGene:
    """Structured representation of gene information."""

    name: str
    synonyms: List[str]
    locus: Optional[str]


@dataclass
class UniProtOrganism:
    """Structured representation of organism information."""

    scientific_name: str
    common_name: Optional[str]
    taxon_id: str
    lineage: List[str]


@dataclass
class UniProtSequence:
    """Structured representation of protein sequence."""

    length: int
    mass: Optional[int]
    checksum: Optional[str]
    modified: Optional[str]
    version: int


@dataclass
class UniProtFunction:
    """Structured representation of protein function."""

    description: str
    evidence: Optional[str]


@dataclass
class UniProtFeature:
    """Structured representation of protein features."""

    type: str
    description: Optional[str]
    position: Optional[int]
    begin: Optional[int]
    end: Optional[int]


@dataclass
class UniProtReference:
    """Structured representation of literature references."""

    title: Optional[str]
    authors: List[str]
    journal: Optional[str]
    publication_date: Optional[str]
    pubmed_id: Optional[str]
    doi: Optional[str]


@dataclass
class UniProtProtein:
    """Structured representation of a UniProt protein entry."""

    primary_accession: str
    entry_name: str
    protein_name: str

    # Status and existence
    status: UniProtStatus
    existence: ProteinExistence

    # Gene information
    genes: List[UniProtGene]

    # Organism
    organism: UniProtOrganism

    # Sequence
    sequence: UniProtSequence

    # Functions and features
    functions: List[UniProtFunction]
    subcellular_locations: List[str]
    features: List[UniProtFeature]

    # References
    references: List[UniProtReference]

    # Cross-references
    database_references: Dict[str, List[str]]

    # Keywords
    keywords: List[str]

    # Comments
    comments: Dict[str, List[str]]

    # Raw data for reference
    raw_data: Dict[str, Any]


class UniProtParser:
    """
    Parser for UniProt XML data.

    Extracts and structures protein information from UniProt XML responses,
    including sequences, functions, annotations, and cross-references.
    """

    def __init__(self) -> None:
        self.protein_cache: Dict[str, UniProtProtein] = {}

    def parse_raw_data(self, raw_data: Dict[str, Any]) -> Optional[UniProtProtein]:
        """
        Parse raw UniProt data into structured protein record.

        Args:
            raw_data: Raw data dictionary from UniProt ingestor

        Returns:
            Structured UniProtProtein object or None if parsing fails
        """
        try:
            primary_accession = raw_data.get("primaryAccession")
            entry_name = raw_data.get("uniProtkbId")

            if not primary_accession:
                return None

            # Extract structured information
            protein_name = self._extract_protein_name(raw_data)
            status = self._extract_status(raw_data)
            existence = self._extract_existence(raw_data)
            genes = self._extract_genes(raw_data)
            organism = self._extract_organism(raw_data)
            sequence = self._extract_sequence(raw_data)
            functions = self._extract_functions(raw_data)
            subcellular_locations = self._extract_subcellular_locations(raw_data)
            features = self._extract_features(raw_data)
            references = self._extract_references(raw_data)
            database_references = self._extract_database_references(raw_data)
            keywords = self._extract_keywords(raw_data)
            comments = self._extract_comments(raw_data)

            protein = UniProtProtein(
                primary_accession=primary_accession,
                entry_name=entry_name or primary_accession,
                protein_name=protein_name,
                status=status,
                existence=existence,
                genes=genes,
                organism=organism,
                sequence=sequence,
                functions=functions,
                subcellular_locations=subcellular_locations,
                features=features,
                references=references,
                database_references=database_references,
                keywords=keywords,
                comments=comments,
                raw_data=raw_data,
            )

            self.protein_cache[primary_accession] = protein
            return protein

        except Exception as e:
            # Log error but don't fail completely
            print(
                f"Error parsing UniProt record {raw_data.get('primaryAccession')}: {e}"
            )
            return None

    def parse_batch(self, raw_data_list: List[Dict[str, Any]]) -> List[UniProtProtein]:
        """
        Parse multiple UniProt records.

        Args:
            raw_data_list: List of raw UniProt data dictionaries

        Returns:
            List of parsed UniProtProtein objects
        """
        parsed_proteins = []
        for raw_data in raw_data_list:
            protein = self.parse_raw_data(raw_data)
            if protein:
                parsed_proteins.append(protein)

        return parsed_proteins

    def _extract_protein_name(self, data: Dict[str, Any]) -> str:
        """Extract protein name from data."""
        protein_desc = data.get("proteinDescription", {})
        recommended = protein_desc.get("recommendedName", {})
        full_name = recommended.get("fullName", {})

        name_value = full_name.get("value")
        if isinstance(name_value, str):
            return name_value

        # Fallback to entry name
        entry_name = data.get("uniProtkbId", "Unknown Protein")
        if isinstance(entry_name, str):
            return entry_name

        # Ensure we always return a string even if unexpected types appear
        return "Unknown Protein"

    def _extract_status(self, data: Dict[str, Any]) -> UniProtStatus:
        """Extract entry status."""
        # This information might not be in the current data structure
        # Default to unreviewed for now
        return UniProtStatus.UNREVIEWED

    def _extract_existence(self, data: Dict[str, Any]) -> ProteinExistence:
        """Extract protein existence evidence."""
        # This information might not be in the current data structure
        # Default to predicted for now
        return ProteinExistence.PREDICTED

    def _extract_genes(self, data: Dict[str, Any]) -> List[UniProtGene]:
        """Extract gene information."""
        genes = []

        for gene_data in data.get("genes", []):
            gene_name_data = gene_data.get("geneName", {})
            name = gene_name_data.get("value")
            if name:
                gene = UniProtGene(
                    name=name,
                    synonyms=[],  # Could extract from other fields if available
                    locus=None,
                )
                genes.append(gene)

        return genes

    def _extract_organism(self, data: Dict[str, Any]) -> UniProtOrganism:
        """Extract organism information."""
        org_data = data.get("organism", {})

        return UniProtOrganism(
            scientific_name=org_data.get("scientificName", "Unknown"),
            common_name=org_data.get("commonName"),
            taxon_id=org_data.get("taxonId", ""),
            lineage=org_data.get("lineage", []),
        )

    def _extract_sequence(self, data: Dict[str, Any]) -> UniProtSequence:
        """Extract sequence information."""
        seq_data = data.get("sequence", {})

        return UniProtSequence(
            length=seq_data.get("length", 0),
            mass=seq_data.get("mass"),
            checksum=seq_data.get("checksum"),
            modified=seq_data.get("modified"),
            version=seq_data.get("version", 1),
        )

    def _extract_functions(self, data: Dict[str, Any]) -> List[UniProtFunction]:
        """Extract protein functions."""
        functions = []

        for comment in data.get("comments", []):
            if comment.get("commentType") == "FUNCTION":
                for text_data in comment.get("texts", []):
                    func = UniProtFunction(
                        description=text_data.get("value", ""), evidence=None
                    )
                    functions.append(func)

        return functions

    def _extract_subcellular_locations(self, data: Dict[str, Any]) -> List[str]:
        """Extract subcellular locations."""
        locations = []

        for comment in data.get("comments", []):
            if comment.get("commentType") == "SUBCELLULAR LOCATION":
                for location_data in comment.get("subcellularLocations", []):
                    location_value = location_data.get("location", {}).get("value")
                    if location_value:
                        locations.append(location_value)

        return locations

    def _extract_features(self, data: Dict[str, Any]) -> List[UniProtFeature]:
        """Extract protein features."""
        features = []

        for feature_data in data.get("features", []):
            feature = UniProtFeature(
                type=feature_data.get("type", ""),
                description=feature_data.get("description"),
                position=None,  # Could extract from location data
                begin=None,
                end=None,
            )
            features.append(feature)

        return features

    def _extract_references(self, data: Dict[str, Any]) -> List[UniProtReference]:
        """Extract literature references."""
        references = []

        for ref_data in data.get("references", []):
            citation = ref_data.get("citation", {})

            reference = UniProtReference(
                title=citation.get("title"),
                authors=citation.get("authors", []),
                journal=None,  # Not always available in current data
                publication_date=citation.get("publicationDate", {}).get("value"),
                pubmed_id=None,  # Could extract from dbReferences if available
                doi=None,
            )
            references.append(reference)

        return references

    def _extract_database_references(
        self, data: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Extract database cross-references."""
        db_refs: Dict[str, List[str]] = {}

        for db_ref in data.get("dbReferences", []):
            db_type = db_ref.get("type")
            db_id = db_ref.get("id")

            if db_type and db_id:
                if db_type not in db_refs:
                    db_refs[db_type] = []
                db_refs[db_type].append(db_id)

        return db_refs

    def _extract_keywords(self, data: Dict[str, Any]) -> List[str]:
        """Extract keywords."""
        # Keywords might not be in current data structure
        return []

    def _extract_comments(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract comments by type."""
        comments: Dict[str, List[str]] = {}

        for comment in data.get("comments", []):
            comment_type = comment.get("commentType")
            if comment_type:
                if comment_type not in comments:
                    comments[comment_type] = []

                for text_data in comment.get("texts", []):
                    text_value = text_data.get("value")
                    if text_value:
                        comments[comment_type].append(text_value)

        return comments

    def validate_parsed_data(self, protein: UniProtProtein) -> List[str]:
        """
        Validate parsed UniProt protein data.

        Args:
            protein: Parsed UniProtProtein object

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not protein.primary_accession:
            errors.append("Missing primary accession")

        if not protein.protein_name:
            errors.append("Missing protein name")

        if protein.sequence.length == 0:
            errors.append("Invalid sequence length")

        if not protein.organism.scientific_name:
            errors.append("Missing organism information")

        return errors

    def get_protein_by_accession(self, accession: str) -> Optional[UniProtProtein]:
        """
        Get a cached protein by accession.

        Args:
            accession: UniProt accession number

        Returns:
            UniProtProtein object or None if not found
        """
        return self.protein_cache.get(accession)
