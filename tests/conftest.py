"""
Test configuration and shared fixtures for MED13 Resource Library tests.

Provides pytest fixtures, test database setup, and common test utilities
across unit, integration, and end-to-end tests.
"""

import os
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.models.database.base import Base

# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test_med13.db"


# Configure pytest-asyncio to use auto mode
# With asyncio_mode = auto in pytest.ini, pytest-asyncio automatically
# manages event loops, so we don't need an explicit event_loop fixture


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    # Use in-memory SQLite for fast tests
    test_engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Provide a database session for tests."""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    original_env = os.environ.copy()

    # Set test-specific environment variables
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["TESTING"] = "true"

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_gene_data():
    """Provide sample gene data for testing."""
    return {
        "gene_id": "MED13_TEST",
        "symbol": "MED13",
        "name": "Mediator complex subunit 13",
        "description": "Test gene for MED13",
        "gene_type": "protein_coding",
        "chromosome": "17",
        "start_position": 60000000,
        "end_position": 60010000,
        "ensembl_id": "ENSG00000108510",
        "ncbi_gene_id": 9968,
        "uniprot_id": "Q9UHV7",
    }


@pytest.fixture
def sample_variant_data():
    """Provide sample variant data for testing."""
    return {
        "variant_id": "VCV000000001",
        "clinvar_id": "RCV000000001",
        "variation_name": "c.123A>G",
        "gene_references": ["MED13"],
        "clinical_significance": "Pathogenic",
        "chromosome": "17",
        "start_position": 60001234,
        "hgvs_notations": {"c": "c.123A>G", "p": "p.Arg41Gly"},
    }


@pytest.fixture
def sample_phenotype_data():
    """Provide sample phenotype data for testing."""
    return {
        "hpo_id": "HP:0001249",
        "hpo_term": "Intellectual disability",
        "definition": "Subnormal intellectual functioning",
        "category": "Clinical",
        "gene_references": ["MED13"],
    }


@pytest.fixture
def sample_provenance():
    """Provide sample provenance data for testing."""
    from datetime import UTC, datetime

    from src.models.value_objects.provenance import DataSource, Provenance

    return Provenance(
        source=DataSource.CLINVAR,
        acquired_at=datetime.now(UTC),
        acquired_by="test_system",
        processing_steps=["normalized", "validated"],
        validation_status="valid",
        quality_score=0.95,
    )


@pytest.fixture
def mock_api_response():
    """Provide a mock API response fixture."""

    class MockResponse:
        def __init__(self, status_code=200, json_data=None, text=""):
            self.status_code = status_code
            self.json_data = json_data or {}
            self.text = text

        def json(self):
            return self.json_data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")

    return MockResponse


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")


# Test data fixtures
@pytest.fixture
def test_data_factory():
    """Factory for creating test data of various types."""

    def create_data(data_type: str, **kwargs):
        factories = {
            "gene": lambda: {
                "gene_id": kwargs.get("gene_id", "TEST001"),
                "symbol": kwargs.get("symbol", "TEST"),
                "name": kwargs.get("name", "Test Gene"),
                "gene_type": kwargs.get("gene_type", "protein_coding"),
                **kwargs,
            },
            "variant": lambda: {
                "variant_id": kwargs.get("variant_id", "VCV000TEST"),
                "clinvar_id": kwargs.get("clinvar_id", "RCV000TEST"),
                "variation_name": kwargs.get("variation_name", "c.123A>G"),
                "gene_references": kwargs.get("gene_references", ["TEST"]),
                **kwargs,
            },
            "phenotype": lambda: {
                "hpo_id": kwargs.get("hpo_id", "HP:000TEST"),
                "hpo_term": kwargs.get("hpo_term", "Test phenotype"),
                "gene_references": kwargs.get("gene_references", ["TEST"]),
                **kwargs,
            },
        }

        factory = factories.get(data_type)
        if not factory:
            raise ValueError(f"Unknown data type: {data_type}")

        return factory()

    return create_data


# Database cleanup utilities
@pytest.fixture(autouse=True)
def clean_database(db_session):
    """Automatically clean database between tests."""
    # This runs before each test
    yield
    # This runs after each test
    db_session.rollback()


# Custom test markers
@pytest.fixture
def skip_if_no_database():
    """Skip test if database is not available."""
    try:
        from src.database.session import engine

        engine.execute("SELECT 1")
    except Exception:
        pytest.skip("Database not available")


@pytest.fixture
def skip_if_no_external_api():
    """Skip test if external APIs are not available."""
    if os.getenv("SKIP_EXTERNAL_TESTS"):
        pytest.skip("External API tests disabled")
