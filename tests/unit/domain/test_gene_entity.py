from datetime import UTC, datetime

import pytest

from src.domain.entities.gene import Gene, GeneType
from src.domain.value_objects.provenance import DataSource, Provenance


def test_gene_create_normalizes_identifier() -> None:
    gene = Gene.create(
        symbol="med13",
        gene_type=GeneType.PROTEIN_CODING,
        chromosome="1",
        start_position=10,
        end_position=20,
    )
    assert gene.symbol == "MED13"
    assert gene.gene_id == "MED13"
    assert gene.chromosome == "CHR1"


def test_gene_set_location_validates_bounds() -> None:
    gene = Gene.create(symbol="MED13")
    with pytest.raises(ValueError):
        gene.set_location(start_position=100, end_position=50)


def test_gene_update_identifier_updates_fields() -> None:
    gene = Gene.create(symbol="MED13")
    gene.update_identifier(ensembl_id="ENSG000001")
    assert gene.ensembl_id == "ENSG000001"
    gene.update_identifier(symbol="med13l")
    assert gene.symbol == "MED13L"


def test_gene_attach_provenance_updates_timestamp() -> None:
    gene = Gene.create(symbol="MED13")
    original_updated = gene.updated_at
    provenance = Provenance(
        source=DataSource.MANUAL,
        acquired_by="tester",
        acquired_at=datetime(2023, 1, 1, tzinfo=UTC),
    )
    gene.attach_provenance(provenance)
    assert gene.provenance is provenance
    assert gene.updated_at > original_updated
