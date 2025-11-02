import pytest

from src.domain.entities.phenotype import Phenotype, PhenotypeCategory
from src.domain.value_objects.identifiers import PhenotypeIdentifier


def test_phenotype_synonym_normalization() -> None:
    identifier = PhenotypeIdentifier(hpo_id="HP:0000001", hpo_term="Generic")
    phenotype = Phenotype(
        identifier=identifier,
        name="Generic phenotype",
        synonyms=("Fatigue", " fatigue ", "Energy loss"),
        category=PhenotypeCategory.NEUROLOGICAL,
        severity_score=3,
    )

    assert phenotype.category == PhenotypeCategory.NEUROLOGICAL
    assert phenotype.synonyms == ("Fatigue", "Energy loss")


def test_phenotype_add_synonym_validates() -> None:
    identifier = PhenotypeIdentifier(hpo_id="HP:0000002", hpo_term="Other")
    phenotype = Phenotype(identifier=identifier, name="Other phenotype")

    phenotype.add_synonym("New term")
    assert "New term" in phenotype.synonyms

    with pytest.raises(ValueError):
        phenotype.add_synonym("   ")
