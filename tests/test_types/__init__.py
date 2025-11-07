"""
Typed test fixtures and mocks for MED13 Resource Library.

Provides type-safe test data and factory functions for comprehensive testing.
"""

from .fixtures import (
    TEST_MEMBERSHIP_ADMIN,
    TEST_MEMBERSHIP_OWNER,
    TEST_MEMBERSHIP_PENDING,
    TEST_RESEARCH_SPACE_MED12,
    TEST_RESEARCH_SPACE_MED13,
    TestEvidence,
    TestGene,
    TestPhenotype,
    TestPublication,
    TestResearchSpace,
    TestResearchSpaceMembership,
    TestVariant,
    create_test_evidence,
    create_test_gene,
    create_test_phenotype,
    create_test_publication,
    create_test_research_space,
    create_test_research_space_membership,
    create_test_variant,
)
from .mocks import (
    MockEvidenceRepository,
    MockGeneRepository,
    MockPhenotypeRepository,
    MockPublicationRepository,
    MockVariantRepository,
    create_mock_evidence_service,
    create_mock_gene_service,
    create_mock_variant_service,
)

__all__ = [
    "MockEvidenceRepository",
    "MockGeneRepository",
    "MockPhenotypeRepository",
    "MockPublicationRepository",
    "MockVariantRepository",
    "TEST_MEMBERSHIP_ADMIN",
    "TEST_MEMBERSHIP_OWNER",
    "TEST_MEMBERSHIP_PENDING",
    "TEST_RESEARCH_SPACE_MED12",
    "TEST_RESEARCH_SPACE_MED13",
    "TestEvidence",
    "TestGene",
    "TestPhenotype",
    "TestPublication",
    "TestResearchSpace",
    "TestResearchSpaceMembership",
    "TestVariant",
    "create_mock_evidence_service",
    "create_mock_gene_service",
    "create_mock_variant_service",
    "create_test_evidence",
    "create_test_gene",
    "create_test_phenotype",
    "create_test_publication",
    "create_test_research_space",
    "create_test_research_space_membership",
    "create_test_variant",
]
