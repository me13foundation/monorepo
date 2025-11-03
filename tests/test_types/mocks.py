"""
Typed mock implementations for MED13 Resource Library testing.

Provides type-safe mock repositories and services for comprehensive unit testing.
"""

from typing import Dict, List, Optional, Any
from unittest.mock import MagicMock

from src.domain.entities.gene import Gene
from src.domain.entities.variant import Variant
from src.domain.entities.phenotype import Phenotype
from src.domain.entities.evidence import Evidence
from src.domain.entities.publication import Publication
from src.domain.repositories.gene_repository import GeneRepository
from src.domain.repositories.variant_repository import VariantRepository
from src.domain.repositories.phenotype_repository import PhenotypeRepository
from src.domain.repositories.evidence_repository import EvidenceRepository
from src.domain.repositories.publication_repository import PublicationRepository
from src.services.domain.gene_service import GeneService as GeneDomainService
from src.services.domain.variant_service import VariantService as VariantDomainService
from src.services.domain.evidence_service import (
    EvidenceService as EvidenceDomainService,
)

from .fixtures import (
    TestGene,
    TestVariant,
    TestPhenotype,
    TestEvidence,
    TestPublication,
)


class MockGeneRepository(GeneRepository):
    """Type-safe mock gene repository for testing."""

    def __init__(self, genes: Optional[List[TestGene]] = None):
        """
        Initialize mock repository with test data.

        Args:
            genes: List of test genes to populate repository
        """
        self._genes: Dict[int, TestGene] = {}
        self._id_counter = 1

        if genes:
            for gene in genes:
                self._genes[self._id_counter] = gene
                self._id_counter += 1

        # Mock methods for tracking calls
        self.save_gene = MagicMock()
        self.get_gene_by_id = MagicMock()
        self.get_gene_by_symbol = MagicMock()
        self.list_genes = MagicMock()
        self.update_gene = MagicMock()
        self.delete_gene = MagicMock()

    def save(self, gene: Gene) -> Gene:
        """Mock save method."""
        self.save_gene(gene)
        # Return the gene as-is for simplicity
        return gene

    def get_by_id(self, gene_id: int) -> Optional[Gene]:
        """Mock get by ID method."""
        self.get_gene_by_id(gene_id)
        if gene_id in self._genes:
            test_gene = self._genes[gene_id]
            # Convert to Gene entity (simplified)
            return Gene(
                gene_id=test_gene.gene_id,
                symbol=test_gene.symbol,
                name=test_gene.name,
                description=test_gene.description,
                gene_type=test_gene.gene_type,
                chromosome=test_gene.chromosome,
                start_position=test_gene.start_position,
                end_position=test_gene.end_position,
                ensembl_id=test_gene.ensembl_id,
                ncbi_gene_id=test_gene.ncbi_gene_id,
                uniprot_id=test_gene.uniprot_id,
            )
        return None

    def get_by_symbol(self, symbol: str) -> Optional[Gene]:
        """Mock get by symbol method."""
        self.get_gene_by_symbol(symbol)
        for test_gene in self._genes.values():
            if test_gene.symbol == symbol:
                return Gene(
                    gene_id=test_gene.gene_id,
                    symbol=test_gene.symbol,
                    name=test_gene.name,
                    description=test_gene.description,
                    gene_type=test_gene.gene_type,
                    chromosome=test_gene.chromosome,
                    start_position=test_gene.start_position,
                    end_position=test_gene.end_position,
                    ensembl_id=test_gene.ensembl_id,
                    ncbi_gene_id=test_gene.ncbi_gene_id,
                    uniprot_id=test_gene.uniprot_id,
                )
        return None

    def list_all(self) -> List[Gene]:
        """Mock list all method."""
        self.list_genes()
        return [
            Gene(
                gene_id=test_gene.gene_id,
                symbol=test_gene.symbol,
                name=test_gene.name,
                description=test_gene.description,
                gene_type=test_gene.gene_type,
                chromosome=test_gene.chromosome,
                start_position=test_gene.start_position,
                end_position=test_gene.end_position,
                ensembl_id=test_gene.ensembl_id,
                ncbi_gene_id=test_gene.ncbi_gene_id,
                uniprot_id=test_gene.uniprot_id,
            )
            for test_gene in self._genes.values()
        ]

    def update(self, gene_id: int, updates: Dict[str, Any]) -> Gene:
        """Mock update method."""
        self.update_gene(gene_id, updates)
        # Simplified: just return a mock updated gene
        if gene_id in self._genes:
            test_gene = self._genes[gene_id]
            return Gene(
                gene_id=test_gene.gene_id,
                symbol=updates.get("symbol", test_gene.symbol),
                name=updates.get("name", test_gene.name),
                description=updates.get("description", test_gene.description),
                gene_type=updates.get("gene_type", test_gene.gene_type),
                chromosome=updates.get("chromosome", test_gene.chromosome),
                start_position=updates.get("start_position", test_gene.start_position),
                end_position=updates.get("end_position", test_gene.end_position),
                ensembl_id=updates.get("ensembl_id", test_gene.ensembl_id),
                ncbi_gene_id=updates.get("ncbi_gene_id", test_gene.ncbi_gene_id),
                uniprot_id=updates.get("uniprot_id", test_gene.uniprot_id),
            )
        raise ValueError(f"Gene {gene_id} not found")

    def delete(self, gene_id: int) -> None:
        """Mock delete method."""
        self.delete_gene(gene_id)
        if gene_id in self._genes:
            del self._genes[gene_id]


