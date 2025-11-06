"""
Typed test fixtures for MED13 Resource Library.

Provides type-safe test data using NamedTuple and TypedDict structures
for reliable, self-documenting test data.
"""

from datetime import UTC, datetime
from typing import NamedTuple


# Test data types using NamedTuple for immutable, typed test data
class TestGene(NamedTuple):
    """Typed test gene data."""

    gene_id: str
    symbol: str
    name: str | None
    description: str | None
    gene_type: str
    chromosome: str | None
    start_position: int | None
    end_position: int | None
    ensembl_id: str | None
    ncbi_gene_id: int | None
    uniprot_id: str | None
    created_at: datetime
    updated_at: datetime


class TestVariant(NamedTuple):
    """Typed test variant data."""

    variant_id: str
    clinvar_id: str | None
    chromosome: str
    position: int
    reference_allele: str
    alternate_allele: str
    variant_type: str
    clinical_significance: str
    gene_identifier: str | None
    gene_database_id: int | None
    hgvs_genomic: str | None
    hgvs_protein: str | None
    hgvs_cdna: str | None
    condition: str | None
    review_status: str | None
    allele_frequency: float | None
    gnomad_af: float | None
    created_at: datetime
    updated_at: datetime


class TestPhenotype(NamedTuple):
    """Typed test phenotype data."""

    hpo_id: str
    name: str
    definition: str | None
    synonyms: list[str]
    created_at: datetime
    updated_at: datetime


class TestEvidence(NamedTuple):
    """Typed test evidence data."""

    variant_id: int
    phenotype_id: int
    description: str
    evidence_level: str
    evidence_type: str
    confidence_score: float
    source: str | None
    created_at: datetime
    updated_at: datetime


class TestPublication(NamedTuple):
    """Typed test publication data."""

    title: str
    authors: list[str]
    journal: str | None
    publication_year: int
    doi: str | None
    pmid: str | None
    abstract: str | None
    created_at: datetime
    updated_at: datetime


# Factory functions for creating test data with defaults
def create_test_gene(
    gene_id: str = "MED13",
    symbol: str = "MED13",
    name: str | None = "Mediator complex subunit 13",
    description: str | None = None,
    gene_type: str = "protein_coding",
    chromosome: str | None = "17",
    start_position: int | None = 60000000,
    end_position: int | None = 60010000,
    ensembl_id: str | None = "ENSG00000108510",
    ncbi_gene_id: int | None = 9968,
    uniprot_id: str | None = "Q9UHV7",
) -> TestGene:
    """
    Create a typed test gene with sensible defaults.

    Args:
        gene_id: Gene identifier
        symbol: Gene symbol
        name: Full gene name
        description: Gene description
        gene_type: Type of gene
        chromosome: Chromosome location
        start_position: Start position on chromosome
        end_position: End position on chromosome
        ensembl_id: Ensembl gene ID
        ncbi_gene_id: NCBI Gene ID
        uniprot_id: UniProt accession

    Returns:
        Typed test gene data
    """
    now = datetime.now(UTC)
    return TestGene(
        gene_id=gene_id,
        symbol=symbol,
        name=name,
        description=description,
        gene_type=gene_type,
        chromosome=chromosome,
        start_position=start_position,
        end_position=end_position,
        ensembl_id=ensembl_id,
        ncbi_gene_id=ncbi_gene_id,
        uniprot_id=uniprot_id,
        created_at=now,
        updated_at=now,
    )


def create_test_variant(
    variant_id: str = "VCV000001234",
    clinvar_id: str | None = "RCV000001234",
    chromosome: str = "17",
    position: int = 60005000,
    reference_allele: str = "A",
    alternate_allele: str = "G",
    variant_type: str = "snv",
    clinical_significance: str = "pathogenic",
    gene_identifier: str | None = "MED13",
    gene_database_id: int | None = 1,
    hgvs_genomic: str | None = "chr17:g.60005000A>G",
    hgvs_protein: str | None = "p.Val123Gly",
    hgvs_cdna: str | None = "c.367A>G",
    condition: str | None = "Intellectual disability",
    review_status: str | None = "criteria_provided",
    allele_frequency: float | None = 0.0001,
    gnomad_af: float | None = 0.0002,
) -> TestVariant:
    """
    Create a typed test variant with sensible defaults.

    Args:
        variant_id: Variant identifier
        clinvar_id: ClinVar accession
        chromosome: Chromosome
        position: Genomic position
        reference_allele: Reference allele
        alternate_allele: Alternate allele
        variant_type: Type of variant
        clinical_significance: Clinical significance
        gene_identifier: Associated gene
        gene_database_id: Gene database ID
        hgvs_genomic: HGVS genomic notation
        hgvs_protein: HGVS protein notation
        hgvs_cdna: HGVS cDNA notation
        condition: Associated condition
        review_status: Review status
        allele_frequency: Allele frequency
        gnomad_af: gnomAD allele frequency

    Returns:
        Typed test variant data
    """
    now = datetime.now(UTC)
    return TestVariant(
        variant_id=variant_id,
        clinvar_id=clinvar_id,
        chromosome=chromosome,
        position=position,
        reference_allele=reference_allele,
        alternate_allele=alternate_allele,
        variant_type=variant_type,
        clinical_significance=clinical_significance,
        gene_identifier=gene_identifier,
        gene_database_id=gene_database_id,
        hgvs_genomic=hgvs_genomic,
        hgvs_protein=hgvs_protein,
        hgvs_cdna=hgvs_cdna,
        condition=condition,
        review_status=review_status,
        allele_frequency=allele_frequency,
        gnomad_af=gnomad_af,
        created_at=now,
        updated_at=now,
    )


