"""
Unit tests for identifier value objects.
"""

import pytest
from src.models.value_objects.identifiers import (
    GeneIdentifier,
    VariantIdentifier,
    PhenotypeIdentifier,
    PublicationIdentifier,
)


class TestGeneIdentifier:
    """Test GeneIdentifier value object."""

    def test_create_gene_identifier(self):
        """Test creating a valid GeneIdentifier."""
        identifier = GeneIdentifier(
            gene_id="GENE123",
            symbol="TEST",
            ensembl_id="ENSG000001",
            ncbi_gene_id=12345,
            uniprot_id="P12345",
        )

        assert identifier.gene_id == "GENE123"
        assert identifier.symbol == "TEST"  # Should be uppercased
        assert identifier.ensembl_id == "ENSG000001"
        assert identifier.ncbi_gene_id == 12345
        assert identifier.uniprot_id == "P12345"

    def test_gene_symbol_uppercase_validation(self):
        """Test that gene symbol is automatically uppercased."""
        identifier = GeneIdentifier(gene_id="GENE123", symbol="test")

        assert identifier.symbol == "TEST"

    def test_gene_id_uppercase_validation(self):
        """Test that gene_id is automatically uppercased."""
        identifier = GeneIdentifier(gene_id="gene123", symbol="TEST")

        assert identifier.gene_id == "GENE123"

    def test_invalid_ensembl_id(self):
        """Test invalid Ensembl ID format."""
        with pytest.raises(ValueError):
            GeneIdentifier(gene_id="GENE123", symbol="TEST", ensembl_id="INVALID")

    def test_immutable(self):
        """Test that GeneIdentifier is immutable."""
        identifier = GeneIdentifier(gene_id="GENE123", symbol="TEST")

        with pytest.raises(
            Exception
        ):  # Pydantic raises ValidationError for frozen instances
            identifier.symbol = "NEW"

    def test_string_representation(self):
        """Test string representation."""
        identifier = GeneIdentifier(gene_id="GENE123", symbol="TEST")

        assert str(identifier) == "TEST"


class TestVariantIdentifier:
    """Test VariantIdentifier value object."""

    def test_create_variant_identifier(self):
        """Test creating a valid VariantIdentifier."""
        identifier = VariantIdentifier(
            variant_id="VAR001",
            clinvar_id="VCV000001",
            hgvs_genomic="NC_000001.11:g.12345A>G",
            hgvs_protein="NP_001:p.Val123Met",
        )

        assert identifier.variant_id == "VAR001"
        assert identifier.clinvar_id == "VCV000001"
        assert identifier.hgvs_genomic == "NC_000001.11:g.12345A>G"
        assert identifier.hgvs_protein == "NP_001:p.Val123Met"

    def test_invalid_clinvar_id(self):
        """Test invalid ClinVar ID format."""
        with pytest.raises(ValueError):
            VariantIdentifier(variant_id="VAR001", clinvar_id="INVALID")

    def test_immutable(self):
        """Test that VariantIdentifier is immutable."""
        identifier = VariantIdentifier(variant_id="VAR001")

        with pytest.raises(
            Exception
        ):  # Pydantic raises ValidationError for frozen instances
            identifier.variant_id = "NEW"

    def test_string_representation(self):
        """Test string representation."""
        identifier = VariantIdentifier(variant_id="VAR001")

        assert str(identifier) == "VAR001"


class TestPhenotypeIdentifier:
    """Test PhenotypeIdentifier value object."""

    def test_create_phenotype_identifier(self):
        """Test creating a valid PhenotypeIdentifier."""
        identifier = PhenotypeIdentifier(hpo_id="HP:0001234", hpo_term="Test phenotype")

        assert identifier.hpo_id == "HP:0001234"
        assert identifier.hpo_term == "Test phenotype"

    def test_invalid_hpo_id_format(self):
        """Test invalid HPO ID format."""
        with pytest.raises(ValueError):
            PhenotypeIdentifier(hpo_id="INVALID", hpo_term="Test")

    def test_invalid_hpo_id_length(self):
        """Test HPO ID with wrong length."""
        with pytest.raises(ValueError):
            PhenotypeIdentifier(hpo_id="HP:123", hpo_term="Test")

    def test_immutable(self):
        """Test that PhenotypeIdentifier is immutable."""
        identifier = PhenotypeIdentifier(hpo_id="HP:0001234", hpo_term="Test")

        with pytest.raises(
            Exception
        ):  # Pydantic raises ValidationError for frozen instances
            identifier.hpo_term = "New"

    def test_string_representation(self):
        """Test string representation."""
        identifier = PhenotypeIdentifier(hpo_id="HP:0001234", hpo_term="Test phenotype")

        assert str(identifier) == "HP:0001234 (Test phenotype)"


class TestPublicationIdentifier:
    """Test PublicationIdentifier value object."""

    def test_create_publication_identifier(self):
        """Test creating a valid PublicationIdentifier."""
        identifier = PublicationIdentifier(
            pubmed_id="12345678", pmc_id="PMC123456", doi="10.1234/test.12345"
        )

        assert identifier.pubmed_id == "12345678"
        assert identifier.pmc_id == "PMC123456"
        assert identifier.doi == "10.1234/test.12345"

    def test_get_primary_id_pubmed(self):
        """Test getting primary ID when PubMed ID is available."""
        identifier = PublicationIdentifier(
            pubmed_id="12345678", doi="10.1234/test.12345"
        )

        assert identifier.get_primary_id() == "12345678"

    def test_get_primary_id_pmc(self):
        """Test getting primary ID when PMC ID is available."""
        identifier = PublicationIdentifier(pmc_id="PMC123456", doi="10.1234/test.12345")

        assert identifier.get_primary_id() == "PMC123456"

    def test_get_primary_id_doi(self):
        """Test getting primary ID when DOI is available."""
        identifier = PublicationIdentifier(doi="10.1234/test.12345")

        assert identifier.get_primary_id() == "10.1234/test.12345"

    def test_invalid_doi_format(self):
        """Test invalid DOI format."""
        with pytest.raises(ValueError):
            PublicationIdentifier(doi="invalid-doi")

    def test_immutable(self):
        """Test that PublicationIdentifier is immutable."""
        identifier = PublicationIdentifier(pubmed_id="12345678")

        with pytest.raises(
            Exception
        ):  # Pydantic raises ValidationError for frozen instances
            identifier.pubmed_id = "NEW"

    def test_string_representation(self):
        """Test string representation."""
        identifier = PublicationIdentifier(pubmed_id="12345678")

        assert str(identifier) == "12345678"
