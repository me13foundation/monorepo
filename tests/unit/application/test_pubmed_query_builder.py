from datetime import date

import pytest

from src.application.services.pubmed_query_builder import PubMedQueryBuilder
from src.domain.entities.data_discovery_parameters import AdvancedQueryParameters


def test_pubmed_query_builder_validates_dates():
    builder = PubMedQueryBuilder()
    params = AdvancedQueryParameters(
        gene_symbol="MED13",
        search_term="development",
        date_from=date(2024, 1, 1),
        date_to=date(2024, 12, 31),
    )
    builder.validate(params)  # Should not raise

    invalid = params.model_copy(update={"date_to": date(2023, 12, 31)})
    with pytest.raises(ValueError):
        builder.validate(invalid)


def test_pubmed_query_builder_builds_query():
    builder = PubMedQueryBuilder()
    params = AdvancedQueryParameters(
        gene_symbol="MED13",
        search_term="cardiac",
        languages=["english"],
        publication_types=["clinical trial"],
        date_from=date(2024, 1, 1),
    )
    query = builder.build_query(params)
    assert "MED13" in query
    assert "cardiac" in query
    assert "english" in query.lower()
    assert "clinical trial" in query.lower()
