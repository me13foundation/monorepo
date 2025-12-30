from __future__ import annotations

"""
Additional comprehensive tests for BulkExportService.

Tests cover critical business logic that was previously untested,
including serialization methods, pagination, error handling, and edge cases.
"""

import csv
import gzip
import io
import json
from typing import TYPE_CHECKING, NamedTuple
from unittest.mock import Mock, call

import pytest

from src.application.export.export_service import BulkExportService
from src.application.export.export_types import CompressionFormat, ExportFormat
from src.application.export.serialization import (
    coerce_scalar,
    item_to_csv_row,
    resolve_nested_value,
    serialize_item,
)
from src.application.export.utils import (
    collect_paginated,
    copy_filters,
    get_evidence_fields,
    get_gene_fields,
    get_phenotype_fields,
    get_variants_fields,
)

if TYPE_CHECKING:
    from src.type_definitions.common import QueryFilters


class TestBulkExportServiceAdditional:
    """Additional comprehensive tests for uncovered business logic."""

    @pytest.fixture
    def mock_services(self) -> tuple[Mock, Mock, Mock, Mock]:
        """Create mock services for testing."""
        gene_service = Mock()
        variant_service = Mock()
        phenotype_service = Mock()
        evidence_service = Mock()

        return gene_service, variant_service, phenotype_service, evidence_service

    @pytest.fixture
    def export_service(
        self,
        mock_services: tuple[Mock, Mock, Mock, Mock],
    ) -> BulkExportService:
        """Create export service with mock dependencies."""
        (
            gene_service,
            variant_service,
            phenotype_service,
            evidence_service,
        ) = mock_services

        gene_service.list_genes.return_value = (
            [
                {
                    "id": "gene-1",
                    "gene_id": "GENE1",
                    "symbol": "MED13",
                    "name": "Mediator Complex Subunit 13",
                    "description": "Test gene",
                    "gene_type": "protein_coding",
                    "chromosome": "17",
                    "start_position": 100,
                    "end_position": 200,
                    "ensembl_id": "ENSG000000",
                    "ncbi_gene_id": 1234,
                    "uniprot_id": "Q99999",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-02T00:00:00Z",
                },
            ],
            1,
        )

        variant_service.list_variants.return_value = (
            [
                {
                    "id": "variant-1",
                    "variant_id": "VAR1",
                    "clinvar_id": "CLN1",
                    "chromosome": "17",
                    "position": 101,
                    "reference_allele": "A",
                    "alternate_allele": "T",
                    "variant_type": "SNV",
                    "clinical_significance": "pathogenic",
                    "gene_symbol": "MED13",
                    "hgvs_genomic": "g.101A>T",
                    "hgvs_cdna": "c.101A>T",
                    "hgvs_protein": "p.Lys34Asn",
                    "condition": "Test condition",
                    "review_status": "criteria_provided",
                    "allele_frequency": 0.01,
                    "gnomad_af": 0.005,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-02T00:00:00Z",
                },
            ],
            1,
        )

        phenotype_service.list_phenotypes.return_value = (
            [
                {
                    "id": "phenotype-1",
                    "identifier": {"hpo_id": "HP:0000001", "hpo_term": "Phenotype"},
                    "name": "Phenotype Name",
                    "definition": "Test definition",
                    "category": "Neurological",
                    "parent_hpo_id": None,
                    "is_root_term": False,
                    "frequency_in_med13": "frequent",
                    "severity_score": 3,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-02T00:00:00Z",
                },
            ],
            1,
        )

        evidence_service.list_evidence.return_value = (
            [
                {
                    "id": "evidence-1",
                    "variant_id": "variant-1",
                    "phenotype_id": "phenotype-1",
                    "description": "Evidence description",
                    "summary": "Evidence summary",
                    "evidence_level": "strong",
                    "evidence_type": "clinical",
                    "confidence": {"score": 0.9},
                    "quality_score": 5,
                    "sample_size": 10,
                    "study_type": "Case Study",
                    "statistical_significance": "p<0.05",
                    "reviewed": True,
                    "review_date": "2024-01-02",
                    "reviewer_notes": "Reviewed",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-02T00:00:00Z",
                },
            ],
            1,
        )

        return BulkExportService(
            gene_service=gene_service,
            variant_service=variant_service,
            phenotype_service=phenotype_service,
            evidence_service=evidence_service,
        )

    class TestCollectPaginated:
        """Test pagination collection logic."""

        def test_collect_paginated_single_page(
            self,
            export_service: BulkExportService,
        ) -> None:
            """Test collecting data that fits in a single page."""
            mock_fetcher = Mock()
            mock_fetcher.side_effect = [
                (["item1", "item2"], 2),  # page 1: 2 items total
            ]

            result = collect_paginated(mock_fetcher, chunk_size=10)

            assert result == ["item1", "item2"]
            mock_fetcher.assert_called_once_with(1, 10)

        def test_collect_paginated_multiple_pages(
            self,
            export_service: BulkExportService,
        ) -> None:
            """Test collecting data across multiple pages."""
            mock_fetcher = Mock()
            mock_fetcher.side_effect = [
                (["item1", "item2"], 5),  # page 1: 2 items, total 5
                (["item3", "item4"], 5),  # page 2: 2 items, total 5
                (["item5"], 5),  # page 3: 1 item, total 5
            ]
            result = collect_paginated(mock_fetcher, chunk_size=2)

            assert result == ["item1", "item2", "item3", "item4", "item5"]
            assert mock_fetcher.call_count == 3
            mock_fetcher.assert_has_calls(
                [
                    call(1, 2),
                    call(2, 2),
                    call(3, 2),
                ],
            )

        def test_collect_paginated_empty_result(
            self,
            export_service: BulkExportService,
        ) -> None:
            """Test collecting data when no items exist."""
            mock_fetcher = Mock()
            mock_fetcher.return_value = ([], 0)

            result = collect_paginated(mock_fetcher, chunk_size=10)

            assert result == []
            mock_fetcher.assert_called_once_with(1, 10)

        def test_collect_paginated_chunk_size_one(
            self,
            export_service: BulkExportService,
        ) -> None:
            """Test collecting data with chunk size of 1."""
            mock_fetcher = Mock()
            mock_fetcher.side_effect = [
                (["item1"], 3),  # page 1
                (["item2"], 3),  # page 2
                (["item3"], 3),  # page 3
                ([], 3),  # sentinel to terminate
            ]

            result = collect_paginated(mock_fetcher, chunk_size=1)

            assert result == ["item1", "item2", "item3"]
            assert mock_fetcher.call_count == 4

    class TestSerializationMethods:
        """Test object serialization methods."""

        def test_serialize_item_with_dict(
            self,
            export_service: BulkExportService,
        ) -> None:
            """Test serializing a dictionary object."""
            data = {"key": "value", "number": 42}
            result = serialize_item(data)
            assert result == data

        def test_serialize_item_with_pydantic_model(
            self,
            export_service: BulkExportService,
        ) -> None:
            """Test serializing a Pydantic model."""
            from pydantic import BaseModel

            class TestModel(BaseModel):
                name: str
                value: int

            model = TestModel(name="test", value=123)
            result = serialize_item(model)

            assert isinstance(result, dict)
            assert result["name"] == "test"
            assert result["value"] == 123

        def test_serialize_item_with_namedtuple(
            self,
            export_service: BulkExportService,
        ) -> None:
            """Test serializing a namedtuple."""

            class Point(NamedTuple):
                x: int
                y: int

            point = Point(x=10, y=20)

            result = serialize_item(point)

            assert isinstance(result, dict)
            assert result["x"] == 10
            assert result["y"] == 20

        def test_serialize_item_with_custom_object(
            self,
            export_service: BulkExportService,
        ) -> None:
            """Test serializing a custom object with attributes."""

            class CustomObject:
                def __init__(self) -> None:
                    self.attr1 = "value1"
                    self.attr2 = 42
                    self._private = "ignored"

            obj = CustomObject()
            result = serialize_item(obj)

            assert isinstance(result, dict)
            assert result["attr1"] == "value1"
            assert result["attr2"] == 42
            assert "_private" not in result  # Private attributes ignored

        def test_serialize_item_with_list(
            self,
            export_service: BulkExportService,
        ) -> None:
            """Test serializing a list."""
            data = [1, "string", {"key": "value"}]
            result = serialize_item(data)
            assert result == data

        def test_serialize_item_with_primitive(
            self,
            export_service: BulkExportService,
        ) -> None:
            """Test serializing primitive values."""
            assert serialize_item("string") == "string"
            assert serialize_item(42) == 42
            assert serialize_item(item=True) is True
            assert serialize_item(None) is None

        def test_serialize_namedtuple(self, export_service: BulkExportService) -> None:
            """Test namedtuple serialization."""

            class Point(NamedTuple):
                x: float
                y: float

            point = Point(x=10.5, y=20.8)

            result = serialize_item(point)

            assert isinstance(result, dict)
            assert result["x"] == 10.5
            assert result["y"] == 20.8

        def test_serialize_object(self, export_service: BulkExportService) -> None:
            """Test generic object serialization."""

            class TestObject:
                def __init__(self) -> None:
                    self.public_attr = "public"
                    self.number_attr = 123
                    self._private_attr = "private"
                    self.__dunder_attr = "dunder"

            obj = TestObject()
            result = serialize_item(obj)

            assert isinstance(result, dict)
            assert result["public_attr"] == "public"
            assert result["number_attr"] == 123
            assert "_private_attr" not in result  # Private attributes excluded
            assert "__dunder_attr" not in result  # Dunder attributes excluded

        def test_serialize_sequence(self, export_service: BulkExportService) -> None:
            """Test sequence serialization."""
            items = ["string", 42, {"key": "value"}]
            result = serialize_item(items)

            assert isinstance(result, list)
            assert len(result) == 3
            assert result[0] == "string"
            assert result[1] == 42
            assert result[2] == {"key": "value"}

    class TestCSVMethods:
        """Test CSV-related methods."""

        def test_item_to_csv_row_with_dict(
            self,
            export_service: BulkExportService,
        ) -> None:
            """Test CSV row conversion for dictionary items."""
            item = {
                "id": "123",
                "name": "Test Item",
                "value": 42,
                "optional": None,
            }
            field_names = ["id", "name", "value", "optional", "missing"]

            result = item_to_csv_row(item, field_names)

            expected = {
                "id": "123",
                "name": "Test Item",
                "value": "42",
                "optional": "",  # None becomes empty string
                "missing": "",  # Missing field becomes empty string
            }
            assert result == expected

        def test_item_to_csv_row_with_pydantic_model(
            self,
            export_service: BulkExportService,
        ) -> None:
            """Test CSV row conversion for Pydantic models."""
            from pydantic import BaseModel

            class TestModel(BaseModel):
                id: str
                name: str
                count: int

            model = TestModel(id="abc", name="Test", count=5)
            field_names = ["id", "name", "count"]

            result = item_to_csv_row(model, field_names)

            expected = {
                "id": "abc",
                "name": "Test",
                "count": "5",
            }
            assert result == expected

        def test_item_to_csv_row_with_nested_data(
            self,
            export_service: BulkExportService,
        ) -> None:
            """Test CSV row conversion with nested object access."""
            item = {
                "gene": {"symbol": "MED13", "id": "ENSG001"},
                "variant": {"id": "VAR001", "type": "SNV"},
            }
            field_names = ["gene.symbol", "variant.id", "gene.id"]

            result = item_to_csv_row(item, field_names)

            expected = {
                "gene.symbol": "MED13",
                "variant.id": "VAR001",
                "gene.id": "ENSG001",
            }
            assert result == expected

        def test_resolve_nested_value_simple(self) -> None:
            """Test resolving simple nested values."""
            data = {"key": "value"}
            assert resolve_nested_value(data, ["key"]) == "value"

        def test_resolve_nested_value_nested(self) -> None:
            """Test resolving nested object values."""
            data = {"parent": {"child": "value"}}
            assert (
                resolve_nested_value(
                    data,
                    ["parent", "child"],
                )
                == "value"
            )

        def test_resolve_nested_value_deeply_nested(self) -> None:
            """Test resolving deeply nested values."""
            data = {"a": {"b": {"c": {"d": "deep_value"}}}}
            assert (
                resolve_nested_value(
                    data,
                    ["a", "b", "c", "d"],
                )
                == "deep_value"
            )

        def test_resolve_nested_value_missing_key(self) -> None:
            """Test resolving missing keys."""
            data = {"key": "value"}
            assert resolve_nested_value(data, ["missing"]) == ""

        def test_resolve_nested_value_missing_nested_key(self) -> None:
            """Test resolving missing nested keys."""
            data = {"parent": {"child": "value"}}
            assert (
                resolve_nested_value(
                    data,
                    ["parent", "missing"],
                )
                == ""
            )

        def test_resolve_nested_value_non_dict_parent(self) -> None:
            """Test resolving when parent is not a dict."""
            data = {"parent": "not_a_dict"}
            assert (
                resolve_nested_value(
                    data,
                    ["parent", "child"],
                )
                == ""
            )

        def test_resolve_nested_value_none_data(self) -> None:
            """Test resolving with None data."""
            assert resolve_nested_value(None, ["key"]) == ""

        def test_coerce_scalar_values(self) -> None:
            """Test scalar value coercion for CSV."""
            # Already scalar values should pass through
            assert coerce_scalar(value="string") == "string"
            assert coerce_scalar(value=42) == 42
            assert coerce_scalar(value=3.14) == 3.14
            assert coerce_scalar(value=True) is True
            assert coerce_scalar(value=False) is False
            assert coerce_scalar(value=None) is None

            # Complex objects should be converted to strings
            assert coerce_scalar(value={"key": "value"}) == "{'key': 'value'}"
            assert coerce_scalar(value=[1, 2, 3]) == "[1, 2, 3]"

    class TestFieldMappings:
        """Test field mapping methods."""

        def test_get_gene_fields(self) -> None:
            """Test gene field mappings."""
            fields = get_gene_fields()
            expected_fields = [
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
            assert fields == expected_fields

        def test_get_variant_fields(self) -> None:
            """Test variant field mappings."""
            fields = get_variants_fields()
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
            assert fields == expected_fields

        def test_get_phenotype_fields(self) -> None:
            """Test phenotype field mappings."""
            fields = get_phenotype_fields()
            expected_fields = [
                "id",
                "identifier.hpo_id",
                "identifier.hpo_term",
                "name",
                "definition",
                "category",
                "parent_hpo_id",
                "is_root_term",
                "frequency_in_med13",
                "severity_score",
                "created_at",
                "updated_at",
            ]
            assert fields == expected_fields

        def test_get_evidence_fields(self) -> None:
            """Test evidence field mappings."""
            fields = get_evidence_fields()
            expected_fields = [
                "id",
                "variant_id",
                "phenotype_id",
                "description",
                "summary",
                "evidence_level",
                "evidence_type",
                "confidence.score",
                "quality_score",
                "sample_size",
                "study_type",
                "statistical_significance",
                "reviewed",
                "review_date",
                "reviewer_notes",
                "created_at",
                "updated_at",
            ]
            assert fields == expected_fields

    class TestFilterHandling:
        """Test filter handling methods."""

        def test_copy_filters_none(self, export_service: BulkExportService) -> None:
            """Test copying None filters."""
            result = copy_filters(None)
            assert result == {}

        def test_copy_filters_empty(self, export_service: BulkExportService) -> None:
            """Test copying empty filters."""
            filters: QueryFilters = {}
            result = copy_filters(filters)
            assert result == {}
            assert result is not filters  # Should be a copy

        def test_copy_filters_with_data(
            self,
            export_service: BulkExportService,
        ) -> None:
            """Test copying filters with data."""
            filters: QueryFilters = {
                "search": "MED13",
                "limit": 100,
                "offset": 0,
                "sort_by": "symbol",
                "nested": {"key": "value"},
            }
            result = copy_filters(filters)

            assert result == filters
            assert result is not filters  # Should be a new mapping
            assert (
                result["nested"] is filters["nested"]
            )  # clone_query_filters performs a shallow copy

    class TestExportIntegration:
        """Integration tests for export functionality."""

        def test_export_with_gzip_compression(
            self,
            export_service: BulkExportService,
        ) -> None:
            """Test exporting with gzip compression."""
            result = list(
                export_service.export_data(
                    entity_type="genes",
                    export_format=ExportFormat.JSON,
                    compression=CompressionFormat.GZIP,
                ),
            )

            assert len(result) == 1
            # Should be bytes for compressed data
            assert isinstance(result[0], bytes)

            # Decompress and verify
            with gzip.GzipFile(fileobj=io.BytesIO(result[0]), mode="rb") as f:
                decompressed = f.read().decode("utf-8")
                data = json.loads(decompressed)
                assert "genes" in data

        def test_export_jsonl_format(self, export_service: BulkExportService) -> None:
            """Test exporting in JSONL format."""
            result = list(
                export_service.export_data(
                    entity_type="variants",
                    export_format=ExportFormat.JSONL,
                    compression=CompressionFormat.NONE,
                ),
            )

            assert len(result) == 1
            assert isinstance(result[0], str)

            # JSONL should be newline-separated JSON objects
            lines = result[0].strip().split("\n")
            assert len(lines) == 1  # One variant in mock

            # Each line should be valid JSON
            data = json.loads(lines[0])
            assert "id" in data or "variant_id" in data

        def test_export_with_chunking(self, export_service: BulkExportService) -> None:
            """Test that export properly handles chunked data retrieval."""
            # This tests the integration of _collect_paginated with export methods
            gene_service = export_service._gene_service
            gene_service.list_genes.side_effect = [
                (
                    [
                        gene_service.list_genes.return_value[0][0],
                    ],
                    2,
                ),
                (
                    [
                        {
                            "id": "gene-2",
                            "gene_id": "GENE2",
                            "symbol": "MED13L",
                            "name": "Mediator Complex Subunit 13 Like",
                            "description": "Second test gene",
                            "gene_type": "protein_coding",
                            "chromosome": "12",
                            "start_position": 300,
                            "end_position": 450,
                            "ensembl_id": "ENSG000001",
                            "ncbi_gene_id": 5678,
                            "uniprot_id": "Q88888",
                            "created_at": "2024-01-03T00:00:00Z",
                            "updated_at": "2024-01-04T00:00:00Z",
                        },
                    ],
                    2,
                ),
                ([], 2),
            ]

            result = list(
                export_service.export_data(
                    entity_type="genes",
                    export_format=ExportFormat.JSON,
                    chunk_size=1,  # Force small chunks
                ),
            )

            assert len(result) == 1
            data = json.loads(result[0])
            assert "genes" in data
            assert len(data["genes"]) == 2  # Should collect all items

    class TestErrorHandling:
        """Test error handling in export operations."""

        def test_export_invalid_entity_type(
            self,
            export_service: BulkExportService,
        ) -> None:
            """Test error handling for invalid entity types."""
            with pytest.raises(ValueError, match="Unsupported entity type"):
                list(
                    export_service.export_data(
                        entity_type="invalid_type",
                        export_format=ExportFormat.JSON,
                    ),
                )

        def test_export_with_service_error(
            self,
            mock_services: tuple[Mock, Mock, Mock, Mock],
        ) -> None:
            """Test handling of service layer errors."""
            gene_service, _, _, _ = mock_services
            gene_service.list_genes.side_effect = Exception("Service error")

            export_service = BulkExportService(
                gene_service=gene_service,
                variant_service=Mock(),
                phenotype_service=Mock(),
                evidence_service=Mock(),
            )

            with pytest.raises(Exception, match="Service error"):
                list(
                    export_service.export_data(
                        entity_type="genes",
                        export_format=ExportFormat.JSON,
                    ),
                )

    class TestEdgeCases:
        """Test edge cases and boundary conditions."""

        def test_export_empty_dataset(
            self,
            mock_services: tuple[Mock, Mock, Mock, Mock],
        ) -> None:
            """Test exporting when no data is available."""
            gene_service, _, _, _ = mock_services
            gene_service.list_genes.return_value = ([], 0)

            export_service = BulkExportService(
                gene_service=gene_service,
                variant_service=Mock(),
                phenotype_service=Mock(),
                evidence_service=Mock(),
            )

            result = list(
                export_service.export_data(
                    entity_type="genes",
                    export_format=ExportFormat.JSON,
                ),
            )

            assert len(result) == 1
            data = json.loads(result[0])
            assert data["genes"] == []

        def test_csv_export_with_special_characters(
            self,
            export_service: BulkExportService,
        ) -> None:
            """Test CSV export handles special characters properly."""
            export_service._gene_service.list_genes.return_value = (
                [
                    {
                        "id": "gene-special",
                        "gene_id": "GENE-SP",
                        "symbol": "MED13",
                        "name": 'Gene, "Quoted"',
                        "description": "Line\nBreak",
                        "gene_type": "protein_coding",
                        "chromosome": "17",
                        "start_position": 100,
                        "end_position": 200,
                        "ensembl_id": "ENSGSPECIAL",
                        "ncbi_gene_id": 4321,
                        "uniprot_id": "Q77777",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-02T00:00:00Z",
                    },
                ],
                1,
            )

            result = list(
                export_service.export_data(
                    entity_type="genes",
                    export_format=ExportFormat.CSV,
                ),
            )

            assert len(result) == 1
            # Verify it's valid CSV
            csv_reader = csv.reader(io.StringIO(result[0]))
            rows = list(csv_reader)
            assert len(rows) >= 2  # Header + at least one data row
            assert rows[1][3] == 'Gene, "Quoted"'