class MockVariantRepository(VariantRepository):
    """Type-safe mock variant repository for testing."""

    def __init__(self, variants: Optional[List[TestVariant]] = None):
        """
        Initialize mock repository with test data.

        Args:
            variants: List of test variants to populate repository
        """
        self._variants: Dict[int, TestVariant] = {}
        self._id_counter = 1

        if variants:
            for variant in variants:
                self._variants[self._id_counter] = variant
                self._id_counter += 1

        # Mock methods for tracking calls
        self.save_variant = MagicMock()
        self.get_variant_by_id = MagicMock()
        self.list_variants = MagicMock()
        self.update_variant = MagicMock()
        self.delete_variant = MagicMock()

    def save(self, variant: Variant) -> Variant:
        """Mock save method."""
        self.save_variant(variant)
        return variant

    def get_by_id(self, variant_id: int) -> Optional[Variant]:
        """Mock get by ID method."""
        self.get_variant_by_id(variant_id)
        if variant_id in self._variants:
            test_variant = self._variants[variant_id]
            return Variant(
                variant_id=test_variant.variant_id,
                clinvar_id=test_variant.clinvar_id,
                chromosome=test_variant.chromosome,
                position=test_variant.position,
                reference_allele=test_variant.reference_allele,
                alternate_allele=test_variant.alternate_allele,
                variant_type=test_variant.variant_type,
                clinical_significance=test_variant.clinical_significance,
                gene_identifier=test_variant.gene_identifier,
                gene_database_id=test_variant.gene_database_id,
                hgvs_genomic=test_variant.hgvs_genomic,
                hgvs_protein=test_variant.hgvs_protein,
                hgvs_cdna=test_variant.hgvs_cdna,
                condition=test_variant.condition,
                review_status=test_variant.review_status,
                allele_frequency=test_variant.allele_frequency,
                gnomad_af=test_variant.gnomad_af,
            )
        return None

    def list_all(self) -> List[Variant]:
        """Mock list all method."""
        self.list_variants()
        return [
            Variant(
                variant_id=test_variant.variant_id,
                clinvar_id=test_variant.clinvar_id,
                chromosome=test_variant.chromosome,
                position=test_variant.position,
                reference_allele=test_variant.reference_allele,
                alternate_allele=test_variant.alternate_allele,
                variant_type=test_variant.variant_type,
                clinical_significance=test_variant.clinical_significance,
                gene_identifier=test_variant.gene_identifier,
                gene_database_id=test_variant.gene_database_id,
                hgvs_genomic=test_variant.hgvs_genomic,
                hgvs_protein=test_variant.hgvs_protein,
                hgvs_cdna=test_variant.hgvs_cdna,
                condition=test_variant.condition,
                review_status=test_variant.review_status,
                allele_frequency=test_variant.allele_frequency,
                gnomad_af=test_variant.gnomad_af,
            )
            for test_variant in self._variants.values()
        ]

    def update(self, variant_id: int, updates: Dict[str, Any]) -> Variant:
        """Mock update method."""
        self.update_variant(variant_id, updates)
        if variant_id in self._variants:
            test_variant = self._variants[variant_id]
            return Variant(
                variant_id=updates.get("variant_id", test_variant.variant_id),
                clinvar_id=updates.get("clinvar_id", test_variant.clinvar_id),
                chromosome=updates.get("chromosome", test_variant.chromosome),
                position=updates.get("position", test_variant.position),
                reference_allele=updates.get(
                    "reference_allele", test_variant.reference_allele
                ),
                alternate_allele=updates.get(
                    "alternate_allele", test_variant.alternate_allele
                ),
                variant_type=updates.get("variant_type", test_variant.variant_type),
                clinical_significance=updates.get(
                    "clinical_significance", test_variant.clinical_significance
                ),
                gene_identifier=updates.get(
                    "gene_identifier", test_variant.gene_identifier
                ),
                gene_database_id=updates.get(
                    "gene_database_id", test_variant.gene_database_id
                ),
                hgvs_genomic=updates.get("hgvs_genomic", test_variant.hgvs_genomic),
                hgvs_protein=updates.get("hgvs_protein", test_variant.hgvs_protein),
                hgvs_cdna=updates.get("hgvs_cdna", test_variant.hgvs_cdna),
                condition=updates.get("condition", test_variant.condition),
                review_status=updates.get("review_status", test_variant.review_status),
                allele_frequency=updates.get(
                    "allele_frequency", test_variant.allele_frequency
                ),
                gnomad_af=updates.get("gnomad_af", test_variant.gnomad_af),
            )
        raise ValueError(f"Variant {variant_id} not found")

    def delete(self, variant_id: int) -> None:
        """Mock delete method."""
        self.delete_variant(variant_id)
        if variant_id in self._variants:
            del self._variants[variant_id]


