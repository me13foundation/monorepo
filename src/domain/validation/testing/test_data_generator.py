"""
Test data generator for validation framework.

Provides synthetic data generation capabilities for testing validation
rules, performance benchmarking, and quality assurance testing.
"""

import random
import string
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class SyntheticDataset:
    """A synthetic dataset for testing."""

    name: str
    entity_type: str
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    quality_profile: str  # 'good', 'mixed', 'poor'


class TestDataGenerator:
    """
    Synthetic test data generator for validation testing.

    Generates realistic biomedical data for testing validation rules,
    with configurable quality profiles and data characteristics.
    """

    def __init__(self, seed: Optional[int] = None):
        self.random = random.Random(seed)

        # Data templates and patterns
        self.gene_symbols = self._load_gene_symbols()
        self.variant_notations = self._generate_variant_notations()
        self.phenotype_terms = self._load_phenotype_terms()
        self.journals = self._load_journals()

    def _load_gene_symbols(self) -> List[str]:
        """Load realistic gene symbols."""
        # HGNC-approved gene symbols (simplified list)
        return [
            "TP53",
            "BRCA1",
            "BRCA2",
            "APC",
            "MLH1",
            "MSH2",
            "MSH6",
            "PMS2",
            "RB1",
            "PTEN",
            "CDKN2A",
            "NF1",
            "NF2",
            "WT1",
            "VHL",
            "MEN1",
            "RET",
            "SDHD",
            "SDHAF2",
            "SDHC",
            "SDHB",
            "FH",
            "MET",
            "EGFR",
            "KRAS",
            "NRAS",
            "HRAS",
            "BRAF",
            "PIK3CA",
            "PTEN",
            "AKT1",
            "MTOR",
            "TP53",
            "RB1",
            "APC",
            "CTNNB1",
            "AXIN1",
            "AXIN2",
        ]

    def _generate_variant_notations(self) -> List[str]:
        """Generate realistic variant notations."""
        notations = []

        # HGVS c. notations
        for i in range(100, 1000, 50):
            for change in ["A>G", "C>T", "G>A", "T>C", "del", "ins", "dup"]:
                notations.append(f"c.{i}{change}")

        # HGVS p. notations
        amino_acids = [
            "Ala",
            "Arg",
            "Asn",
            "Asp",
            "Cys",
            "Glu",
            "Gln",
            "Gly",
            "His",
            "Ile",
            "Leu",
            "Lys",
            "Met",
            "Phe",
            "Pro",
            "Ser",
            "Thr",
            "Trp",
            "Tyr",
            "Val",
        ]

        for aa1 in amino_acids[:5]:  # Limit for performance
            for aa2 in amino_acids[:5]:
                for pos in range(100, 500, 50):
                    notations.append(f"p.{aa1}{pos}{aa2}")

        return notations

    def _load_phenotype_terms(self) -> List[str]:
        """Load realistic phenotype terms."""
        return [
            "Intellectual disability",
            "Developmental delay",
            "Seizures",
            "Autism spectrum disorder",
            "Microcephaly",
            "Macrocephaly",
            "Growth retardation",
            "Short stature",
            "Obesity",
            "Diabetes mellitus",
            "Cardiovascular disease",
            "Hypertrophic cardiomyopathy",
            "Arrhythmia",
            "Cancer predisposition",
            "Breast cancer",
            "Colorectal cancer",
            "Renal cell carcinoma",
            "Thyroid cancer",
            "Pheochromocytoma",
        ]

    def _load_journals(self) -> List[str]:
        """Load realistic journal names."""
        return [
            "Nature Genetics",
            "PLOS Genetics",
            "Human Molecular Genetics",
            "Genetics in Medicine",
            "European Journal of Human Genetics",
            "American Journal of Human Genetics",
            "Nature Medicine",
            "New England Journal of Medicine",
            "The Lancet",
            "JAMA",
        ]

    def generate_gene_dataset(
        self, size: int, quality_profile: str = "good"
    ) -> SyntheticDataset:
        """
        Generate synthetic gene dataset.

        Args:
            size: Number of gene records to generate
            quality_profile: Quality profile ('good', 'mixed', 'poor')

        Returns:
            SyntheticDataset with gene data
        """
        data = []

        for i in range(size):
            gene = self._generate_gene_record(i, quality_profile)
            data.append(gene)

        metadata = {
            "generation_date": datetime.now().isoformat(),
            "size": size,
            "quality_distribution": self._get_quality_distribution(
                quality_profile, size
            ),
            "entity_type": "gene",
        }

        return SyntheticDataset(
            name=f"gene_dataset_{quality_profile}_{size}",
            entity_type="gene",
            data=data,
            metadata=metadata,
            quality_profile=quality_profile,
        )

    def generate_variant_dataset(
        self, size: int, quality_profile: str = "good"
    ) -> SyntheticDataset:
        """
        Generate synthetic variant dataset.

        Args:
            size: Number of variant records to generate
            quality_profile: Quality profile

        Returns:
            SyntheticDataset with variant data
        """
        data = []

        for i in range(size):
            variant = self._generate_variant_record(i, quality_profile)
            data.append(variant)

        metadata = {
            "generation_date": datetime.now().isoformat(),
            "size": size,
            "quality_distribution": self._get_quality_distribution(
                quality_profile, size
            ),
            "entity_type": "variant",
        }

        return SyntheticDataset(
            name=f"variant_dataset_{quality_profile}_{size}",
            entity_type="variant",
            data=data,
            metadata=metadata,
            quality_profile=quality_profile,
        )

    def generate_phenotype_dataset(
        self, size: int, quality_profile: str = "good"
    ) -> SyntheticDataset:
        """
        Generate synthetic phenotype dataset.

        Args:
            size: Number of phenotype records to generate
            quality_profile: Quality profile

        Returns:
            SyntheticDataset with phenotype data
        """
        data = []

        for i in range(size):
            phenotype = self._generate_phenotype_record(i, quality_profile)
            data.append(phenotype)

        metadata = {
            "generation_date": datetime.now().isoformat(),
            "size": size,
            "quality_distribution": self._get_quality_distribution(
                quality_profile, size
            ),
            "entity_type": "phenotype",
        }

        return SyntheticDataset(
            name=f"phenotype_dataset_{quality_profile}_{size}",
            entity_type="phenotype",
            data=data,
            metadata=metadata,
            quality_profile=quality_profile,
        )

    def generate_publication_dataset(
        self, size: int, quality_profile: str = "good"
    ) -> SyntheticDataset:
        """
        Generate synthetic publication dataset.

        Args:
            size: Number of publication records to generate
            quality_profile: Quality profile

        Returns:
            SyntheticDataset with publication data
        """
        data = []

        for i in range(size):
            publication = self._generate_publication_record(i, quality_profile)
            data.append(publication)

        metadata = {
            "generation_date": datetime.now().isoformat(),
            "size": size,
            "quality_distribution": self._get_quality_distribution(
                quality_profile, size
            ),
            "entity_type": "publication",
        }

        return SyntheticDataset(
            name=f"publication_dataset_{quality_profile}_{size}",
            entity_type="publication",
            data=data,
            metadata=metadata,
            quality_profile=quality_profile,
        )

    def _generate_gene_record(self, index: int, quality_profile: str) -> Dict[str, Any]:
        """Generate a single gene record."""
        # Base data
        symbol = self.random.choice(self.gene_symbols)
        hgnc_id = f"HGNC:{self.random.randint(10000, 50000)}"

        record = {
            "symbol": symbol,
            "hgnc_id": hgnc_id,
            "name": f"{symbol} gene",
            "source": "synthetic",
            "confidence_score": self._generate_confidence_score(quality_profile),
        }

        # Add quality-specific issues
        if quality_profile == "poor":
            # Introduce errors
            if self.random.random() < 0.3:  # 30% chance
                record["symbol"] = record["symbol"].lower()  # Wrong case
            if self.random.random() < 0.2:  # 20% chance
                record["hgnc_id"] = record["hgnc_id"].replace(
                    "HGNC:", "hgnc:"
                )  # Wrong case
        elif quality_profile == "mixed":
            # Mix of good and poor quality
            if self.random.random() < 0.1:  # 10% chance
                record["symbol"] = "INVALID_SYMBOL"

        # Add optional fields
        if self.random.random() < 0.7:
            record["chromosome"] = f"chr{self.random.randint(1, 22)}"
        if self.random.random() < 0.5:
            record["start_position"] = self.random.randint(1000000, 200000000)
        if self.random.random() < 0.5:
            record["end_position"] = record.get(
                "start_position", 1000000
            ) + self.random.randint(1000, 100000)

        return record

    def _generate_variant_record(
        self, index: int, quality_profile: str
    ) -> Dict[str, Any]:
        """Generate a single variant record."""
        record = {
            "clinvar_id": f"{self.random.randint(100000, 999999)}",
            "variant_id": f"VCV{self.random.randint(100000, 999999)}",
            "variation_name": self.random.choice(self.variant_notations),
            "gene_symbol": self.random.choice(self.gene_symbols),
            "chromosome": f"{self.random.randint(1, 22)}",
            "start_position": self.random.randint(1000000, 200000000),
            "reference_allele": self.random.choice(["A", "C", "G", "T"]),
            "alternate_allele": self.random.choice(["A", "C", "G", "T"]),
            "clinical_significance": self.random.choice(
                [
                    "Pathogenic",
                    "Likely pathogenic",
                    "Uncertain significance",
                    "Likely benign",
                    "Benign",
                ]
            ),
            "source": "synthetic",
            "confidence_score": self._generate_confidence_score(quality_profile),
        }

        # Add quality-specific issues
        if quality_profile == "poor":
            if self.random.random() < 0.4:
                record["variation_name"] = "invalid_notation"
            if self.random.random() < 0.3:
                record["chromosome"] = "invalid_chromosome"
        elif quality_profile == "mixed":
            if self.random.random() < 0.1:
                record["clinical_significance"] = "invalid_significance"

        return record

    def _generate_phenotype_record(
        self, index: int, quality_profile: str
    ) -> Dict[str, Any]:
        """Generate a single phenotype record."""
        hpo_number = self.random.randint(1, 9999999)
        hpo_id = f"HP:{hpo_number:07d}"
        name = self.random.choice(self.phenotype_terms)

        record = {
            "hpo_id": hpo_id,
            "name": name,
            "definition": f"A condition characterized by {name.lower()}",
            "source": "synthetic",
            "confidence_score": self._generate_confidence_score(quality_profile),
        }

        # Add quality-specific issues
        if quality_profile == "poor":
            if self.random.random() < 0.3:
                record["hpo_id"] = record["hpo_id"].replace("HP:", "hp:")  # Wrong case
            if self.random.random() < 0.2:
                record["name"] = record["name"].lower()  # Wrong case
        elif quality_profile == "mixed":
            if self.random.random() < 0.1:
                record["hpo_id"] = "INVALID_ID"

        return record

    def _generate_publication_record(
        self, index: int, quality_profile: str
    ) -> Dict[str, Any]:
        """Generate a single publication record."""
        pubmed_id = self.random.randint(10000000, 39999999)

        record = {
            "pubmed_id": str(pubmed_id),
            "title": self._generate_publication_title(),
            "authors": [
                self._generate_author_name() for _ in range(self.random.randint(1, 8))
            ],
            "journal": self.random.choice(self.journals),
            "publication_date": f"{self.random.randint(2000, 2023)}-{self.random.randint(1, 12):02d}-{self.random.randint(1, 28):02d}",
            "doi": f"10.{self.random.randint(1000, 9999)}/{self.random.choice(string.ascii_letters)}{self.random.randint(1000, 9999)}",
            "source": "synthetic",
            "confidence_score": self._generate_confidence_score(quality_profile),
        }

        # Add quality-specific issues
        if quality_profile == "poor":
            if self.random.random() < 0.3:
                record["doi"] = "invalid_doi"
            if self.random.random() < 0.2:
                record["pubmed_id"] = "invalid_id"
        elif quality_profile == "mixed":
            if self.random.random() < 0.1:
                record["publication_date"] = "invalid_date"

        return record

    def _generate_publication_title(self) -> str:
        """Generate a realistic publication title."""
        templates = [
            "Genetic analysis of {gene} in {disease}",
            "Identification of {gene} mutations in patients with {phenotype}",
            "Clinical and genetic characteristics of {disease}",
            "Novel {gene} variants associated with {phenotype}",
            "Molecular genetics of {disease}: a review",
        ]

        template = self.random.choice(templates)
        gene = self.random.choice(self.gene_symbols)
        disease = self.random.choice(self.phenotype_terms)
        phenotype = disease

        return template.format(gene=gene, disease=disease, phenotype=phenotype)

    def _generate_author_name(self) -> str:
        """Generate a realistic author name."""
        first_names = [
            "John",
            "Jane",
            "Michael",
            "Sarah",
            "David",
            "Emma",
            "Robert",
            "Lisa",
        ]
        last_names = [
            "Smith",
            "Johnson",
            "Williams",
            "Brown",
            "Jones",
            "Garcia",
            "Miller",
            "Davis",
        ]

        return f"{self.random.choice(first_names)} {self.random.choice(last_names)}"

    def _generate_confidence_score(self, quality_profile: str) -> float:
        """Generate confidence score based on quality profile."""
        if quality_profile == "good":
            return self.random.uniform(0.8, 1.0)
        elif quality_profile == "mixed":
            return self.random.uniform(0.4, 0.9)
        else:  # poor
            return self.random.uniform(0.1, 0.6)

    def _get_quality_distribution(
        self, quality_profile: str, size: int
    ) -> Dict[str, int]:
        """Get quality distribution for the dataset."""
        if quality_profile == "good":
            return {"high_quality": size, "medium_quality": 0, "low_quality": 0}
        elif quality_profile == "mixed":
            return {
                "high_quality": int(size * 0.5),
                "medium_quality": int(size * 0.3),
                "low_quality": int(size * 0.2),
            }
        else:  # poor
            return {
                "high_quality": 0,
                "medium_quality": int(size * 0.3),
                "low_quality": int(size * 0.7),
            }

    def generate_comprehensive_test_suite(self) -> Dict[str, List[SyntheticDataset]]:
        """
        Generate a comprehensive test suite with multiple datasets.

        Returns:
            Dictionary with datasets for different entity types and quality profiles
        """
        suite = {}

        # Standard sizes for testing
        sizes = [100, 500, 1000]

        for entity_type in ["gene", "variant", "phenotype", "publication"]:
            suite[entity_type] = []

            for quality_profile in ["good", "mixed", "poor"]:
                for size in sizes:
                    if entity_type == "gene":
                        dataset = self.generate_gene_dataset(size, quality_profile)
                    elif entity_type == "variant":
                        dataset = self.generate_variant_dataset(size, quality_profile)
                    elif entity_type == "phenotype":
                        dataset = self.generate_phenotype_dataset(size, quality_profile)
                    else:  # publication
                        dataset = self.generate_publication_dataset(
                            size, quality_profile
                        )

                    suite[entity_type].append(dataset)

        return suite

    def export_dataset(
        self, dataset: SyntheticDataset, filepath: Path, format: str = "json"
    ):
        """
        Export synthetic dataset to file.

        Args:
            dataset: Dataset to export
            filepath: Path to export file
            format: Export format ("json", "csv")
        """
        if format == "json":
            import json

            data = {"metadata": dataset.metadata, "data": dataset.data}
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
        elif format == "csv":
            self._export_csv_dataset(dataset, filepath)

    def _export_csv_dataset(self, dataset: SyntheticDataset, filepath: Path):
        """Export dataset in CSV format."""
        if not dataset.data:
            return

        # Get all unique keys
        all_keys = set()
        for record in dataset.data:
            all_keys.update(record.keys())

        fieldnames = sorted(all_keys)

        with open(filepath, "w") as f:
            # Write header
            f.write(",".join(fieldnames) + "\n")

            # Write data
            for record in dataset.data:
                row = []
                for field in fieldnames:
                    value = record.get(field, "")
                    # Escape commas and quotes in CSV
                    if isinstance(value, str) and ("," in value or '"' in value):
                        value = f'"{value.replace(chr(34), chr(34) + chr(34))}"'
                    row.append(str(value))
                f.write(",".join(row) + "\n")

    def generate_edge_cases(self, entity_type: str) -> List[Dict[str, Any]]:
        """
        Generate edge case data for testing.

        Args:
            entity_type: Type of entity

        Returns:
            List of edge case records
        """
        edge_cases = []

        if entity_type == "gene":
            edge_cases = [
                {"symbol": "", "source": "test"},  # Empty symbol
                {"symbol": "A" * 50, "source": "test"},  # Very long symbol
                {"symbol": "gene@#$", "source": "test"},  # Invalid characters
                {"symbol": "123GENE", "source": "test"},  # Starts with number
                {"hgnc_id": "HGNC:abc", "source": "test"},  # Invalid HGNC ID
            ]
        elif entity_type == "variant":
            edge_cases = [
                {"variation_name": "", "source": "test"},  # Empty notation
                {"chromosome": "25", "source": "test"},  # Invalid chromosome
                {
                    "clinical_significance": "unknown_significance",
                    "source": "test",
                },  # Invalid significance
            ]
        elif entity_type == "phenotype":
            edge_cases = [
                {"hpo_id": "HP:123", "source": "test"},  # Too short HPO ID
                {"hpo_id": "HP:ABCDEFG", "source": "test"},  # Non-numeric HPO ID
                {"name": "", "source": "test"},  # Empty name
            ]
        elif entity_type == "publication":
            edge_cases = [
                {"pubmed_id": "abc", "source": "test"},  # Non-numeric PubMed ID
                {"doi": "invalid_doi", "source": "test"},  # Invalid DOI
                {"publication_date": "invalid_date", "source": "test"},  # Invalid date
            ]

        return edge_cases