def create_test_phenotype(
    hpo_id: str = "HP:0001249",
    name: str = "Intellectual disability",
    definition: str | None = "Subnormal intellectual functioning",
    synonyms: list[str] | None = None,
) -> TestPhenotype:
    """
    Create a typed test phenotype with sensible defaults.

    Args:
        hpo_id: HPO identifier
        name: Phenotype name
        definition: Phenotype definition
        synonyms: Alternative names

    Returns:
        Typed test phenotype data
    """
    if synonyms is None:
        synonyms = ["Mental retardation", "Intellectual impairment"]

    now = datetime.now(UTC)
    return TestPhenotype(
        hpo_id=hpo_id,
        name=name,
        definition=definition,
        synonyms=synonyms,
        created_at=now,
        updated_at=now,
    )


def create_test_evidence(
    variant_id: int = 1,
    phenotype_id: int = 1,
    description: str = "Pathogenic variant identified in patient with intellectual disability",
    evidence_level: str = "definitive",
    evidence_type: str = "clinical_report",
    confidence_score: float = 0.95,
    source: str | None = "ClinVar",
) -> TestEvidence:
    """
    Create a typed test evidence with sensible defaults.

    Args:
        variant_id: Associated variant ID
        phenotype_id: Associated phenotype ID
        description: Evidence description
        evidence_level: Level of evidence
        evidence_type: Type of evidence
        confidence_score: Confidence score (0.0-1.0)
        source: Evidence source

    Returns:
        Typed test evidence data
    """
    now = datetime.now(UTC)
    return TestEvidence(
        variant_id=variant_id,
        phenotype_id=phenotype_id,
        description=description,
        evidence_level=evidence_level,
        evidence_type=evidence_type,
        confidence_score=confidence_score,
        source=source,
        created_at=now,
        updated_at=now,
    )


def create_test_publication(
    title: str = "Novel MED13 pathogenic variant causes intellectual disability",
    authors: list[str] | None = None,
    journal: str | None = "American Journal of Human Genetics",
    publication_year: int = 2023,
    doi: str | None = "10.1016/j.ajhg.2023.01.001",
    pmid: str | None = "36736399",
    abstract: str | None = None,
) -> TestPublication:
    """
    Create a typed test publication with sensible defaults.

    Args:
        title: Publication title
        authors: List of authors
        journal: Journal name
        publication_year: Year of publication
        doi: DOI identifier
        pmid: PubMed ID
        abstract: Publication abstract

    Returns:
        Typed test publication data
    """
    if authors is None:
        authors = ["Smith J", "Johnson A", "Williams B"]

    if abstract is None:
        abstract = "We report a novel pathogenic variant in MED13 associated with intellectual disability..."

    now = datetime.now(UTC)
    return TestPublication(
        title=title,
        authors=authors,
        journal=journal,
        publication_year=publication_year,
        doi=doi,
        pmid=pmid,
        abstract=abstract,
        created_at=now,
        updated_at=now,
    )


# Pre-defined test data instances
TEST_GENE_MED13 = create_test_gene()
TEST_GENE_TP53 = create_test_gene(
    gene_id="TP53",
    symbol="TP53",
    name="Tumor protein p53",
    description="Tumor suppressor gene encoding p53 protein",
    chromosome="17",
    start_position=7661779,
    end_position=7687550,
    ensembl_id="ENSG00000141510",
    ncbi_gene_id=7157,
    uniprot_id="P04637",
)

TEST_VARIANT_PATHOGENIC = create_test_variant()
TEST_VARIANT_BENIGN = create_test_variant(
    variant_id="VCV000005678",
    clinvar_id="RCV000005678",
    position=60006000,
    clinical_significance="benign",
    condition=None,
    allele_frequency=0.01,
    gnomad_af=0.015,
)

TEST_PHENOTYPE_ID = create_test_phenotype()
TEST_PHENOTYPE_AUTISM = create_test_phenotype(
    hpo_id="HP:0000717",
    name="Autism",
    definition="Persistent deficits in social communication and interaction",
    synonyms=["Autistic disorder", "ASD"],
)

TEST_EVIDENCE_PATHOGENIC = create_test_evidence()
TEST_EVIDENCE_SUPPORTING = create_test_evidence(
    evidence_level="supporting",
    confidence_score=0.7,
    source="Literature review",
)

TEST_PUBLICATION_MED13 = create_test_publication()
TEST_PUBLICATION_REVIEW = create_test_publication(
    title="MED13 and intellectual disability: a comprehensive review",
    authors=["Brown C", "Davis M", "Garcia R", "Miller T"],
    journal="Human Molecular Genetics",
    publication_year=2022,
    doi="10.1093/hmg/ddac123",
    pmid="35640231",
)
