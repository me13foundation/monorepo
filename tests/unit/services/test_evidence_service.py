from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.application.services.evidence_service import EvidenceApplicationService
from src.domain.services.evidence_domain_service import EvidenceDomainService
from src.infrastructure.repositories import SqlAlchemyEvidenceRepository
from src.models.database import (
    Base,
    EvidenceModel,
    GeneModel,
    PhenotypeModel,
    VariantModel,
)


@pytest.fixture
def session() -> Generator[Session, None, None]:
    """Create an in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    db_session = session_local()
    try:
        yield db_session
    finally:
        db_session.close()


def seed_high_confidence_evidence(db_session: Session) -> None:
    gene = GeneModel(gene_id="GENE001", symbol="MED13")
    db_session.add(gene)
    db_session.flush()

    variant = VariantModel(
        gene_id=gene.id,
        variant_id="chr1:200:G>C",
        chromosome="chr1",
        position=200,
        reference_allele="G",
        alternate_allele="C",
        clinical_significance="pathogenic",
    )
    db_session.add(variant)

    phenotype = PhenotypeModel(
        hpo_id="HP:0000003",
        hpo_term="Phenotype",
        name="Phenotype",
        category="other",
        is_root_term=False,
    )
    db_session.add(phenotype)
    db_session.flush()

    evidence = EvidenceModel(
        variant_id=variant.id,
        phenotype_id=phenotype.id,
        evidence_level="definitive",
        evidence_type="functional_study",
        description="High confidence evidence",
        confidence_score=0.95,
        reviewed=True,
    )
    db_session.add(evidence)
    db_session.commit()


def test_evidence_service_high_confidence(session: Session) -> None:
    seed_high_confidence_evidence(session)
    service = EvidenceApplicationService(
        evidence_repository=SqlAlchemyEvidenceRepository(session),
        evidence_domain_service=EvidenceDomainService(),
    )

    evidence_records = service.find_high_confidence_evidence()

    assert len(evidence_records) == 1
    assert evidence_records[0].description == "High confidence evidence"
