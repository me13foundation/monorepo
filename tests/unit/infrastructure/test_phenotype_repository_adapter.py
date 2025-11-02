import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.domain.entities.phenotype import Phenotype, PhenotypeCategory
from src.domain.value_objects.identifiers import PhenotypeIdentifier
from src.infrastructure.repositories import SqlAlchemyPhenotypeRepository
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


def test_create_and_fetch_phenotype(test_session):
    repository = SqlAlchemyPhenotypeRepository(test_session)
    identifier = PhenotypeIdentifier(hpo_id="HP:0000001", hpo_term="Phenotype")
    phenotype = Phenotype(
        identifier=identifier,
        name="Phenotype",
        category=PhenotypeCategory.NEUROLOGICAL,
        synonyms=("Term A", "Term B"),
    )

    created = repository.create(phenotype)
    assert created.id is not None

    fetched = repository.find_by_hpo_id(identifier.hpo_id)
    assert fetched is not None
    assert fetched.identifier.hpo_id == identifier.hpo_id
    assert "Term A" in fetched.synonyms
