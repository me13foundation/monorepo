"""
Sample test data fixtures for MED13 Resource Library.

Provides realistic test data for genes, variants, phenotypes, and publications
that can be used across different test suites.
"""

from datetime import UTC, datetime


# Gene fixtures
GENE_MED13 = {
    "gene_id": "MED13",
    "symbol": "MED13",
    "name": "Mediator complex subunit 13",
    "description": "Component of the Mediator complex, a coactivator involved in regulated transcription of nearly all RNA polymerase II-dependent genes.",
    "gene_type": "protein_coding",
    "chromosome": "17",
    "start_position": 60000000,
    "end_position": 60010000,
    "ensembl_id": "ENSG00000108510",
    "ncbi_gene_id": 9968,
    "uniprot_id": "Q9UHV7",
    "created_at": datetime.now(UTC),
    "updated_at": datetime.now(UTC),
}

GENE_TP53 = {
    "gene_id": "TP53",
    "symbol": "TP53",
    "name": "Tumor protein p53",
    "description": "Tumor suppressor gene encoding p53 protein",
    "gene_type": "protein_coding",
    "chromosome": "17",
    "start_position": 7661779,
    "end_position": 7687550,
    "ensembl_id": "ENSG00000141510",
    "ncbi_gene_id": 7157,
    "uniprot_id": "P04637",
    "created_at": datetime.now(UTC),
    "updated_at": datetime.now(UTC),
}


# Variant fixtures
VARIANT_MED13_PATHOGENIC = {
    "variant_id": "VCV000001234",
    "clinvar_id": "RCV000001234",
    "variation_name": "c.1234A>G",
    "gene_references": ["MED13"],
    "clinical_significance": "Pathogenic",
    "chromosome": "17",
    "start_position": 60001234,
    "hgvs_notations": {"c": "c.1234A>G", "p": "p.Arg412Gly"},
    "allele_frequency": 0.001,
    "population_frequencies": {"AFR": 0.005, "EUR": 0.001, "ASN": 0.0005},
    "created_at": datetime.now(UTC),
    "updated_at": datetime.now(UTC),
}

VARIANT_TP53_BENIGN = {
    "variant_id": "VCV000005678",
    "clinvar_id": "RCV000005678",
    "variation_name": "c.215C>G",
    "gene_references": ["TP53"],
    "clinical_significance": "Benign",
    "chromosome": "17",
    "start_position": 7670700,
    "hgvs_notations": {"c": "c.215C>G", "p": "p.Pro72Arg"},
    "allele_frequency": 0.45,
    "population_frequencies": {"AFR": 0.35, "EUR": 0.50, "ASN": 0.40},
    "created_at": datetime.now(UTC),
    "updated_at": datetime.now(UTC),
}


# Phenotype fixtures
PHENOTYPE_INTELLECTUAL_DISABILITY = {
    "hpo_id": "HP:0001249",
    "hpo_term": "Intellectual disability",
    "definition": "Subnormal intellectual functioning which originates during the developmental period.",
    "category": "Clinical",
    "gene_references": ["MED13"],
    "frequency": 0.7,
    "created_at": datetime.now(UTC),
    "updated_at": datetime.now(UTC),
}

PHENOTYPE_AUTISM = {
    "hpo_id": "HP:0000729",
    "hpo_term": "Autism",
    "definition": "Persistent deficits in social communication and interaction.",
    "category": "Clinical",
    "gene_references": ["MED13"],
    "frequency": 0.3,
    "created_at": datetime.now(UTC),
    "updated_at": datetime.now(UTC),
}


