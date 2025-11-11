"""
Property-based tests for gene identifier normalization.

These tests ensure that the GeneDomainService normalization helpers
preserve the invariants described in docs/type_examples.md by using
Hypothesis-generated inputs instead of fixed fixtures.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from src.domain.services.gene_domain_service import GeneDomainService
from src.domain.value_objects.identifiers import GeneIdentifier

identifier_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
identifier_text = st.text(alphabet=list(identifier_chars), min_size=1, max_size=20)


@st.composite
def gene_identifier_inputs(draw: st.DrawFn) -> GeneIdentifier:
    """Generate valid GeneIdentifier instances for property testing."""
    symbol = draw(identifier_text)
    gene_id = draw(identifier_text)

    ensembl = draw(
        st.none()
        | st.integers(min_value=1_000_000, max_value=9_999_999).map(
            lambda value: f"ENSG{value}",
        ),
    )
    uniprot = draw(
        st.none()
        | st.text(
            alphabet=list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"),
            min_size=3,
            max_size=12,
        ),
    )
    ncbi = draw(st.none() | st.integers(min_value=1, max_value=999_999))

    return GeneIdentifier(
        gene_id=gene_id,
        symbol=symbol,
        ensembl_id=ensembl,
        ncbi_gene_id=ncbi,
        uniprot_id=uniprot,
    )


service = GeneDomainService()


@given(identifier=gene_identifier_inputs())
def test_normalize_gene_identifiers_always_uppercase(
    identifier: GeneIdentifier,
) -> None:
    """Normalized identifiers must be uppercase and non-empty."""
    normalized = service.normalize_gene_identifiers(identifier)

    assert normalized.symbol == normalized.symbol.upper()
    assert normalized.gene_id == normalized.gene_id.upper()
    assert normalized.symbol
    assert normalized.gene_id

    if normalized.uniprot_id is not None:
        assert normalized.uniprot_id == normalized.uniprot_id.upper()


@given(identifier=gene_identifier_inputs())
def test_normalize_gene_identifiers_preserves_external_ids(
    identifier: GeneIdentifier,
) -> None:
    """Normalization must not drop optional identifiers."""
    normalized = service.normalize_gene_identifiers(identifier)

    assert normalized.ensembl_id == identifier.ensembl_id
    assert normalized.ncbi_gene_id == identifier.ncbi_gene_id