class MockPhenotypeRepository(PhenotypeRepository):
    """Type-safe mock phenotype repository for testing."""

    def __init__(self, phenotypes: Optional[List[TestPhenotype]] = None):
        """
        Initialize mock repository with test data.

        Args:
            phenotypes: List of test phenotypes to populate repository
        """
        self._phenotypes: Dict[int, TestPhenotype] = {}
        self._id_counter = 1

        if phenotypes:
            for phenotype in phenotypes:
                self._phenotypes[self._id_counter] = phenotype
                self._id_counter += 1

        # Mock methods for tracking calls
        self.save_phenotype = MagicMock()
        self.get_phenotype_by_id = MagicMock()
        self.get_phenotype_by_hpo_id = MagicMock()
        self.list_phenotypes = MagicMock()
        self.update_phenotype = MagicMock()
        self.delete_phenotype = MagicMock()

    def save(self, phenotype: Phenotype) -> Phenotype:
        """Mock save method."""
        self.save_phenotype(phenotype)
        return phenotype

    def get_by_id(self, phenotype_id: int) -> Optional[Phenotype]:
        """Mock get by ID method."""
        self.get_phenotype_by_id(phenotype_id)
        if phenotype_id in self._phenotypes:
            test_phenotype = self._phenotypes[phenotype_id]
            return Phenotype(
                hpo_id=test_phenotype.hpo_id,
                name=test_phenotype.name,
                definition=test_phenotype.definition,
                synonyms=test_phenotype.synonyms,
            )
        return None

    def get_by_hpo_id(self, hpo_id: str) -> Optional[Phenotype]:
        """Mock get by HPO ID method."""
        self.get_phenotype_by_hpo_id(hpo_id)
        for test_phenotype in self._phenotypes.values():
            if test_phenotype.hpo_id == hpo_id:
                return Phenotype(
                    hpo_id=test_phenotype.hpo_id,
                    name=test_phenotype.name,
                    definition=test_phenotype.definition,
                    synonyms=test_phenotype.synonyms,
                )
        return None

    def list_all(self) -> List[Phenotype]:
        """Mock list all method."""
        self.list_phenotypes()
        return [
            Phenotype(
                hpo_id=test_phenotype.hpo_id,
                name=test_phenotype.name,
                definition=test_phenotype.definition,
                synonyms=test_phenotype.synonyms,
            )
            for test_phenotype in self._phenotypes.values()
        ]

    def update(self, phenotype_id: int, updates: Dict[str, Any]) -> Phenotype:
        """Mock update method."""
        self.update_phenotype(phenotype_id, updates)
        if phenotype_id in self._phenotypes:
            test_phenotype = self._phenotypes[phenotype_id]
            return Phenotype(
                hpo_id=updates.get("hpo_id", test_phenotype.hpo_id),
                name=updates.get("name", test_phenotype.name),
                definition=updates.get("definition", test_phenotype.definition),
                synonyms=updates.get("synonyms", test_phenotype.synonyms),
            )
        raise ValueError(f"Phenotype {phenotype_id} not found")

    def delete(self, phenotype_id: int) -> None:
        """Mock delete method."""
        self.delete_phenotype(phenotype_id)
        if phenotype_id in self._phenotypes:
            del self._phenotypes[phenotype_id]


