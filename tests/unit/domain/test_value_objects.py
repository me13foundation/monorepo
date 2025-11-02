import pytest

from src.domain.value_objects.confidence import Confidence, EvidenceLevel
from src.domain.value_objects.identifiers import (
    GeneIdentifier,
    PhenotypeIdentifier,
    PublicationIdentifier,
    VariantIdentifier,
)
from src.domain.value_objects.provenance import DataSource, Provenance


def test_gene_identifier_normalizes_and_validates() -> None:
    identifier = GeneIdentifier(gene_id="med13", symbol="med13l")
    assert identifier.gene_id == "MED13"
    assert identifier.symbol == "MED13L"


def test_gene_identifier_rejects_invalid_pattern() -> None:
    with pytest.raises(ValueError):
        GeneIdentifier(gene_id="invalid space", symbol="MED13")


def test_variant_identifier_validates_clinvar() -> None:
    with pytest.raises(ValueError):
        VariantIdentifier(variant_id="1", clinvar_id="BAD")


def test_phenotype_identifier_requires_hpo_format() -> None:
    with pytest.raises(ValueError):
        PhenotypeIdentifier(hpo_id="HP:123", hpo_term="term")


def test_publication_identifier_primary_id_resolution() -> None:
    identifier = PublicationIdentifier(pubmed_id="12345")
    assert identifier.get_primary_id() == "12345"


def test_confidence_from_score_sets_level() -> None:
    confidence = Confidence.from_score(0.85, peer_reviewed=True)
    assert confidence.level == EvidenceLevel.STRONG
    assert confidence.peer_reviewed is True


def test_provenance_add_processing_step() -> None:
    provenance = Provenance(source=DataSource.MANUAL, acquired_by="tester")
    updated = provenance.add_processing_step("normalize")
    assert provenance.processing_steps == ()
    assert updated.processing_steps == ("normalize",)
