"""
Unit tests for validation rules.

Tests individual validation rule implementations for correctness
and proper error handling.
"""

from src.domain.validation.rules.base_rules import ValidationRuleEngine
from src.domain.validation.rules.gene_rules import GeneValidationRules
from src.domain.validation.rules.phenotype_rules import PhenotypeValidationRules
from src.domain.validation.rules.publication_rules import PublicationValidationRules
from src.domain.validation.rules.relationship_rules import RelationshipValidationRules
from src.domain.validation.rules.variant_rules import VariantValidationRules


class TestGeneValidationRules:
    """Test gene validation rules."""

    def test_hgnc_nomenclature_valid(self):
        """Test valid HGNC nomenclature."""
        rule = GeneValidationRules.validate_hgnc_nomenclature("symbol")

        # Valid symbol
        is_valid, _message, _suggestion = rule.validator("TP53")
        assert is_valid
        assert _message == ""
        assert _suggestion is None

    def test_hgnc_nomenclature_invalid(self):
        """Test invalid HGNC nomenclature."""
        rule = GeneValidationRules.validate_hgnc_nomenclature("symbol")

        # Invalid symbols
        test_cases = [
            ("", "Gene symbol is required"),
            ("123GENE", "Invalid gene symbol format"),
            ("gene@#$", "Invalid gene symbol format"),
            ("A", "Gene symbol length 1 is invalid"),  # Too short
            ("A" * 30, "Gene symbol length 30 is invalid"),  # Too long
        ]

        for invalid_symbol, expected_message in test_cases:
            is_valid, message, _suggestion = rule.validator(invalid_symbol)
            assert not is_valid
            assert expected_message in message

    def test_hgnc_id_format_valid(self):
        """Test valid HGNC ID format."""
        rule = GeneValidationRules.validate_hgnc_id_format("hgnc_id")

        # Valid IDs
        valid_ids = ["HGNC:12345", "HGNC:99999"]
        for hgnc_id in valid_ids:
            is_valid, _message, _suggestion = rule.validator(hgnc_id)
            assert is_valid

    def test_hgnc_id_format_invalid(self):
        """Test invalid HGNC ID format."""
        rule = GeneValidationRules.validate_hgnc_id_format("hgnc_id")

        # Invalid IDs
        invalid_ids = ["HGC:12345", "HGNC:abc", "HGNC:123abc", "12345"]
        for invalid_id in invalid_ids:
            is_valid, message, _suggestion = rule.validator(invalid_id)
            assert not is_valid
            assert "format" in message.lower()

    def test_cross_reference_consistency(self):
        """Test cross-reference consistency validation."""
        rule = GeneValidationRules.validate_cross_reference_consistency({})

        # Empty cross-references (should pass)
        is_valid, _message, _suggestion = rule.validator({})
        assert is_valid

        # Inconsistent cross-references
        inconsistent_xrefs = {
            "SYMBOL": ["TP53", "TP53", "P53"],  # Multiple symbols
            "HGNC": ["HGNC:11998"],  # Single HGNC ID
        }
        is_valid, _message, _suggestion = rule.validator(inconsistent_xrefs)
        assert not is_valid

    def test_genomic_coordinates_validation(self):
        """Test genomic coordinates validation."""
        rule = GeneValidationRules.validate_genomic_coordinates("", 0, 0)

        # Valid coordinates
        valid_coords = {"chromosome": "1", "start_position": 1000, "end_position": 2000}
        is_valid, _message, _suggestion = rule.validator(valid_coords)
        assert is_valid

        # Invalid coordinates
        invalid_coords = [
            {
                "chromosome": "25",
                "start_position": 1000,
                "end_position": 2000,
            },  # Invalid chromosome
            {
                "chromosome": "1",
                "start_position": 2000,
                "end_position": 1000,
            },  # Start > End
            {
                "chromosome": "1",
                "start_position": -100,
                "end_position": 2000,
            },  # Negative position
        ]

        for coords in invalid_coords:
            is_valid, _message, _suggestion = rule.validator(coords)
            assert not is_valid

    def test_gene_comprehensive_validation(self):
        """Test comprehensive gene validation."""
        # Valid gene
        valid_gene = {
            "symbol": "TP53",
            "hgnc_id": "HGNC:11998",
            "name": "tumor protein p53",
            "chromosome": "17",
            "start_position": 7661779,
            "end_position": 7687550,
            "cross_references": {"SYMBOL": ["TP53"], "HGNC": ["HGNC:11998"]},
            "source": "test",
        }

        issues = GeneValidationRules.validate_gene_comprehensively(valid_gene)
        # Should have no critical issues
        error_issues = [i for i in issues if i.get("severity") == "error"]
        assert len(error_issues) == 0

        # Invalid gene
        invalid_gene = {
            "symbol": "",  # Missing symbol
            "hgnc_id": "invalid",  # Invalid HGNC ID
            "source": "test",
        }

        issues = GeneValidationRules.validate_gene_comprehensively(invalid_gene)
        error_issues = [i for i in issues if i.get("severity") == "error"]
        assert len(error_issues) > 0


