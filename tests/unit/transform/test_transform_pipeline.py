"""
Unit tests for data transformation pipeline components.
"""

import pytest
from unittest.mock import Mock, patch

from src.domain.transform.parsers.clinvar_parser import ClinVarParser, ClinVarVariant
from src.domain.transform.parsers.pubmed_parser import PubMedParser, PubMedPublication

from src.domain.transform.normalizers.gene_normalizer import (
    GeneNormalizer,
    NormalizedGene,
    GeneIdentifierType,
)
from src.domain.transform.normalizers.variant_normalizer import (
    VariantNormalizer,
    NormalizedVariant,
)

from src.domain.transform.mappers.gene_variant_mapper import (
    GeneVariantMapper,
    GeneVariantLink,
)

from src.domain.transform.transformers.etl_transformer import ETLTransformer
from src.domain.transform.transformers.transformation_pipeline import (
    TransformationPipeline,
    PipelineConfig,
    PipelineMode,
)

from src.domain.validation.rules.base_rules import (
    DataQualityValidator,
    ValidationLevel,
    ValidationSeverity,
)


class TestClinVarParser:
    """Test ClinVar XML parser."""

    def setup_method(self):
        self.parser = ClinVarParser()

    def test_parse_sample_clinvar_data(self):
        """Test parsing sample ClinVar data."""
        sample_data = {
            "clinvar_id": "4282399",
            "raw_xml": """<?xml version="1.0" encoding="UTF-8"?>
<ClinVarResult-Set>
<VariationArchive VariationID="702748" VariationName="NM_020822.3(KCNT1):c.335-5C>T">
<RecordStatus>previous</RecordStatus>
<Species>Homo sapiens</Species>
<ClassifiedRecord>
<SimpleAllele AlleleID="695429" VariationID="702748">
<GeneList>
<Gene Symbol="KCNT1" GeneID="57582" FullName="potassium sodium-activated channel subfamily T member 1"/>
</GeneList>
</SimpleAllele>
</ClassifiedRecord>
</VariationArchive>
</ClinVarResult-Set>""",
        }

        result = self.parser.parse_raw_data(sample_data)

        assert result is not None
        assert isinstance(result, ClinVarVariant)
        assert result.clinvar_id == "4282399"
        assert result.gene_symbol == "KCNT1"

    def test_validate_parsed_variant(self):
        """Test validation of parsed variant."""
        variant = ClinVarVariant(
            clinvar_id="4282399",
            variant_id="702748",
            variation_name="NM_020822.3(KCNT1):c.335-5C>T",
            variant_type=ClinVarParser()._parse_variant_type(
                "single nucleotide variant"
            ),
            clinical_significance=ClinVarParser()._parse_clinical_significance(
                "Pathogenic"
            ),
            gene_symbol="KCNT1",
            gene_id="57582",
            gene_name="potassium sodium-activated channel subfamily T member 1",
            chromosome=None,
            start_position=None,
            end_position=None,
            reference_allele=None,
            alternate_allele=None,
            phenotypes=["Seizures"],
            review_status=None,
            last_updated=None,
            raw_xml="<xml>test</xml>",
        )

        errors = self.parser.validate_parsed_data(variant)
        assert len(errors) == 0  # Should be valid


