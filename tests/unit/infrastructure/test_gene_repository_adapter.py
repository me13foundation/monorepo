import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.domain.entities.gene import Gene
from src.infrastructure.repositories import SqlAlchemyGeneRepository
from src.models.database import Base


@pytest.fixture
def test_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


def test_create_and_fetch_gene(test_session):
    repository = SqlAlchemyGeneRepository(test_session)

    gene = Gene.create(symbol="MED13", name="MED13 Gene")
    created = repository.create(gene)

    assert isinstance(created, Gene)
    assert created.id is not None
    assert created.symbol == "MED13"

    fetched = repository.find_by_gene_id("MED13")
    assert fetched is not None
    assert fetched.id == created.id


def test_update_gene_properties(test_session):
    repository = SqlAlchemyGeneRepository(test_session)
    gene = repository.create(Gene.create(symbol="MED13L", name="Original"))

    assert gene.id is not None

    updated = repository.update(gene.id, {"name": "Updated"})
    assert updated.name == "Updated"


def test_paginate_genes_returns_domain_entities(test_session):
    repository = SqlAlchemyGeneRepository(test_session)

    for index in range(3):
        repository.create(Gene.create(symbol=f"GENE{index}", name=f"Gene {index}"))

    results, total = repository.paginate_genes(
        page=1, per_page=2, sort_by="symbol", sort_order="asc"
    )

    assert total == 3
    assert len(results) == 2
    assert all(isinstance(gene, Gene) for gene in results)
