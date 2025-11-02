import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.database import (
    Base,
    EvidenceModel,
    GeneModel,
    PhenotypeModel,
    PublicationModel,
    VariantModel,
)
from src.services.domain.publication_service import PublicationService


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def seed_publication_with_evidence(db_session) -> int:
    gene = GeneModel(gene_id="GENE001", symbol="MED13")
    db_session.add(gene)
    db_session.flush()

    variant = VariantModel(
        gene_id=gene.id,
        variant_id="chr1:100:A>T",
        chromosome="chr1",
        position=100,
        reference_allele="A",
        alternate_allele="T",
        clinical_significance="pathogenic",
    )
    db_session.add(variant)

    phenotype = PhenotypeModel(
        hpo_id="HP:0000001",
        hpo_term="Phenotype",
        name="Phenotype",
        category="other",
        is_root_term=False,
    )
    db_session.add(phenotype)

    publication = PublicationModel(
        pubmed_id="12345678",
        title="MED13 Case Study",
        authors='["Doe J"]',
        journal="Journal",
        publication_year=2021,
    )
    db_session.add(publication)
    db_session.flush()

    evidence = EvidenceModel(
        variant_id=variant.id,
        phenotype_id=phenotype.id,
        publication_id=publication.id,
        evidence_level="strong",
        evidence_type="clinical_report",
        description="Validated evidence",
        confidence_score=0.8,
        reviewed=True,
    )
    db_session.add(evidence)
    db_session.commit()
    return publication.id


def test_publication_service_enriches_evidence(session):
    publication_id = seed_publication_with_evidence(session)
    service = PublicationService(session)

    publication = service.get_publication_with_evidence(publication_id)

    assert publication is not None
    assert len(publication.evidence) == 1
    assert publication.evidence[0].description == "Validated evidence"