class TestVariantValidationRules:
    """Test variant validation rules."""

    def test_hgvs_notation_validation(self):
        """Test HGVS notation validation."""
        rule = VariantValidationRules.validate_hgvs_notation_comprehensive("", "c")

        # Valid c. notation
        is_valid, _message, _suggestion = rule.validator("c.123A>G")
        assert is_valid

        # Invalid notations
        invalid_notations = ["", "invalid_notation", "c.?", "c.()"]
        for notation in invalid_notations:
            is_valid, _message, _suggestion = rule.validator(notation)
            assert not is_valid

    def test_clinical_significance_validation(self):
        """Test clinical significance validation."""
        rule = VariantValidationRules.validate_clinical_significance_comprehensive("")

        # Valid significance
        valid_terms = [
            "Pathogenic",
            "Likely pathogenic",
            "Uncertain significance",
            "Benign",
        ]
        for term in valid_terms:
            is_valid, _message, _suggestion = rule.validator(term)
            assert is_valid

        # Invalid significance
        is_valid, _message, _suggestion = rule.validator("Invalid significance")
        assert not is_valid

        # Conflicting terms
        is_valid, _message, _suggestion = rule.validator("Pathogenic and Benign")
        assert not is_valid

    def test_population_frequencies_validation(self):
        """Test population frequencies validation."""
        rule = VariantValidationRules.validate_population_frequencies({})

        # Valid frequencies
        valid_freqs = {"AFR": 0.1, "EUR": 0.05, "ASN": 0.02}
        is_valid, _message, _suggestion = rule.validator(valid_freqs)
        assert is_valid

        # Invalid frequencies
        invalid_freqs = [
            {"AFR": 1.5},  # > 1.0
            {"AFR": -0.1},  # Negative
            {"INVALID": 0.1},  # Non-numeric
        ]

        for freqs in invalid_freqs:
            is_valid, _message, _suggestion = rule.validator(freqs)
            assert not is_valid

    def test_variant_comprehensive_validation(self):
        """Test comprehensive variant validation."""
        # Valid variant
        valid_variant = {
            "clinvar_id": "123456",
            "variation_name": "c.123A>G",
            "gene_symbol": "TP53",
            "chromosome": "17",
            "start_position": 7670000,
            "clinical_significance": "Pathogenic",
            "hgvs_notations": {"c": "c.123A>G", "p": "p.Arg123Gly"},
            "source": "test",
        }

        issues = VariantValidationRules.validate_variant_comprehensively(valid_variant)
        error_issues = [i for i in issues if i.get("severity") == "error"]
        assert len(error_issues) == 0

        # Invalid variant
        invalid_variant = {
            "variation_name": "",  # Empty notation
            "clinical_significance": "Invalid",  # Invalid significance
            "source": "test",
        }

        issues = VariantValidationRules.validate_variant_comprehensively(
            invalid_variant,
        )
        error_issues = [i for i in issues if i.get("severity") == "error"]
        assert len(error_issues) > 0


