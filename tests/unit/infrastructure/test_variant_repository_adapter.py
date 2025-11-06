import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.domain.entities.variant import ClinicalSignificance, Variant
from src.domain.value_objects.identifiers import GeneIdentifier
from src.infrastructure.repositories import SqlAlchemyVariantRepository
from src.models.database import Base, GeneModel, VariantModel


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


@pytest.fixture
def persisted_gene(test_session):
    gene = GeneModel(gene_id="GENE001", symbol="MED13")
    test_session.add(gene)
    test_session.commit()
    return gene


def test_variant_repository_creates_domain_variant(test_session, persisted_gene):
    repository = SqlAlchemyVariantRepository(test_session)
    gene_identifier = GeneIdentifier(
        gene_id=persisted_gene.gene_id,
        symbol=persisted_gene.symbol,
    )

    variant = Variant.create(
        chromosome="1",
        position=42,
        reference_allele="A",
        alternate_allele="T",
        gene_database_id=persisted_gene.id,
        gene_identifier=gene_identifier,
    )

    created = repository.create(variant)

    assert isinstance(created, Variant)
    assert created.id is not None
    assert created.gene_database_id == persisted_gene.id
    assert created.variant_id.startswith("1:42")


def test_variant_repository_finds_pathogenic_variants(test_session, persisted_gene):
    variant = VariantModel(
        gene_id=persisted_gene.id,
        variant_id="chr1:100:A>T",
        clinvar_id="VCV0001",
        chromosome="chr1",
        position=100,
        reference_allele="A",
        alternate_allele="T",
        clinical_significance=ClinicalSignificance.PATHOGENIC,
    )

    test_session.add(variant)
    test_session.commit()

    repository = SqlAlchemyVariantRepository(test_session)
    variants = repository.find_pathogenic_variants()

    assert len(variants) == 1
    assert variants[0].clinical_significance == ClinicalSignificance.PATHOGENIC