class MockEvidenceRepository(EvidenceRepository):
    """Type-safe mock evidence repository for testing."""

    def __init__(self, evidence_list: Optional[List[TestEvidence]] = None):
        """
        Initialize mock repository with test data.

        Args:
            evidence_list: List of test evidence to populate repository
        """
        self._evidence: Dict[int, TestEvidence] = {}
        self._id_counter = 1

        if evidence_list:
            for evidence in evidence_list:
                self._evidence[self._id_counter] = evidence
                self._id_counter += 1

        # Mock methods for tracking calls
        self.save_evidence = MagicMock()
        self.get_evidence_by_id = MagicMock()
        self.list_evidence = MagicMock()
        self.update_evidence = MagicMock()
        self.delete_evidence = MagicMock()

    def save(self, evidence: Evidence) -> Evidence:
        """Mock save method."""
        self.save_evidence(evidence)
        return evidence

    def get_by_id(self, evidence_id: int) -> Optional[Evidence]:
        """Mock get by ID method."""
        self.get_evidence_by_id(evidence_id)
        if evidence_id in self._evidence:
            test_evidence = self._evidence[evidence_id]
            return Evidence(
                variant_id=test_evidence.variant_id,
                phenotype_id=test_evidence.phenotype_id,
                description=test_evidence.description,
                evidence_level=test_evidence.evidence_level,
                evidence_type=test_evidence.evidence_type,
                confidence_score=test_evidence.confidence_score,
                source=test_evidence.source,
            )
        return None

    def list_all(self) -> List[Evidence]:
        """Mock list all method."""
        self.list_evidence()
        return [
            Evidence(
                variant_id=test_evidence.variant_id,
                phenotype_id=test_evidence.phenotype_id,
                description=test_evidence.description,
                evidence_level=test_evidence.evidence_level,
                evidence_type=test_evidence.evidence_type,
                confidence_score=test_evidence.confidence_score,
                source=test_evidence.source,
            )
            for test_evidence in self._evidence.values()
        ]

    def update(self, evidence_id: int, updates: Dict[str, Any]) -> Evidence:
        """Mock update method."""
        self.update_evidence(evidence_id, updates)
        if evidence_id in self._evidence:
            test_evidence = self._evidence[evidence_id]
            return Evidence(
                variant_id=updates.get("variant_id", test_evidence.variant_id),
                phenotype_id=updates.get("phenotype_id", test_evidence.phenotype_id),
                description=updates.get("description", test_evidence.description),
                evidence_level=updates.get(
                    "evidence_level", test_evidence.evidence_level
                ),
                evidence_type=updates.get("evidence_type", test_evidence.evidence_type),
                confidence_score=updates.get(
                    "confidence_score", test_evidence.confidence_score
                ),
                source=updates.get("source", test_evidence.source),
            )
        raise ValueError(f"Evidence {evidence_id} not found")

    def delete(self, evidence_id: int) -> None:
        """Mock delete method."""
        self.delete_evidence(evidence_id)
        if evidence_id in self._evidence:
            del self._evidence[evidence_id]


