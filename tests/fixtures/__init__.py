"""
Test fixtures package for MED13 Resource Library.

This package contains reusable test data and fixtures for
unit, integration, and end-to-end testing.
"""

from .sample_data import (
    # Individual fixtures
    GENE_MED13,
    GENE_TP53,
    VARIANT_MED13_PATHOGENIC,
    VARIANT_TP53_BENIGN,
    PHENOTYPE_INTELLECTUAL_DISABILITY,
    PHENOTYPE_AUTISM,
    PUBLICATION_MED13_REVIEW,
    PUBLICATION_TP53_CANCER,
    EVIDENCE_MED13_VARIANT,
    # Collections
    ALL_GENES,
    ALL_VARIANTS,
    ALL_PHENOTYPES,
    ALL_PUBLICATIONS,
    ALL_EVIDENCE,
    # Dataset collections
    MED13_DATASET,
    TP53_DATASET,
)

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
