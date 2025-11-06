import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.database import Base, PhenotypeModel
from src.services.domain.phenotype_service import PhenotypeService


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    db_session = session_local()
    try:
        yield db_session
    finally:
        db_session.close()


def seed_hierarchy(db_session) -> str:
    parent = PhenotypeModel(
        hpo_id="HP:0000001",
        hpo_term="Root phenotype",
        name="Root phenotype",
        category="other",
        is_root_term=True,
    )
    db_session.add(parent)
    db_session.flush()

    child = PhenotypeModel(
        hpo_id="HP:0000002",
        hpo_term="Child phenotype",
        name="Child phenotype",
        category="other",
        parent_hpo_id=parent.hpo_id,
        is_root_term=False,
    )
    db_session.add(child)
    db_session.commit()
    return parent.hpo_id


def test_get_phenotype_hierarchy(session):
    parent_hpo_id = seed_hierarchy(session)
    service = PhenotypeService(session)

    hierarchy = service.get_phenotype_hierarchy(parent_hpo_id)

    assert hierarchy is not None
    assert hierarchy.phenotype.identifier.hpo_id == parent_hpo_id
    assert len(hierarchy.children) == 1
