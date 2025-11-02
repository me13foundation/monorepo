import pytest

from src.domain.entities.variant import (
    ClinicalSignificance,
    Variant,
    VariantType,
)
from src.domain.value_objects.identifiers import GeneIdentifier, VariantIdentifier


def build_identifier(symbol: str = "MED13") -> GeneIdentifier:
    return GeneIdentifier(gene_id=symbol, symbol=symbol)


def test_variant_create_defaults() -> None:
    variant = Variant.create(
        chromosome="1",
        position=100,
        reference_allele="A",
        alternate_allele="T",
        gene_identifier=build_identifier(),
    )

    assert variant.chromosome == "CHR1"
    assert variant.variant_type == VariantType.UNKNOWN
    assert variant.clinical_significance == ClinicalSignificance.NOT_PROVIDED
    assert variant.gene_symbol == "MED13"


def test_variant_update_classification_validates() -> None:
    identifier = VariantIdentifier(variant_id="chr1:100:A>T")
    variant = Variant(
        identifier=identifier,
        chromosome="chr1",
        position=100,
        reference_allele="A",
        alternate_allele="T",
    )

    variant.update_classification(
        variant_type=VariantType.SNV,
        clinical_significance=ClinicalSignificance.PATHOGENIC,
    )

    assert variant.variant_type == VariantType.SNV
    assert variant.clinical_significance == ClinicalSignificance.PATHOGENIC


def test_variant_frequency_validation() -> None:
    identifier = VariantIdentifier(variant_id="chr1:100:A>T")
    with pytest.raises(ValueError):
        Variant(
            identifier=identifier,
            chromosome="chr1",
            position=100,
            reference_allele="A",
            alternate_allele="T",
            allele_frequency=1.5,
        )