class TestPubMedParser:
    """Test PubMed XML parser."""

    def setup_method(self):
        self.parser = PubMedParser()

    def test_parse_sample_pubmed_data(self):
        """Test parsing sample PubMed data."""
        sample_data = {
            "pubmed_id": "29740699",
            "raw_xml": """<?xml version="1.0"?>
<PubmedArticle>
<MedlineCitation>
<PMID>29740699</PMID>
<Article>
<ArticleTitle>Test Publication Title</ArticleTitle>
<Abstract><AbstractText>Test abstract content.</AbstractText></Abstract>
</Article>
<AuthorList>
<Author><LastName>Smith</LastName><ForeName>John</ForeName></Author>
</AuthorList>
</MedlineCitation>
</PubmedArticle>""",
        }

        result = self.parser.parse_raw_data(sample_data)

        assert result is not None
        assert isinstance(result, PubMedPublication)
        assert result.pubmed_id == "29740699"
        assert result.title == "Test Publication Title"
        assert len(result.authors) == 1

    def test_validate_parsed_publication(self):
        """Test validation of parsed publication."""
        publication = PubMedPublication(
            pubmed_id="29740699",
            title="Valid Title",
            abstract="Valid abstract content.",
            authors=[Mock(last_name="Smith", first_name="John")],
            journal=Mock(title="Test Journal"),
            publication_date=None,
            publication_types=["Journal Article"],
            keywords=["genetics"],
            doi=None,
            pmc_id=None,
            language="eng",
            country="USA",
            raw_xml="<xml>test</xml>",
        )

        errors = self.parser.validate_parsed_data(publication)
        assert len(errors) == 0  # Should be valid


class TestGeneNormalizer:
    """Test gene identifier normalizer."""

    def setup_method(self):
        self.normalizer = GeneNormalizer()

    def test_normalize_clinvar_gene(self):
        """Test normalizing gene from ClinVar."""
        raw_gene = {
            "symbol": "KCNT1",
            "name": "potassium sodium-activated channel subfamily T member 1",
            "id": "57582",
            "source": "clinvar",
        }

        result = self.normalizer.normalize(raw_gene, "clinvar")

        assert result is not None
        assert isinstance(result, NormalizedGene)
        assert result.primary_id == "KCNT1"
        assert result.symbol == "KCNT1"
        assert result.source == "clinvar"

    def test_validate_gene_symbol(self):
        """Test gene symbol validation."""
        gene = NormalizedGene(
            primary_id="KCNT1",
            id_type=GeneIdentifierType.SYMBOL,
            symbol="KCNT1",
            name="potassium sodium-activated channel subfamily T member 1",
            synonyms=[],
            cross_references={},
            source="clinvar",
            confidence_score=0.9,
        )

        errors = self.normalizer.validate_normalized_gene(gene)
        assert len(errors) == 0  # Should be valid


class TestVariantNormalizer:
    """Test variant identifier normalizer."""

    def setup_method(self):
        self.normalizer = VariantNormalizer()

    def test_normalize_clinvar_variant(self):
        """Test normalizing variant from ClinVar."""
        raw_variant = {
            "clinvar_id": "4282399",
            "variant_id": "702748",
            "variation_name": "NM_020822.3(KCNT1):c.335-5C>T",
            "chromosome": "9",
            "start_position": 1000000,
            "reference_allele": "C",
            "alternate_allele": "T",
            "clinical_significance": "Pathogenic",
            "source": "clinvar",
        }

        result = self.normalizer.normalize(raw_variant, "clinvar")

        assert result is not None
        assert isinstance(result, NormalizedVariant)
        assert result.primary_id == "4282399"
        assert result.genomic_location is not None
        assert result.genomic_location.chromosome == "9"

    def test_validate_variant(self):
        """Test variant validation."""
        variant = NormalizedVariant(
            primary_id="4282399",
            id_type=self.normalizer._identify_variant_type("4282399"),
            genomic_location=Mock(
                chromosome="9",
                position=1000000,
                reference_allele="C",
                alternate_allele="T",
            ),
            hgvs_notations={"c": "c.335-5C>T"},
            clinical_significance="Pathogenic",
            gene_symbol="KCNT1",
            cross_references={},
            source="clinvar",
            confidence_score=0.9,
        )

        errors = self.normalizer.validate_normalized_variant(variant)
        assert len(errors) == 0  # Should be valid


