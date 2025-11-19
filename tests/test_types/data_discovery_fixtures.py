"""
Type-safe test fixtures for Data Discovery entities.

Following the patterns established in type_examples.md for creating
test fixtures with proper typing and mock data.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.domain.entities.data_discovery_parameters import (
    AdvancedQueryParameters,
    QueryParameterCapabilities,
    TestResultStatus,
)
from src.domain.entities.data_discovery_session import (
    DataDiscoverySession,
    QueryTestResult,
    SourceCatalogEntry,
)
from src.domain.entities.user_data_source import SourceType


def create_test_source_catalog_entry(
    entry_id: str = "test-source",
    name: str = "Test Source",
    category: str = "Genomic Variant Databases",
    param_type: str = "gene",
    **overrides: object,
) -> SourceCatalogEntry:
    """
    Create a test SourceCatalogEntry with sensible defaults.

    Args:
        entry_id: Unique identifier for the entry
        name: Display name
        category: Category classification
        param_type: Parameter type (gene, term, etc.)
        **overrides: Additional field overrides

    Returns:
        A properly typed SourceCatalogEntry instance
    """
    defaults = {
        "id": entry_id,
        "name": name,
        "category": category,
        "subcategory": None,
        "description": f"Test description for {name}",
        "param_type": param_type,
        "source_type": SourceType.API,
        "url_template": (
            f"https://example.com/{entry_id}/{{gene}}" if param_type == "gene" else None
        ),
        "data_format": "json",
        "api_endpoint": (
            f"https://api.example.com/{entry_id}" if param_type == "api" else None
        ),
        "is_active": True,
        "requires_auth": False,
        "usage_count": 10,
        "success_rate": 0.85,
        "source_template_id": uuid4(),
        "tags": ["test", "mock"],
        "capabilities": QueryParameterCapabilities(),
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }

    # Apply overrides
    defaults.update(overrides)

    return SourceCatalogEntry(**defaults)


def create_test_data_discovery_session(
    session_id: str | None = None,
    owner_id: str | None = None,
    research_space_id: str | None = None,
    name: str = "Test Session",
    **overrides: object,
) -> DataDiscoverySession:
    """
    Create a test DataDiscoverySession with sensible defaults.

    Args:
        session_id: Session ID (generated if not provided)
        owner_id: Owner ID (generated if not provided)
        research_space_id: Research space ID
        name: Session name
        **overrides: Additional field overrides

    Returns:
        A properly typed DataDiscoverySession instance
    """
    defaults = {
        "id": session_id or uuid4(),
        "owner_id": owner_id or uuid4(),
        "research_space_id": research_space_id,
        "name": name,
        "current_parameters": AdvancedQueryParameters(
            gene_symbol="MED13L",
            search_term="atrial septal defect",
        ),
        "selected_sources": [],
        "tested_sources": [],
        "total_tests_run": 0,
        "successful_tests": 0,
        "is_active": True,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "last_activity_at": datetime.now(UTC),
    }

    # Apply overrides
    defaults.update(overrides)

    return DataDiscoverySession(**defaults)


def create_test_query_test_result(
    result_id: str | None = None,
    session_id: str | None = None,
    catalog_entry_id: str = "test-source",
    status: TestResultStatus = TestResultStatus.SUCCESS,
    **overrides: object,
) -> QueryTestResult:
    """
    Create a test QueryTestResult with sensible defaults.

    Args:
        result_id: Result ID (generated if not provided)
        session_id: Session ID (generated if not provided)
        catalog_entry_id: Catalog entry ID
        status: Test status
        **overrides: Additional field overrides

    Returns:
        A properly typed QueryTestResult instance
    """
    defaults = {
        "id": result_id or uuid4(),
        "session_id": session_id or uuid4(),
        "catalog_entry_id": catalog_entry_id,
        "parameters": AdvancedQueryParameters(
            gene_symbol="MED13L",
            search_term="atrial septal defect",
        ),
        "status": status,
        "response_data": {"test": True} if status == TestResultStatus.SUCCESS else None,
        "response_url": (
            "https://example.com/result" if status == TestResultStatus.SUCCESS else None
        ),
        "error_message": "Test error" if status == TestResultStatus.ERROR else None,
        "execution_time_ms": 1500,
        "data_quality_score": 0.8 if status == TestResultStatus.SUCCESS else None,
        "started_at": datetime.now(UTC),
        "completed_at": (
            datetime.now(UTC) + timedelta(milliseconds=1500)
            if status != TestResultStatus.PENDING
            else None
        ),
    }

    # Apply overrides
    defaults.update(overrides)

    return QueryTestResult(**defaults)


# Pre-defined test instances for common use cases
TEST_SOURCE_CLINVAR = create_test_source_catalog_entry(
    entry_id="clinvar",
    name="ClinVar",
    category="Genomic Variant Databases",
    param_type="gene",
    description="Public archive of human variations and phenotypes",
    usage_count=1250,
    success_rate=0.94,
    tags=["variants", "clinical", "pathogenic"],
)

TEST_SOURCE_HPO = create_test_source_catalog_entry(
    entry_id="hpo",
    name="Human Phenotype Ontology",
    category="Phenotype Ontologies & Databases",
    param_type="term",
    description="Standardized vocabulary for human phenotypic abnormalities",
    usage_count=1450,
    success_rate=0.96,
    tags=["phenotype", "ontology", "standardized"],
)

TEST_SOURCE_VARIANTFORMER = create_test_source_catalog_entry(
    entry_id="variantformer",
    name="VariantFormer",
    category="AI Predictive Models",
    param_type="api",
    description="AI model for predicting variant pathogenicity",
    usage_count=320,
    success_rate=0.87,
    tags=["ai", "prediction", "pathogenicity"],
)

TEST_SESSION_ACTIVE = create_test_data_discovery_session(
    name="Active Research Session",
    selected_sources=["clinvar", "hpo"],
    tested_sources=["clinvar"],
    total_tests_run=1,
    successful_tests=1,
)

TEST_SESSION_EMPTY = create_test_data_discovery_session(
    name="Empty Session",
)

TEST_RESULT_SUCCESS = create_test_query_test_result(
    status=TestResultStatus.SUCCESS,
    execution_time_ms=1200,
    data_quality_score=0.9,
)

TEST_RESULT_ERROR = create_test_query_test_result(
    status=TestResultStatus.ERROR,
    error_message="API timeout",
    execution_time_ms=30000,
)
