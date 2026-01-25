"""
Unit tests for MechanismMapper.
"""

from datetime import UTC, datetime

from src.domain.entities.mechanism import Mechanism
from src.domain.value_objects.confidence import EvidenceLevel
from src.domain.value_objects.protein_structure import ProteinDomain
from src.infrastructure.mappers.mechanism_mapper import MechanismMapper
from src.models.database.mechanism import MechanismModel
from src.models.database.phenotype import PhenotypeModel


def test_mechanism_mapper_to_domain() -> None:
    now = datetime.now(UTC)
    mechanism_model = MechanismModel(
        name="Mediator complex disruption",
        description="Test mechanism",
        evidence_tier="strong",
        confidence_score=0.85,
        source="manual",
        protein_domains=[
            {
                "name": "Mediator binding",
                "start_residue": 10,
                "end_residue": 50,
                "domain_type": "structural",
            },
        ],
        created_at=now,
        updated_at=now,
    )
    phenotype = PhenotypeModel(
        hpo_id="HP:0000001",
        hpo_term="All",
        name="All",
        category="other",
    )
    phenotype.id = 1
    mechanism_model.phenotypes = [phenotype]

    mechanism = MechanismMapper.to_domain(mechanism_model)

    assert mechanism.name == "Mediator complex disruption"
    assert mechanism.evidence_tier == EvidenceLevel.STRONG
    assert mechanism.protein_domains[0].name == "Mediator binding"
    assert mechanism.phenotype_ids == [1]


def test_mechanism_mapper_to_model() -> None:
    domain = ProteinDomain(name="Mediator binding", start_residue=10, end_residue=50)
    mechanism = Mechanism(
        name="Mediator complex disruption",
        evidence_tier=EvidenceLevel.STRONG,
        confidence_score=0.9,
        source="manual",
        protein_domains=[domain],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    model = MechanismMapper.to_model(mechanism)

    assert model.name == "Mediator complex disruption"
    assert model.evidence_tier == "strong"
    assert model.protein_domains[0]["name"] == "Mediator binding"
