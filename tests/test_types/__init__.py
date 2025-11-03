"""
Typed test fixtures and mocks for MED13 Resource Library.

Provides type-safe test data and factory functions for comprehensive testing.
"""

from .fixtures import (
    TestGene,
    TestVariant,
    TestPhenotype,
    TestEvidence,
    TestPublication,
    create_test_gene,
    create_test_variant,
    create_test_phenotype,
    create_test_evidence,
    create_test_publication,
)

from .mocks import (
    MockGeneRepository,
    MockVariantRepository,
    MockPhenotypeRepository,
    MockEvidenceRepository,
    MockPublicationRepository,
    create_mock_gene_service,
    create_mock_variant_service,
    create_mock_evidence_service,
)

__all__ = [
    "TestGene",
    "TestVariant",
    "TestPhenotype",
    "TestEvidence",
    "TestPublication",
    "create_test_gene",
    "create_test_variant",
    "create_test_phenotype",
    "create_test_evidence",
    "create_test_publication",
    "MockGeneRepository",
    "MockVariantRepository",
    "MockPhenotypeRepository",
    "MockEvidenceRepository",
    "MockPublicationRepository",
    "create_mock_gene_service",
    "create_mock_variant_service",
    "create_mock_evidence_service",
]