# Publication fixtures
PUBLICATION_MED13_REVIEW = {
    "pubmed_id": "12345678",
    "pmcid": "PMC1234567",
    "doi": "10.1038/ng.1234",
    "title": "MED13 mutations in developmental disorders: genotype-phenotype correlations",
    "authors": [
        {"last_name": "Smith", "first_name": "John", "affiliation": "Test University"},
        {"last_name": "Doe", "first_name": "Jane", "affiliation": "Test Hospital"},
    ],
    "journal": "Nature Genetics",
    "publication_date": "2023-01-15",
    "abstract": "This study investigates MED13 mutations in developmental disorders...",
    "keywords": ["MED13", "developmental disorder", "genotype-phenotype"],
    "language": "eng",
    "country": "USA",
    "created_at": datetime.now(UTC),
    "updated_at": datetime.now(UTC),
}

PUBLICATION_TP53_CANCER = {
    "pubmed_id": "87654321",
    "pmcid": "PMC8765432",
    "doi": "10.1056/NEJMoa1916839",
    "title": "TP53 mutations in human cancer: a comprehensive review",
    "authors": [
        {
            "last_name": "Johnson",
            "first_name": "Robert",
            "affiliation": "Cancer Institute",
        }
    ],
    "journal": "New England Journal of Medicine",
    "publication_date": "2020-05-20",
    "abstract": "TP53 is the most frequently mutated gene in human cancer...",
    "keywords": ["TP53", "cancer", "tumor suppressor"],
    "language": "eng",
    "country": "USA",
    "created_at": datetime.now(UTC),
    "updated_at": datetime.now(UTC),
}


# Evidence fixtures
EVIDENCE_MED13_VARIANT = {
    "evidence_id": "EVID001",
    "evidence_type": "genetic_association",
    "source": "clinvar",
    "gene_references": ["MED13"],
    "variant_references": ["VCV000001234"],
    "phenotype_references": ["HP:0001249"],
    "publication_references": ["12345678"],
    "confidence_score": 0.9,
    "evidence_level": "strong",
    "description": "Pathogenic MED13 variant associated with intellectual disability",
    "created_at": datetime.now(UTC),
    "updated_at": datetime.now(UTC),
}


# Collection fixtures for convenience
ALL_GENES = [GENE_MED13, GENE_TP53]
ALL_VARIANTS = [VARIANT_MED13_PATHOGENIC, VARIANT_TP53_BENIGN]
ALL_PHENOTYPES = [PHENOTYPE_INTELLECTUAL_DISABILITY, PHENOTYPE_AUTISM]
ALL_PUBLICATIONS = [PUBLICATION_MED13_REVIEW, PUBLICATION_TP53_CANCER]
ALL_EVIDENCE = [EVIDENCE_MED13_VARIANT]


# Test dataset collections
MED13_DATASET = {
    "genes": [GENE_MED13],
    "variants": [VARIANT_MED13_PATHOGENIC],
    "phenotypes": [PHENOTYPE_INTELLECTUAL_DISABILITY, PHENOTYPE_AUTISM],
    "publications": [PUBLICATION_MED13_REVIEW],
    "evidence": [EVIDENCE_MED13_VARIANT],
}

TP53_DATASET = {
    "genes": [GENE_TP53],
    "variants": [VARIANT_TP53_BENIGN],
    "phenotypes": [],
    "publications": [PUBLICATION_TP53_CANCER],
    "evidence": [],
}


__all__ = [
    # Individual fixtures
    "GENE_MED13",
    "GENE_TP53",
    "VARIANT_MED13_PATHOGENIC",
    "VARIANT_TP53_BENIGN",
    "PHENOTYPE_INTELLECTUAL_DISABILITY",
    "PHENOTYPE_AUTISM",
    "PUBLICATION_MED13_REVIEW",
    "PUBLICATION_TP53_CANCER",
    "EVIDENCE_MED13_VARIANT",
    # Collections
    "ALL_GENES",
    "ALL_VARIANTS",
    "ALL_PHENOTYPES",
    "ALL_PUBLICATIONS",
    "ALL_EVIDENCE",
    # Dataset collections
    "MED13_DATASET",
    "TP53_DATASET",
]
