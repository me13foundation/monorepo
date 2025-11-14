"""
Typed mock implementations for MED13 Resource Library testing.

Provides type-safe mock repositories and services for comprehensive unit testing.
"""

from typing import TypedDict
from unittest.mock import MagicMock

from src.application.services.evidence_service import EvidenceApplicationService
from src.application.services.gene_service import GeneApplicationService
from src.application.services.variant_service import VariantApplicationService
from src.domain.entities.evidence import Evidence
from src.domain.entities.gene import Gene
from src.domain.entities.phenotype import Phenotype
from src.domain.entities.publication import Publication
from src.domain.entities.variant import Variant
from src.domain.repositories.evidence_repository import EvidenceRepository
from src.domain.repositories.gene_repository import GeneRepository
from src.domain.repositories.phenotype_repository import PhenotypeRepository
from src.domain.repositories.publication_repository import PublicationRepository
from src.domain.repositories.variant_repository import VariantRepository
from src.domain.services.evidence_domain_service import EvidenceDomainService
from src.domain.services.gene_domain_service import GeneDomainService
from src.domain.services.variant_domain_service import VariantDomainService
from src.type_definitions.common import (
    EvidenceUpdate,
    GeneUpdate,
    JSONObject,
    PhenotypeUpdate,
    PublicationUpdate,
    VariantUpdate,
)

from .fixtures import (
    TestEvidence,
    TestGene,
    TestPhenotype,
    TestPublication,
    TestVariant,
)


class MockGeneRepository(GeneRepository):
    """Type-safe mock gene repository for testing."""

    def __init__(self, genes: list[TestGene] | None = None):
        """
        Initialize mock repository with test data.

        Args:
            genes: List of test genes to populate repository
        """
        self._genes: dict[int, TestGene] = {}
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

    def get_by_id(self, gene_id: int) -> Gene | None:
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

    def get_by_symbol(self, symbol: str) -> Gene | None:
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

    def list_all(self) -> list[Gene]:
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

    def update(self, gene_id: int, updates: GeneUpdate) -> Gene:
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

    def __init__(self, variants: list[TestVariant] | None = None):
        """
        Initialize mock repository with test data.

        Args:
            variants: List of test variants to populate repository
        """
        self._variants: dict[int, TestVariant] = {}
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

    def get_by_id(self, variant_id: int) -> Variant | None:
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

    def list_all(self) -> list[Variant]:
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

    def update(self, variant_id: int, updates: VariantUpdate) -> Variant:
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
                    "reference_allele",
                    test_variant.reference_allele,
                ),
                alternate_allele=updates.get(
                    "alternate_allele",
                    test_variant.alternate_allele,
                ),
                variant_type=updates.get("variant_type", test_variant.variant_type),
                clinical_significance=updates.get(
                    "clinical_significance",
                    test_variant.clinical_significance,
                ),
                gene_identifier=updates.get(
                    "gene_identifier",
                    test_variant.gene_identifier,
                ),
                gene_database_id=updates.get(
                    "gene_database_id",
                    test_variant.gene_database_id,
                ),
                hgvs_genomic=updates.get("hgvs_genomic", test_variant.hgvs_genomic),
                hgvs_protein=updates.get("hgvs_protein", test_variant.hgvs_protein),
                hgvs_cdna=updates.get("hgvs_cdna", test_variant.hgvs_cdna),
                condition=updates.get("condition", test_variant.condition),
                review_status=updates.get("review_status", test_variant.review_status),
                allele_frequency=updates.get(
                    "allele_frequency",
                    test_variant.allele_frequency,
                ),
                gnomad_af=updates.get("gnomad_af", test_variant.gnomad_af),
            )
        raise ValueError(f"Variant {variant_id} not found")

    def delete(self, variant_id: int) -> None:
        """Mock delete method."""
        self.delete_variant(variant_id)
        if variant_id in self._variants:
            del self._variants[variant_id]

    def find_pathogenic_variants(
        self,
        limit: int | None = None,
    ) -> list[Variant]:
        """Return variants marked as pathogenic or likely pathogenic."""
        pathogenic_statuses = {"pathogenic", "likely_pathogenic"}
        variants = [
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
            if test_variant.clinical_significance in pathogenic_statuses
        ]
        if limit is not None:
            return variants[:limit]
        return variants