class TestGeneVariantMapper:
    """Test gene-variant relationship mapping."""

    def setup_method(self):
        self.mapper = GeneVariantMapper()

    def test_map_gene_variant_relationship(self):
        """Test mapping gene-variant relationships."""
        # Create mock gene and variant
        gene = Mock()
        gene.primary_id = "KCNT1"

        variant = Mock()
        variant.primary_id = "4282399"
        variant.genomic_location = Mock(chromosome="9", position=1000000)

        # Add gene coordinates
        self.mapper.add_gene_coordinates("KCNT1", "9", 999000, 1001000)

        link = self.mapper.map_gene_variant_relationship(gene, variant)

        assert link is not None
        assert isinstance(link, GeneVariantLink)
        assert link.gene_id == "KCNT1"
        assert link.variant_id == "4282399"

    def test_validate_mapping(self):
        """Test validation of gene-variant mappings."""
        link = GeneVariantLink(
            gene_id="KCNT1",
            variant_id="4282399",
            relationship_type=self.mapper._determine_relationship_type(
                999000, 1001000, 1000000, Mock()
            ),
            confidence_score=0.8,
            evidence_sources=["clinvar"],
            genomic_distance=0,
            functional_impact=None,
        )

        errors = self.mapper.validate_mapping(link)
        assert len(errors) == 0  # Should be valid


class TestDataQualityValidator:
    """Test data quality validation."""

    def setup_method(self):
        self.validator = DataQualityValidator(ValidationLevel.STANDARD)

    def test_validate_gene_entity(self):
        """Test validating gene entity."""
        gene_data = {"symbol": "KCNT1", "confidence_score": 0.9}

        result = self.validator.validate_entity("gene", gene_data)

        assert result.is_valid
        assert result.score > 0.8
        assert len(result.issues) == 0

    def test_validate_invalid_gene(self):
        """Test validating invalid gene entity."""
        gene_data = {
            "symbol": "invalid_symbol_with_spaces and special chars!",
            "confidence_score": 1.5,  # Invalid range
        }

        result = self.validator.validate_entity("gene", gene_data)

        assert not result.is_valid
        assert len(result.issues) > 0
        assert any(
            issue.severity == ValidationSeverity.ERROR for issue in result.issues
        )

    def test_validate_variant_entity(self):
        """Test validating variant entity."""
        variant_data = {
            "chromosome": "9",
            "position": 1000000,
            "reference_allele": "C",
            "alternate_allele": "T",
        }

        result = self.validator.validate_entity("variant", variant_data)

        assert result.is_valid
        assert len(result.issues) == 0

    def test_validate_publication_entity(self):
        """Test validating publication entity."""
        pub_data = {
            "pubmed_id": "29740699",
            "title": "Valid publication title with sufficient length",
            "authors": ["Author 1", "Author 2"],
        }

        result = self.validator.validate_entity("publication", pub_data)

        assert result.is_valid
        assert len(result.issues) == 0


class TestETLTransformer:
    """Test ETL transformation orchestrator."""

    def setup_method(self):
        self.transformer = ETLTransformer()

    @patch(
        "src.domain.transform.transformers.etl_transformer.ETLTransformer._parse_all_sources"
    )
    @patch(
        "src.domain.transform.transformers.etl_transformer.ETLTransformer._normalize_all_entities"
    )
    @patch(
        "src.domain.transform.transformers.etl_transformer.ETLTransformer._create_cross_references"
    )
    @patch(
        "src.domain.transform.transformers.etl_transformer.ETLTransformer._validate_transformed_data"
    )
    @patch(
        "src.domain.transform.transformers.etl_transformer.ETLTransformer._export_transformed_data"
    )
    async def test_transform_all_sources(
        self, mock_export, mock_validate, mock_cross_ref, mock_normalize, mock_parse
    ):
        """Test full ETL transformation pipeline."""
        # Setup mocks
        mock_parse.return_value = {
            "clinvar": [],
            "pubmed": [],
            "hpo": [],
            "uniprot": [],
        }
        mock_normalize.return_value = {
            "genes": [],
            "variants": [],
            "phenotypes": [],
            "publications": [],
        }
        mock_cross_ref.return_value = {
            "gene_variant_links": [],
            "variant_phenotype_links": [],
        }
        mock_validate.return_value = {"passed": 0, "failed": 0, "errors": []}
        mock_export.return_value = {"files_created": [], "errors": []}

        raw_data = {
            "clinvar": [{"clinvar_id": "test"}],
            "pubmed": [{"pubmed_id": "test"}],
        }

        result = await self.transformer.transform_all_sources(raw_data)

        assert "parsed" in result
        assert "normalized" in result
        assert "mapped" in result
        assert "validation" in result
        assert "export" in result
        assert "metadata" in result

        # Verify all methods were called
        mock_parse.assert_called_once()
        mock_normalize.assert_called_once()
        mock_cross_ref.assert_called_once()
        mock_validate.assert_called_once()
        mock_export.assert_called_once()