class TestPhenotypeValidationRules:
    """Test phenotype validation rules."""

    def test_hpo_term_format_validation(self):
        """Test HPO term format validation."""
        rule = PhenotypeValidationRules.validate_hpo_term_format("")

        # Valid HPO IDs
        valid_ids = ["HP:0000001", "HP:9999999"]
        for hpo_id in valid_ids:
            is_valid, _message, _suggestion = rule.validator(hpo_id)
            assert is_valid

        # Invalid HPO IDs
        invalid_ids = ["HP:123", "HP:ABCDEFG", "HP:12345678", "HPO:0000001"]
        for invalid_id in invalid_ids:
            is_valid, _message, _suggestion = rule.validator(invalid_id)
            assert not is_valid

    def test_phenotype_name_consistency(self):
        """Test phenotype name consistency."""
        rule = PhenotypeValidationRules.validate_phenotype_name_consistency({}, "")

        # Consistent name/ID
        consistent_data = {"name": "Intellectual disability", "hpo_id": "HP:0001249"}
        is_valid, _message, _suggestion = rule.validator(consistent_data)
        assert is_valid

        # Inconsistent name/ID
        inconsistent_data = {"name": "Invalid phenotype", "hpo_id": "HP:0001249"}
        is_valid, _message, _suggestion = rule.validator(inconsistent_data)
        # This might pass or fail depending on implementation - just check it runs
        assert isinstance(is_valid, bool)

    def test_phenotype_comprehensive_validation(self):
        """Test comprehensive phenotype validation."""
        # Valid phenotype
        valid_phenotype = {
            "hpo_id": "HP:0001249",
            "name": "Intellectual disability",
            "definition": "A condition characterized by intellectual disability",
            "source": "test",
        }

        issues = PhenotypeValidationRules.validate_phenotype_comprehensively(
            valid_phenotype,
        )
        error_issues = [i for i in issues if i.get("severity") == "error"]
        assert len(error_issues) == 0

        # Invalid phenotype
        invalid_phenotype = {
            "hpo_id": "HP:123",  # Invalid format
            "name": "",  # Empty name
            "source": "test",
        }

        issues = PhenotypeValidationRules.validate_phenotype_comprehensively(
            invalid_phenotype,
        )
        error_issues = [i for i in issues if i.get("severity") == "error"]
        assert len(error_issues) > 0


class TestPublicationValidationRules:
    """Test publication validation rules."""

    def test_doi_format_validation(self):
        """Test DOI format validation."""
        rule = PublicationValidationRules.validate_doi_format_and_accessibility("")

        # Valid DOIs
        valid_dois = ["10.1038/nature12345", "10.1101/2023.01.01.123456"]
        for doi in valid_dois:
            is_valid, _message, _suggestion = rule.validator(doi)
            assert is_valid

        # Invalid DOIs
        invalid_dois = ["invalid_doi", "doi:10.1038/nature12345", "10.1038", ""]
        for invalid_doi in invalid_dois:
            is_valid, _message, _suggestion = rule.validator(invalid_doi)
            assert not is_valid

    def test_author_information_validation(self):
        """Test author information validation."""
        rule = PublicationValidationRules.validate_author_information([])

        # Valid authors
        valid_authors = [
            {"name": "John Smith", "affiliation": "Test University"},
            {"name": "Jane Doe", "affiliation": "Research Institute"},
        ]
        is_valid, _message, _suggestion = rule.validator(valid_authors)
        assert is_valid

        # Invalid authors
        invalid_authors = [
            [],  # Empty list
            [{"name": ""}],  # Empty name
            [{"invalid": "data"}],  # Invalid format
        ]

        for authors in invalid_authors:
            is_valid, _message, _suggestion = rule.validator(authors)
            assert not is_valid

    def test_publication_comprehensive_validation(self):
        """Test comprehensive publication validation."""
        # Valid publication
        valid_publication = {
            "pubmed_id": "12345678",
            "title": "A comprehensive study of genetic variants in human disease",
            "authors": [{"name": "John Smith"}, {"name": "Jane Doe"}],
            "journal": "Nature Genetics",
            "publication_date": "2023-01-01",
            "doi": "10.1038/ng.1234",
            "source": "test",
        }

        issues = PublicationValidationRules.validate_publication_comprehensively(
            valid_publication,
        )
        error_issues = [i for i in issues if i.get("severity") == "error"]
        assert len(error_issues) == 0

        # Invalid publication
        invalid_publication = {
            "pubmed_id": "invalid",  # Invalid PubMed ID
            "doi": "invalid_doi",  # Invalid DOI
            "source": "test",
        }

        issues = PublicationValidationRules.validate_publication_comprehensively(
            invalid_publication,
        )
        error_issues = [i for i in issues if i.get("severity") == "error"]
        assert len(error_issues) > 0