class MockPhenotypeRepository(PhenotypeRepository):
    """Type-safe mock phenotype repository for testing."""

    def __init__(self, phenotypes: list[TestPhenotype] | None = None):
        """
        Initialize mock repository with test data.

        Args:
            phenotypes: List of test phenotypes to populate repository
        """
        self._phenotypes: dict[int, TestPhenotype] = {}
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

    def get_by_id(self, phenotype_id: int) -> Phenotype | None:
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

    def get_by_hpo_id(self, hpo_id: str) -> Phenotype | None:
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

    def list_all(self) -> list[Phenotype]:
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

    def update(self, phenotype_id: int, updates: PhenotypeUpdate) -> Phenotype:
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

    def __init__(self, evidence_list: list[TestEvidence] | None = None):
        """
        Initialize mock repository with test data.

        Args:
            evidence_list: List of test evidence to populate repository
        """
        self._evidence: dict[int, TestEvidence] = {}
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

    def get_by_id(self, evidence_id: int) -> Evidence | None:
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

    def list_all(self) -> list[Evidence]:
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

    def update(self, evidence_id: int, updates: EvidenceUpdate) -> Evidence:
        """Mock update method."""
        self.update_evidence(evidence_id, updates)
        if evidence_id in self._evidence:
            test_evidence = self._evidence[evidence_id]
            return Evidence(
                variant_id=updates.get("variant_id", test_evidence.variant_id),
                phenotype_id=updates.get("phenotype_id", test_evidence.phenotype_id),
                description=updates.get("description", test_evidence.description),
                evidence_level=updates.get(
                    "evidence_level",
                    test_evidence.evidence_level,
                ),
                evidence_type=updates.get("evidence_type", test_evidence.evidence_type),
                confidence_score=updates.get(
                    "confidence_score",
                    test_evidence.confidence_score,
                ),
                source=updates.get("source", test_evidence.source),
            )
        raise ValueError(f"Evidence {evidence_id} not found")

    def delete(self, evidence_id: int) -> None:
        """Mock delete method."""
        self.delete_evidence(evidence_id)
        if evidence_id in self._evidence:
            del self._evidence[evidence_id]

    def find_high_confidence_evidence(
        self,
        limit: int | None = None,
    ) -> list[Evidence]:
        """Return evidence entries with high confidence scores."""
        high_confidence = [
            evidence
            for evidence in self.list_all()
            if evidence.confidence_score is not None
            and evidence.confidence_score >= 0.9
        ]
        if limit is not None:
            return high_confidence[:limit]
        return high_confidence

    def find_relationship_evidence(
        self,
        variant_id: int,
        phenotype_id: int,
        min_confidence: float = 0.5,
    ) -> list[Evidence]:
        """Return evidence records linking the provided variant and phenotype."""
        return [
            evidence
            for evidence in self.list_all()
            if evidence.variant_id == variant_id
            and evidence.phenotype_id == phenotype_id
            and (
                evidence.confidence_score is None
                or evidence.confidence_score >= min_confidence
            )
        ]