class TestTransformationPipeline:
    """Test transformation pipeline orchestrator."""

    def setup_method(self):
        self.pipeline = TransformationPipeline()

    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        assert self.pipeline.config is not None
        assert not self.pipeline.is_running
        assert self.pipeline.current_progress == 0.0

    @pytest.mark.asyncio
    async def test_pipeline_config_validation(self):
        """Test pipeline configuration validation."""
        # Valid config should pass
        config = PipelineConfig(max_concurrent_sources=2, batch_size=100)
        pipeline = TransformationPipeline(config)

        # Test with invalid config
        config = PipelineConfig(max_concurrent_sources=0)
        pipeline = TransformationPipeline(config)

        errors = await pipeline.validate_pipeline_config()
        assert len(errors) > 0  # Should have validation errors

    def test_get_pipeline_status(self):
        """Test getting pipeline status."""
        status = self.pipeline.get_pipeline_status()

        assert "is_running" in status
        assert "current_progress" in status
        assert "config" in status
        assert "transformer_status" in status


# Integration tests for end-to-end transformation


class TestTransformationIntegration:
    """Integration tests for transformation pipeline."""

    def setup_method(self):
        self.pipeline = TransformationPipeline(
            PipelineConfig(
                mode=PipelineMode.SEQUENTIAL,
                enable_validation=False,  # Skip for faster testing
            )
        )

    async def test_end_to_end_transformation(self):
        """Test end-to-end transformation with sample data."""
        # Create sample raw data
        raw_data = {
            "clinvar": [
                {
                    "clinvar_id": "TEST123",
                    "raw_xml": """<?xml version="1.0"?>
<ClinVarResult-Set>
<VariationArchive VariationID="123" VariationName="TEST:c.100A>G">
<Species>Homo sapiens</Species>
<ClassifiedRecord>
<SimpleAllele VariationID="123">
<GeneList>
<Gene Symbol="TESTGENE" GeneID="12345"/>
</GeneList>
</SimpleAllele>
</ClassifiedRecord>
</VariationArchive>
</ClinVarResult-Set>""",
                }
            ],
            "pubmed": [
                {
                    "pubmed_id": "12345678",
                    "raw_xml": """<?xml version="1.0"?>
<PubmedArticle>
<MedlineCitation>
<PMID>12345678</PMID>
<Article>
<ArticleTitle>Test Publication</ArticleTitle>
<Abstract><AbstractText>Test abstract.</AbstractText></Abstract>
</Article>
<AuthorList>
<Author><LastName>Test</LastName><ForeName>Author</ForeName></Author>
</AuthorList>
</MedlineCitation>
</PubmedArticle>""",
                }
            ],
            "hpo": [
                {
                    "hpo_id": "HP:0000001",
                    "name": "Test phenotype",
                    "definition": "A test phenotype.",
                    "format": "sample",
                }
            ],
            "uniprot": [
                {
                    "primaryAccession": "P12345",
                    "uniProtkbId": "TEST_HUMAN",
                    "proteinDescription": {
                        "recommendedName": {"fullName": {"value": "Test protein"}}
                    },
                    "genes": [{"geneName": {"value": "TESTGENE"}}],
                    "organism": {"scientificName": "Homo sapiens", "taxonId": "9606"},
                    "sequence": {"length": 100, "mass": 11000},
                }
            ],
        }

        result = await self.pipeline.execute_pipeline(raw_data)

        assert result.success
        assert "transformed_data" in result
        assert "execution_time" in result

        # Check that transformation produced results
        transformed = result.transformed_data
        assert "parsed" in transformed
        assert "metadata" in transformed