class MockPublicationRepository(PublicationRepository):
    """Type-safe mock publication repository for testing."""

    def __init__(self, publications: Optional[List[TestPublication]] = None):
        """
        Initialize mock repository with test data.

        Args:
            publications: List of test publications to populate repository
        """
        self._publications: Dict[int, TestPublication] = {}
        self._id_counter = 1

        if publications:
            for publication in publications:
                self._publications[self._id_counter] = publication
                self._id_counter += 1

        # Mock methods for tracking calls
        self.save_publication = MagicMock()
        self.get_publication_by_id = MagicMock()
        self.list_publications = MagicMock()
        self.update_publication = MagicMock()
        self.delete_publication = MagicMock()

    def save(self, publication: Publication) -> Publication:
        """Mock save method."""
        self.save_publication(publication)
        return publication

    def get_by_id(self, publication_id: int) -> Optional[Publication]:
        """Mock get by ID method."""
        self.get_publication_by_id(publication_id)
        if publication_id in self._publications:
            test_publication = self._publications[publication_id]
            return Publication(
                title=test_publication.title,
                authors=test_publication.authors,
                journal=test_publication.journal,
                publication_year=test_publication.publication_year,
                doi=test_publication.doi,
                pmid=test_publication.pmid,
                abstract=test_publication.abstract,
            )
        return None

    def list_all(self) -> List[Publication]:
        """Mock list all method."""
        self.list_publications()
        return [
            Publication(
                title=test_publication.title,
                authors=test_publication.authors,
                journal=test_publication.journal,
                publication_year=test_publication.publication_year,
                doi=test_publication.doi,
                pmid=test_publication.pmid,
                abstract=test_publication.abstract,
            )
            for test_publication in self._publications.values()
        ]

    def update(self, publication_id: int, updates: Dict[str, Any]) -> Publication:
        """Mock update method."""
        self.update_publication(publication_id, updates)
        if publication_id in self._publications:
            test_publication = self._publications[publication_id]
            return Publication(
                title=updates.get("title", test_publication.title),
                authors=updates.get("authors", test_publication.authors),
                journal=updates.get("journal", test_publication.journal),
                publication_year=updates.get(
                    "publication_year", test_publication.publication_year
                ),
                doi=updates.get("doi", test_publication.doi),
                pmid=updates.get("pmid", test_publication.pmid),
                abstract=updates.get("abstract", test_publication.abstract),
            )
        raise ValueError(f"Publication {publication_id} not found")

    def delete(self, publication_id: int) -> None:
        """Mock delete method."""
        self.delete_publication(publication_id)
        if publication_id in self._publications:
            del self._publications[publication_id]


# Factory functions for creating mock services
def create_mock_gene_service(
    genes: Optional[List[TestGene]] = None,
) -> GeneDomainService:
    """
    Create a mock gene domain service with typed repositories.

    Args:
        genes: Test genes to populate the repository

    Returns:
        Mock gene domain service
    """
    mock_repo = MockGeneRepository(genes)
    return GeneDomainService(mock_repo)


def create_mock_variant_service(
    variants: Optional[List[TestVariant]] = None,
) -> VariantDomainService:
    """
    Create a mock variant domain service with typed repositories.

    Args:
        variants: Test variants to populate the repository

    Returns:
        Mock variant domain service
    """
    mock_repo = MockVariantRepository(variants)
    return VariantDomainService(mock_repo)


def create_mock_evidence_service(
    evidence_list: Optional[List[TestEvidence]] = None,
) -> EvidenceDomainService:
    """
    Create a mock evidence domain service with typed repositories.

    Args:
        evidence_list: Test evidence to populate the repository

    Returns:
        Mock evidence domain service
    """
    mock_repo = MockEvidenceRepository(evidence_list)
    return EvidenceDomainService(mock_repo)