class MockPublicationRepository(PublicationRepository):
    """Type-safe mock publication repository for testing."""

    def __init__(self, publications: list[TestPublication] | None = None):
        """
        Initialize mock repository with test data.

        Args:
            publications: List of test publications to populate repository
        """
        self._publications: dict[int, TestPublication] = {}
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

    def get_by_id(self, publication_id: int) -> Publication | None:
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

    def list_all(self) -> list[Publication]:
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

    def update(self, publication_id: int, updates: PublicationUpdate) -> Publication:
        """Mock update method."""
        self.update_publication(publication_id, updates)
        if publication_id in self._publications:
            test_publication = self._publications[publication_id]
            return Publication(
                title=updates.get("title", test_publication.title),
                authors=updates.get("authors", test_publication.authors),
                journal=updates.get("journal", test_publication.journal),
                publication_year=updates.get(
                    "publication_year",
                    test_publication.publication_year,
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

    def find_recent_publications(self, days: int = 30) -> list[Publication]:
        """Return recent publications (mocked as entire dataset)."""
        return self.list_all()

    def find_med13_relevant(
        self,
        min_relevance: int = 3,
        limit: int | None = None,
    ) -> list[Publication]:
        """Return MED13-relevant publications (mocked subset)."""
        publications = self.list_all()
        if limit is not None:
            publications = publications[:limit]
        return publications


# Factory functions for creating mock services
def create_mock_gene_service(
    genes: list[TestGene] | None = None,
) -> GeneApplicationService:
    """
    Create a mock gene domain service with typed repositories.

    Args:
        genes: Test genes to populate the repository

    Returns:
        Mock gene domain service
    """
    mock_gene_repo = MockGeneRepository(genes)
    mock_variant_repo = MockVariantRepository()
    domain_service = GeneDomainService()
    return GeneApplicationService(
        gene_repository=mock_gene_repo,
        gene_domain_service=domain_service,
        variant_repository=mock_variant_repo,
    )


def create_mock_variant_service(
    variants: list[TestVariant] | None = None,
) -> VariantApplicationService:
    """
    Create a mock variant domain service with typed repositories.

    Args:
        variants: Test variants to populate the repository

    Returns:
        Mock variant domain service
    """
    mock_variant_repo = MockVariantRepository(variants)
    mock_evidence_repo = MockEvidenceRepository()
    domain_service = VariantDomainService()
    return VariantApplicationService(
        variant_repository=mock_variant_repo,
        variant_domain_service=domain_service,
        evidence_repository=mock_evidence_repo,
    )


def create_mock_evidence_service(
    evidence_list: list[TestEvidence] | None = None,
) -> EvidenceApplicationService:
    """
    Create a mock evidence domain service with typed repositories.

    Args:
        evidence_list: Test evidence to populate the repository

    Returns:
        Mock evidence domain service
    """
    mock_repo = MockEvidenceRepository(evidence_list)
    domain_service = EvidenceDomainService()
    return EvidenceApplicationService(
        evidence_repository=mock_repo,
        evidence_domain_service=domain_service,
    )


# Data Discovery mock repositories and services
class MockDataDiscoverySessionRepository:
    """Mock data discovery session repository for testing."""

    def __init__(self):
        self.sessions = {}
        self.save = MagicMock()
        self.find_by_id = MagicMock()
        self.find_by_owner = MagicMock(return_value=[])
        self.find_by_space = MagicMock(return_value=[])
        self.delete = MagicMock(return_value=True)

    def setup_default_behavior(self):
        """Set up default mock behaviors."""
        self.save.side_effect = lambda session: session
        self.find_by_id.side_effect = lambda session_id: self.sessions.get(session_id)
        self.find_by_owner.return_value = list(self.sessions.values())
        self.find_by_space.return_value = list(self.sessions.values())


class MockSourceCatalogRepository:
    """Mock source catalog repository for testing."""

    def __init__(self):
        self.entries = {}
        self.save = MagicMock()
        self.find_by_id = MagicMock()
        self.find_all_active = MagicMock(return_value=[])
        self.find_by_category = MagicMock(return_value=[])
        self.search = MagicMock(return_value=[])
        self.update_usage_stats = MagicMock(return_value=True)

    def setup_default_behavior(self):
        """Set up default mock behaviors."""
        self.save.side_effect = lambda entry: entry
        self.find_by_id.side_effect = lambda entry_id: self.entries.get(entry_id)


class MockQueryTestResultRepository:
    """Mock query test result repository for testing."""

    def __init__(self):
        self.results = {}
        self.save = MagicMock()
        self.find_by_session = MagicMock(return_value=[])
        self.find_by_source = MagicMock(return_value=[])
        self.find_by_id = MagicMock()
        self.delete_session_results = MagicMock(return_value=0)

    def setup_default_behavior(self):
        """Set up default mock behaviors."""
        self.save.side_effect = lambda result: result
        self.find_by_id.side_effect = lambda result_id: self.results.get(result_id)


class MockSourceQueryClient:
    """Mock source query client for testing."""

    def __init__(self):
        self.execute_query = MagicMock()
        self.generate_url = MagicMock()
        self.validate_parameters = MagicMock(return_value=True)

    def setup_success_behavior(self, response_data: JSONObject | None = None):
        """Set up successful query behavior."""
        self.execute_query.return_value = response_data or {"result": "success"}
        self.generate_url.return_value = "https://example.com/test"
        self.validate_parameters.return_value = True

    def setup_failure_behavior(self, error_message: str = "Query failed"):
        """Set up failed query behavior."""
        from src.infrastructure.queries.source_query_client import QueryExecutionError

        self.execute_query.side_effect = QueryExecutionError(
            error_message,
            "test-source",
        )
        self.validate_parameters.return_value = False


class DataDiscoveryRepositoryMocks(TypedDict):
    """Typed mapping for mock data discovery repositories."""

    session_repo: MockDataDiscoverySessionRepository
    catalog_repo: MockSourceCatalogRepository
    query_repo: MockQueryTestResultRepository


def create_mock_data_discovery_repositories() -> DataDiscoveryRepositoryMocks:
    """
    Create a set of mock data discovery repositories for testing.

    Returns:
        Dictionary containing mock repositories
    """
    session_repo = MockDataDiscoverySessionRepository()
    catalog_repo = MockSourceCatalogRepository()
    query_repo = MockQueryTestResultRepository()

    # Don't set up default behaviors - let individual tests configure mocks as needed
    # This allows tests to have full control over mock behavior

    return {
        "session_repo": session_repo,
        "catalog_repo": catalog_repo,
        "query_repo": query_repo,
    }


def create_mock_query_client() -> MockSourceQueryClient:
    """
    Create a mock source query client for testing.

    Returns:
        Mock query client with success behavior
    """
    client = MockSourceQueryClient()
    client.setup_success_behavior()
    return client
