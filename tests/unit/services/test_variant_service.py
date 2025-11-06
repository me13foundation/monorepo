import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.domain.entities.variant import Variant
from src.models.database import (
    Base,
    EvidenceModel,
    GeneModel,
    PhenotypeModel,
    VariantModel,
)
from src.services.domain.variant_service import VariantService


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


def seed_variant_with_evidence(db_session) -> int:
    gene = GeneModel(gene_id="GENE001", symbol="MED13")
    db_session.add(gene)
    db_session.flush()

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
    db_session.add(variant)
    db_session.flush()

    phenotype = PhenotypeModel(
        hpo_id="HP:0000001",
        hpo_term="All phenotype",
        name="Generic phenotype",
        category="other",
        is_root_term=False,
    )
    db_session.add(phenotype)
    db_session.flush()

    evidence = EvidenceModel(
        variant_id=variant.id,
        phenotype_id=phenotype.id,
        evidence_level="strong",
        evidence_type="clinical_report",
        description="Supporting evidence",
        reviewed=True,
    )
    db_session.add(evidence)
    db_session.commit()

    return variant.id


def test_variant_service_returns_variant_with_evidence(session):
    variant_id = seed_variant_with_evidence(session)
    service = VariantService(session)

    result = service.get_variant_with_evidence(variant_id)

    assert isinstance(result, Variant)
    assert result.evidence_count == 1
    assert result.evidence[0].reviewed is True
