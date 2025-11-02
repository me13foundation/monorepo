import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.domain.entities.publication import Publication
from src.domain.value_objects.identifiers import PublicationIdentifier
from src.infrastructure.repositories import SqlAlchemyPublicationRepository
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


def test_publication_repository_roundtrip(test_session):
    repository = SqlAlchemyPublicationRepository(test_session)
    identifier = PublicationIdentifier(pubmed_id="12345678")
    publication = Publication(
        identifier=identifier,
        title="MED13 study",
        authors=("Doe J", "Smith A"),
        journal="Genome Research",
        publication_year=2022,
        keywords=("med13",),
    )

    created = repository.create(publication)
    assert created.id is not None

    search_results = repository.search_publications("MED13")
    assert any(result.identifier.pubmed_id == "12345678" for result in search_results)
