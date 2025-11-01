"""
Unit tests for base repository functionality.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.database import Base, GeneModel, GeneType
from src.repositories import GeneRepository
from src.repositories.base import NotFoundError, DuplicateError


@pytest.fixture
def test_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


class TestBaseRepository:
    """Test base repository functionality using GeneRepository."""

    def test_create_and_retrieve(self, test_session):
        """Test creating and retrieving an entity."""
        repo = GeneRepository(test_session)

        # Create a gene
        gene = GeneModel(
            gene_id="TEST001",
            symbol="TEST",
            name="Test Gene",
            gene_type=GeneType.PROTEIN_CODING,
        )
        created_gene = repo.create(gene)

        assert created_gene.id is not None
        assert created_gene.gene_id == "TEST001"
        assert created_gene.symbol == "TEST"

        # Retrieve by ID
        retrieved_gene = repo.get_by_id(created_gene.id)
        assert retrieved_gene is not None
        assert retrieved_gene.id == created_gene.id
        assert retrieved_gene.gene_id == "TEST001"

    def test_get_by_id_not_found(self, test_session):
        """Test retrieving non-existent entity."""
        repo = GeneRepository(test_session)

        result = repo.get_by_id(999)
        assert result is None

    def test_get_by_id_or_fail_success(self, test_session):
        """Test successful get_by_id_or_fail."""
        repo = GeneRepository(test_session)

        # Create a gene
        gene = GeneModel(gene_id="TEST001", symbol="TEST")
        created_gene = repo.create(gene)

        # Retrieve successfully
        retrieved_gene = repo.get_by_id_or_fail(created_gene.id)
        assert retrieved_gene.id == created_gene.id

    def test_get_by_id_or_fail_not_found(self, test_session):
        """Test get_by_id_or_fail with non-existent entity."""
        repo = GeneRepository(test_session)

        with pytest.raises(NotFoundError):
            repo.get_by_id_or_fail(999)

    def test_find_all(self, test_session):
        """Test finding all entities."""
        repo = GeneRepository(test_session)

        # Create multiple genes
        genes = [GeneModel(gene_id=f"TEST00{i}", symbol=f"T{i}") for i in range(1, 4)]
        for gene in genes:
            repo.create(gene)

        # Find all
        all_genes = repo.find_all()
        assert len(all_genes) == 3

    def test_find_all_with_limit(self, test_session):
        """Test finding all entities with limit."""
        repo = GeneRepository(test_session)

        # Create multiple genes
        genes = [GeneModel(gene_id=f"TEST00{i}", symbol=f"T{i}") for i in range(1, 6)]
        for gene in genes:
            repo.create(gene)

        # Find with limit
        limited_genes = repo.find_all(limit=2)
        assert len(limited_genes) == 2

    def test_find_by_criteria(self, test_session):
        """Test finding entities by criteria."""
        repo = GeneRepository(test_session)

        # Create genes with different types
        coding_gene = GeneModel(
            gene_id="TEST001", symbol="CODING", gene_type=GeneType.PROTEIN_CODING
        )
        rn_gene = GeneModel(gene_id="TEST002", symbol="RNA", gene_type=GeneType.NCRNA)

        repo.create(coding_gene)
        repo.create(rn_gene)

        # Find by gene type
        coding_genes = repo.find_by_criteria({"gene_type": GeneType.PROTEIN_CODING})
        assert len(coding_genes) == 1
        assert coding_genes[0].symbol == "CODING"

    def test_update_entity(self, test_session):
        """Test updating an entity."""
        repo = GeneRepository(test_session)

        # Create a gene
        gene = GeneModel(gene_id="TEST001", symbol="TEST", name="Original Name")
        created_gene = repo.create(gene)

        # Update the gene
        updated_gene = repo.update(created_gene.id, {"name": "Updated Name"})

        assert updated_gene.name == "Updated Name"
        assert updated_gene.id == created_gene.id

    def test_update_nonexistent_entity(self, test_session):
        """Test updating a non-existent entity."""
        repo = GeneRepository(test_session)

        with pytest.raises(NotFoundError):
            repo.update(999, {"name": "New Name"})

    def test_delete_entity(self, test_session):
        """Test deleting an entity."""
        repo = GeneRepository(test_session)

        # Create a gene
        gene = GeneModel(gene_id="TEST001", symbol="TEST")
        created_gene = repo.create(gene)

        # Delete the gene
        deleted = repo.delete(created_gene.id)
        assert deleted is True

        # Verify it's gone
        retrieved = repo.get_by_id(created_gene.id)
        assert retrieved is None

    def test_delete_nonexistent_entity(self, test_session):
        """Test deleting a non-existent entity."""
        repo = GeneRepository(test_session)

        deleted = repo.delete(999)
        assert deleted is False

    def test_count_entities(self, test_session):
        """Test counting entities."""
        repo = GeneRepository(test_session)

        # Initially empty
        assert repo.count() == 0

        # Add some genes
        genes = [GeneModel(gene_id=f"TEST00{i}", symbol=f"T{i}") for i in range(1, 4)]
        for gene in genes:
            repo.create(gene)

        assert repo.count() == 3

    def test_exists_entity(self, test_session):
        """Test checking if entity exists."""
        repo = GeneRepository(test_session)

        # Create a gene
        gene = GeneModel(gene_id="TEST001", symbol="TEST")
        created_gene = repo.create(gene)

        # Check existence
        assert repo.exists(created_gene.id) is True
        assert repo.exists(999) is False

    def test_duplicate_creation_error(self, test_session):
        """Test that creating duplicate entities raises error."""
        repo = GeneRepository(test_session)

        # Create first gene
        gene1 = GeneModel(gene_id="TEST001", symbol="TEST")  # Unique constraint
        repo.create(gene1)

        # Try to create duplicate
        gene2 = GeneModel(gene_id="TEST001", symbol="TEST2")  # Same gene_id

        with pytest.raises(DuplicateError):
            repo.create(gene2)