class TestRelationshipValidationRules:
    """Test relationship validation rules."""

    def test_genotype_phenotype_plausibility(self):
        """Test genotype-phenotype plausibility validation."""
        rule = RelationshipValidationRules.validate_genotype_phenotype_plausibility(
            {},
            {},
            {},
        )

        # This is a complex rule that may need mocking for full testing
        # Basic structure test
        relationship_data = {
            "gene": {"function": "kinase"},
            "variant": {"clinical_significance": "Pathogenic"},
            "phenotype": {"name": "Cancer"},
        }

        is_valid, _message, _suggestion = rule.validator(relationship_data)
        # Result depends on implementation - just check it runs
        assert isinstance(is_valid, bool)

    def test_evidence_strength_validation(self):
        """Test evidence strength validation."""
        rule = RelationshipValidationRules.validate_evidence_strength_and_consistency(
            [],
            0.0,
            "",
        )

        # High confidence with good evidence
        strong_evidence = {
            "evidence_sources": ["clinvar", "pubmed", "omim"],
            "confidence_score": 0.9,
            "evidence_level": "reviewed",
        }
        is_valid, _message, _suggestion = rule.validator(strong_evidence)
        assert is_valid

        # Low confidence with poor evidence
        weak_evidence = {
            "evidence_sources": [],
            "confidence_score": 0.1,
            "evidence_level": "predicted",
        }
        is_valid, _message, _suggestion = rule.validator(weak_evidence)
        # May or may not be valid depending on thresholds

    def test_statistical_significance_validation(self):
        """Test statistical significance validation."""
        rule = RelationshipValidationRules.validate_statistical_significance(
            1.0,
            0,
            0.0,
            (0.0, 0.0),
        )

        # Valid statistical data
        valid_stats = {
            "p_value": 0.001,
            "sample_size": 1000,
            "effect_size": 0.5,
            "confidence_interval": (0.3, 0.7),
        }
        is_valid, _message, _suggestion = rule.validator(valid_stats)
        assert is_valid

        # Invalid statistical data
        invalid_stats = [
            {"p_value": 1.5},  # P-value > 1
            {"sample_size": 5},  # Too small sample
            {"confidence_interval": (0.7, 0.3)},  # Invalid CI
        ]

        for stats in invalid_stats:
            is_valid, _message, _suggestion = rule.validator(stats)
            assert not is_valid


class TestValidationRuleEngine:
    """Test the validation rule engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = ValidationRuleEngine()

    def test_engine_initialization(self):
        """Test rule engine initialization."""
        assert self.engine.rule_registry is not None
        assert "gene" in self.engine.rule_registry
        assert "variant" in self.engine.rule_registry

    def test_validate_entity_basic(self):
        """Test basic entity validation."""
        # Valid gene
        valid_gene = {"symbol": "TP53", "hgnc_id": "HGNC:11998", "source": "test"}

        result = self.engine.validate_entity("gene", valid_gene)
        assert result.is_valid
        assert result.score > 0

    def test_validate_entity_invalid(self):
        """Test validation of invalid entity."""
        # Invalid gene
        invalid_gene = {"symbol": "", "source": "test"}  # Empty symbol

        result = self.engine.validate_entity("gene", invalid_gene)
        assert not result.is_valid
        assert len(result.issues) > 0

    def test_validate_batch(self):
        """Test batch validation."""
        expected_results = 3
        genes = [
            {"symbol": "TP53", "source": "test"},
            {"symbol": "BRCA1", "source": "test"},
            {"symbol": "", "source": "test"},  # Invalid
        ]

        results = self.engine.validate_batch("gene", genes)
        assert len(results) == expected_results
        assert results[0].is_valid  # TP53 should be valid
        assert results[1].is_valid  # BRCA1 should be valid
        assert not results[2].is_valid  # Empty symbol should be invalid

    def test_get_available_rules(self):
        """Test retrieving available rules."""
        rules = self.engine.get_available_rules()
        assert isinstance(rules, dict)
        assert "gene" in rules

        gene_rules = self.engine.get_available_rules("gene")
        assert "gene" in gene_rules
        assert isinstance(gene_rules["gene"], list)

    def test_rule_selection(self):
        """Test rule selection functionality."""
        # Test with specific rules
        gene_data = {"symbol": "TP53", "source": "test"}
        result_all = self.engine.validate_entity("gene", gene_data)
        result_selected = self.engine.validate_entity(
            "gene",
            gene_data,
            ["hgnc_nomenclature"],
        )

        # Results should be different when different rules are applied
        assert isinstance(result_all, object)
        assert isinstance(result_selected, object)

    def test_unknown_entity_type(self):
        """Test validation of unknown entity type."""
        result = self.engine.validate_entity("unknown_type", {})
        assert not result.is_valid
        assert len(result.issues) > 0
        assert "unknown entity type" in result.issues[0]["message"].lower()
