"""
Unit tests for gene repository functionality.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.database import Base, GeneModel
from src.repositories import GeneRepository
from src.repositories.base import NotFoundError

EXPECTED_TOTAL_GENES = 2


@pytest.fixture
def test_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    session_local = sessionmaker(bind=engine)
    session = session_local()

    try:
        yield session
    finally:
        session.close()


class TestGeneRepository:
    """Test gene-specific repository functionality."""

    def test_find_by_symbol(self, test_session):
        """Test finding gene by symbol."""
        repo = GeneRepository(test_session)

        # Create genes
        gene1 = GeneModel(gene_id="GENE001", symbol="TEST1", name="Test Gene 1")
        gene2 = GeneModel(
            gene_id="GENE002",
            symbol="test2",
            name="Test Gene 2",  # lowercase
        )

        repo.create(gene1)
        repo.create(gene2)

        # Find by symbol (case insensitive)
        found_gene = repo.find_by_symbol("TEST1")
        assert found_gene is not None
        assert found_gene.symbol == "TEST1"

        found_gene_lower = repo.find_by_symbol("test2")
        assert found_gene_lower is not None
        assert found_gene_lower.symbol == "test2"

        # Non-existent symbol
        not_found = repo.find_by_symbol("NONEXISTENT")
        assert not_found is None

    def test_find_by_gene_id(self, test_session):
        """Test finding gene by gene_id."""
        repo = GeneRepository(test_session)

        # Create genes
        gene1 = GeneModel(gene_id="GENE001", symbol="TEST1")
        gene2 = GeneModel(gene_id="GENE002", symbol="TEST2")

        repo.create(gene1)
        repo.create(gene2)

        # Find by gene_id
        found_gene = repo.find_by_gene_id("GENE001")
        assert found_gene is not None
        assert found_gene.gene_id == "GENE001"

        # Non-existent gene_id
        not_found = repo.find_by_gene_id("NONEXISTENT")
        assert not_found is None

    def test_find_by_external_id_ensembl(self, test_session):
        """Test finding gene by Ensembl ID."""
        repo = GeneRepository(test_session)

        # Create genes
        gene1 = GeneModel(gene_id="GENE001", symbol="TEST1", ensembl_id="ENSG000001")
        gene2 = GeneModel(gene_id="GENE002", symbol="TEST2", ensembl_id="ENSG000002")

        repo.create(gene1)
        repo.create(gene2)

        # Find by Ensembl ID
        found_gene = repo.find_by_external_id("ENSG000001")
        assert found_gene is not None
        assert found_gene.ensembl_id == "ENSG000001"

        # Non-existent Ensembl ID
        not_found = repo.find_by_external_id("ENSG999999")
        assert not_found is None

    def test_find_by_external_id_ncbi(self, test_session):
        """Test finding gene by NCBI Gene ID."""
        repo = GeneRepository(test_session)

        # Create genes
        gene1 = GeneModel(gene_id="GENE001", symbol="TEST1", ncbi_gene_id=12345)
        gene2 = GeneModel(gene_id="GENE002", symbol="TEST2", ncbi_gene_id=67890)

        repo.create(gene1)
        repo.create(gene2)

        # Find by NCBI Gene ID
        found_gene = repo.find_by_external_id("12345")
        assert found_gene is not None
        assert found_gene.ncbi_gene_id == 12345

        # Non-existent NCBI ID
        not_found = repo.find_by_external_id("99999")
        assert not_found is None

    def test_search_by_name_or_symbol(self, test_session):
        """Test searching genes by name or symbol."""
        repo = GeneRepository(test_session)

        # Create genes
        genes = [
            GeneModel(gene_id="GENE001", symbol="TEST1", name="Test Gene One"),
            GeneModel(gene_id="GENE002", symbol="OTHER", name="Another Gene"),
            GeneModel(gene_id="GENE003", symbol="TESTING", name="Testing Gene"),
        ]

        for gene in genes:
            repo.create(gene)

        # Search for "test" - should match TEST1 and TESTING symbols,
        # and "Test Gene One"
        results = repo.search_by_name_or_symbol("test", limit=10)
        assert len(results) == 2  # TEST1 symbol and "Test Gene One" name

        # Search for "Gene" - should match names
        results = repo.search_by_name_or_symbol("Gene", limit=10)
        assert len(results) == 3

        # Search for non-existent term
        results = repo.search_by_name_or_symbol("nonexistent", limit=10)
        assert len(results) == 0

    def test_get_gene_statistics(self, test_session):
        """Test getting gene statistics."""
        repo = GeneRepository(test_session)

        # Initially empty
        stats = repo.get_gene_statistics()
        assert stats["total_genes"] == 0

        # Add some genes
        genes = [
            GeneModel(
                gene_id="GENE001",
                symbol="TEST1",
                chromosome="1",
                start_position=1000,
                end_position=2000,
            ),
            GeneModel(
                gene_id="GENE002",
                symbol="TEST2",
                # No location data
            ),
        ]

        for gene in genes:
            repo.create(gene)

        # Check updated stats
        stats = repo.get_gene_statistics()
        assert stats["total_genes"] == EXPECTED_TOTAL_GENES
        # Note: Additional stats would need variant relationships to be meaningful

    def test_find_by_symbol_or_fail_success(self, test_session):
        """Test successful find_by_symbol_or_fail."""
        repo = GeneRepository(test_session)

        # Create a gene
        gene = GeneModel(gene_id="GENE001", symbol="TEST")
        repo.create(gene)

        # Find successfully
        found_gene = repo.find_by_symbol_or_fail("TEST")
        assert found_gene.symbol == "TEST"

    def test_find_by_symbol_or_fail_not_found(self, test_session):
        """Test find_by_symbol_or_fail with non-existent symbol."""
        repo = GeneRepository(test_session)

        with pytest.raises(NotFoundError):
            repo.find_by_symbol_or_fail("NONEXISTENT")
