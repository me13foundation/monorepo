"""
Tests for Bulk Export Service with type safety patterns.

Follows type safety examples from type_examples.md:
- Uses typed test fixtures
- Implements mock repository patterns
- Validates API responses with type safety
"""

import gzip
import json
import pytest
from unittest.mock import Mock

from src.application.export.export_service import (
    BulkExportService,
    ExportFormat,
    CompressionFormat,
)
from tests.test_types.fixtures import (
    TEST_GENE_MED13,
    TEST_GENE_TP53,
    TEST_VARIANT_PATHOGENIC,
    TEST_PHENOTYPE_AUTISM as TEST_PHENOTYPE_NEUROLOGICAL,
    TEST_EVIDENCE_PATHOGENIC as TEST_EVIDENCE_CLINICAL_REPORT,
)


class TestBulkExportService:
    """Test suite for BulkExportService with comprehensive type safety."""

    @pytest.fixture
    def mock_gene_service(self) -> Mock:
        """Create mock gene service for testing."""
        service = Mock()
        # Mock the list_genes method to return test data
        service.list_genes.return_value = ([TEST_GENE_MED13, TEST_GENE_TP53], 2)
        return service

    @pytest.fixture
    def mock_variant_service(self) -> Mock:
        """Create mock variant service for testing."""
        service = Mock()
        service.list_variants.return_value = ([TEST_VARIANT_PATHOGENIC], 1)
        return service

    @pytest.fixture
    def mock_phenotype_service(self) -> Mock:
        """Create mock phenotype service for testing."""
        service = Mock()
        service.list_phenotypes.return_value = ([TEST_PHENOTYPE_NEUROLOGICAL], 1)
        return service

    @pytest.fixture
    def mock_evidence_service(self) -> Mock:
        """Create mock evidence service for testing."""
        service = Mock()
        service.list_evidence.return_value = ([TEST_EVIDENCE_CLINICAL_REPORT], 1)
        return service

    @pytest.fixture
    def export_service(
        self,
        mock_gene_service: Mock,
        mock_variant_service: Mock,
        mock_phenotype_service: Mock,
        mock_evidence_service: Mock,
    ) -> BulkExportService:
        """Create export service with typed mock dependencies."""
        return BulkExportService(
            gene_service=mock_gene_service,
            variant_service=mock_variant_service,
            phenotype_service=mock_phenotype_service,
            evidence_service=mock_evidence_service,
        )

    def test_export_genes_json_format(self, export_service: BulkExportService) -> None:
        """Test exporting genes in JSON format with type safety."""
        # Act: Export genes as JSON
        result = list(
            export_service.export_data(
                entity_type="genes",
                export_format=ExportFormat.JSON,
                compression=CompressionFormat.NONE,
            )
        )

        # Assert: Verify result structure and types
        assert len(result) == 1
        assert isinstance(result[0], str)

        # Parse JSON and validate structure
        data = json.loads(result[0])
        assert "genes" in data
        assert isinstance(data["genes"], list)
        assert len(data["genes"]) == 2  # MED13 and TP53

        # Validate typed structure
        for gene_data in data["genes"]:
            assert "gene_id" in gene_data
            assert "symbol" in gene_data
            assert "name" in gene_data
            assert "gene_type" in gene_data

    def test_export_variants_csv_format(
        self, export_service: BulkExportService
    ) -> None:
        """Test exporting variants in CSV format with type safety."""
        # Act: Export variants as CSV
        result = list(
            export_service.export_data(
                entity_type="variants",
                export_format=ExportFormat.CSV,
                compression=CompressionFormat.NONE,
            )
        )

        # Assert: Verify CSV structure
        assert len(result) == 1
        assert isinstance(result[0], str)

        # Parse CSV and validate
        lines = result[0].strip().split("\n")
        assert len(lines) >= 2  # Header + data

        # Check header
        header = lines[0].split(",")
        expected_fields = [
            "id",
            "variant_id",
            "clinvar_id",
            "chromosome",
            "position",
            "reference_allele",
            "alternate_allele",
            "variant_type",
            "clinical_significance",
            "gene_symbol",
        ]
        for field in expected_fields:
            assert field in header

    def test_export_phenotypes_compressed_json(
        self, export_service: BulkExportService
    ) -> None:
        """Test exporting phenotypes with gzip compression."""
        # Act: Export phenotypes as compressed JSON
        result = list(
            export_service.export_data(
                entity_type="phenotypes",
                export_format=ExportFormat.JSON,
                compression=CompressionFormat.GZIP,
            )
        )

        # Assert: Verify compression
        assert len(result) == 1
        assert isinstance(result[0], bytes)

        # Decompress and validate
        decompressed = gzip.decompress(result[0]).decode("utf-8")
        data = json.loads(decompressed)
        assert "phenotypes" in data
        assert isinstance(data["phenotypes"], list)

    def test_export_evidence_jsonl_format(
        self, export_service: BulkExportService
    ) -> None:
        """Test exporting evidence in JSON Lines format."""
        # Act: Export evidence as JSONL
        result = list(
            export_service.export_data(
                entity_type="evidence",
                export_format=ExportFormat.JSONL,
                compression=CompressionFormat.NONE,
            )
        )

        # Assert: Verify JSONL structure
        assert len(result) == 1
        assert isinstance(result[0], str)

        # Parse JSONL (one JSON object per line)
        lines = result[0].strip().split("\n")
        assert len(lines) >= 1

        # Validate each line is valid JSON
        for line in lines:
            if line.strip():  # Skip empty lines
                data = json.loads(line)
                assert isinstance(data, dict)
                # Evidence objects should have basic fields like description
                assert "description" in data or "value" in data

    def test_export_with_filters(self, export_service: BulkExportService) -> None:
        """Test export functionality with filters applied."""
        # Note: Current implementation doesn't support filtering in export
        # This test verifies the export still works when filters are passed
        # Act: Export with filters (limit)
        result = list(
            export_service.export_data(
                entity_type="genes",
                export_format=ExportFormat.JSON,
                compression=CompressionFormat.NONE,
                filters={"limit": 1},  # Filters are passed but not currently used
            )
        )

        # Assert: Verify export still works (returns all data since filtering not implemented)
        assert len(result) == 1
        data = json.loads(result[0])
        assert "genes" in data
        assert len(data["genes"]) == 2  # Returns all mock data

    def test_invalid_entity_type_raises_error(
        self, export_service: BulkExportService
    ) -> None:
        """Test that invalid entity types raise appropriate errors."""
        # Act & Assert: Invalid entity type should raise ValueError
        with pytest.raises(ValueError, match="Unsupported entity type"):
            list(
                export_service.export_data(
                    entity_type="invalid_entity",
                    export_format=ExportFormat.JSON,
                    compression=CompressionFormat.NONE,
                )
            )

    def test_get_export_info_returns_typed_structure(
        self, export_service: BulkExportService
    ) -> None:
        """Test get_export_info returns properly typed structure."""
        # Act: Get export info for genes
        info = export_service.get_export_info("genes")

        # Assert: Verify structure and types
        assert isinstance(info, dict)
        assert "entity_type" in info
        assert "supported_formats" in info
        assert "supported_compression" in info

        assert info["entity_type"] == "genes"
        assert isinstance(info["supported_formats"], list)
        assert isinstance(info["supported_compression"], list)

        # Verify enum values are converted to strings
        assert ExportFormat.JSON.value in info["supported_formats"]
        assert CompressionFormat.GZIP.value in info["supported_compression"]

    def test_export_format_enum_values(self) -> None:
        """Test that export format enums have correct values."""
        # Assert: Verify enum values match expected strings
        assert ExportFormat.JSON.value == "json"
        assert ExportFormat.CSV.value == "csv"
        assert ExportFormat.TSV.value == "tsv"
        assert ExportFormat.JSONL.value == "jsonl"

    def test_compression_format_enum_values(self) -> None:
        """Test that compression format enums have correct values."""
        # Assert: Verify enum values match expected strings
        assert CompressionFormat.NONE.value == "none"
        assert CompressionFormat.GZIP.value == "gzip"

    def test_csv_field_mappings_are_correct(
        self, export_service: BulkExportService
    ) -> None:
        """Test that CSV field mappings include all expected fields."""
        # Test gene fields
        gene_fields = export_service._get_gene_fields()
        expected_gene_fields = [
            "id",
            "gene_id",
            "symbol",
            "name",
            "description",
            "gene_type",
            "chromosome",
            "start_position",
            "end_position",
            "ensembl_id",
            "ncbi_gene_id",
            "uniprot_id",
            "created_at",
            "updated_at",
        ]
        assert gene_fields == expected_gene_fields

        # Test variant fields
        variant_fields = export_service._get_variant_fields()
        expected_variant_fields = [
            "id",
            "variant_id",
            "clinvar_id",
            "chromosome",
            "position",
            "reference_allele",
            "alternate_allele",
            "variant_type",
            "clinical_significance",
            "gene_symbol",
            "hgvs_genomic",
            "hgvs_cdna",
            "hgvs_protein",
            "condition",
            "review_status",
            "allele_frequency",
            "gnomad_af",
            "created_at",
            "updated_at",
        ]
        assert variant_fields == expected_variant_fields

    def test_serialization_handles_complex_objects(
        self, export_service: BulkExportService
    ) -> None:
        """Test that serialization handles complex nested objects correctly."""
        # Create a mock object with nested structure
        complex_obj = {
            "id": 1,
            "name": "Test Object",
            "metadata": {"nested": {"value": 42, "list": [1, 2, 3]}},
            "tags": ["tag1", "tag2"],
        }

        # Act: Serialize the object
        serialized = export_service._serialize_item(complex_obj)

        # Assert: Verify nested structure is preserved
        assert serialized["id"] == 1
        assert serialized["name"] == "Test Object"
        assert serialized["metadata"]["nested"]["value"] == 42
        assert serialized["metadata"]["nested"]["list"] == [1, 2, 3]
        assert serialized["tags"] == ["tag1", "tag2"]

    def test_csv_row_conversion_handles_missing_fields(
        self, export_service: BulkExportService
    ) -> None:
        """Test CSV row conversion handles missing fields gracefully."""
        # Create object missing some fields
        incomplete_obj = {"id": 1, "name": "Test"}

        # Act: Convert to CSV row
        row = export_service._item_to_csv_row(
            incomplete_obj, ["id", "name", "missing_field"]
        )

        # Assert: Missing fields become empty strings
        assert row["id"] == "1"
        assert row["name"] == "Test"
        assert row["missing_field"] == ""

    def test_csv_row_conversion_handles_complex_types(
        self, export_service: BulkExportService
    ) -> None:
        """Test CSV row conversion properly handles lists and None values."""
        # Create object with complex types
        complex_obj = {
            "id": 1,
            "tags": ["tag1", "tag2"],
            "optional_field": None,
            "number": 42,
        }

        # Act: Convert to CSV row
        row = export_service._item_to_csv_row(
            complex_obj, ["id", "tags", "optional_field", "number"]
        )

        # Assert: Complex types are converted appropriately
        assert row["id"] == "1"
        assert row["tags"] == "tag1;tag2"  # List joined with semicolons
        assert row["optional_field"] == ""  # None becomes empty string
        assert row["number"] == "42"  # Number converted to string
