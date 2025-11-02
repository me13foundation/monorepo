import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.domain.entities.evidence import Evidence, EvidenceType
from src.domain.value_objects.confidence import Confidence, EvidenceLevel
from src.domain.value_objects.identifiers import (
    PhenotypeIdentifier,
    PublicationIdentifier,
    VariantIdentifier,
)
from src.infrastructure.repositories import SqlAlchemyEvidenceRepository
from src.models.database import (
    Base,
    GeneModel,
    PhenotypeModel,
    PublicationModel,
    VariantModel,
)


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


def seed_related_records(session):
    gene = GeneModel(gene_id="GENE001", symbol="MED13")
    session.add(gene)
    session.flush()

    variant = VariantModel(
        gene_id=gene.id,
        variant_id="chr1:100:A>T",
        clinvar_id="VCV0001",
        chromosome="chr1",
        position=100,
        reference_allele="A",
        alternate_allele="T",
        clinical_significance="pathogenic",
    )
    session.add(variant)

    phenotype = PhenotypeModel(
        hpo_id="HP:0000001",
        hpo_term="Phenotype",
        name="Phenotype",
        category="other",
        is_root_term=False,
    )
    session.add(phenotype)

    publication = PublicationModel(
        pubmed_id="12345678",
        title="Study",
        authors='["Doe J"]',
        journal="Journal",
        publication_year=2020,
    )
    session.add(publication)
    session.commit()
    return variant, phenotype, publication


def test_evidence_repository_maps_domain(test_session):
    variant_model, phenotype_model, publication_model = seed_related_records(
        test_session
    )
    repository = SqlAlchemyEvidenceRepository(test_session)

    evidence = Evidence(
        variant_id=variant_model.id,
        phenotype_id=phenotype_model.id,
        description="Clinically validated",
        evidence_level=EvidenceLevel.STRONG,
        evidence_type=EvidenceType.CLINICAL_REPORT,
        confidence=Confidence.from_score(0.85, peer_reviewed=True),
        publication_id=publication_model.id,
        variant_identifier=VariantIdentifier(variant_id=variant_model.variant_id),
        phenotype_identifier=PhenotypeIdentifier(
            hpo_id=phenotype_model.hpo_id,
            hpo_term=phenotype_model.hpo_term,
        ),
        publication_identifier=PublicationIdentifier(
            pubmed_id=publication_model.pubmed_id
        ),
    )

    created = repository.create(evidence)
    assert created.id is not None

    results = repository.find_by_variant(variant_model.id)
    assert len(results) == 1
    assert results[0].variant_identifier is not None
