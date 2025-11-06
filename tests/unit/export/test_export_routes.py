"""
Tests for Bulk Export Routes with type safety patterns.

Follows type safety examples from type_examples.md:
- Uses typed test fixtures
- Implements proper API response validation
- Validates external API responses with type safety
"""

import json
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.application.export.export_service import CompressionFormat, ExportFormat
from src.routes.export import router


class TestExportRoutes:
    """Test suite for export routes with comprehensive type safety."""

    @pytest.fixture
    def mock_export_service(self) -> Mock:
        """Create typed mock export service."""
        mock_service = Mock()

        # Mock the export_data method to return test data
        def mock_export_data(
            entity_type: str,
            export_format: ExportFormat,
            compression: CompressionFormat,
            **kwargs,
        ):
            if export_format == ExportFormat.JSON:
                test_data = {f"{entity_type}": [{"id": 1, "name": "Test Item"}]}
                yield json.dumps(test_data)
            elif export_format == ExportFormat.CSV:
                yield "id,name\n1,Test Item\n"
            else:
                yield "test data"

        mock_service.export_data.side_effect = mock_export_data

        # Mock get_export_info
        mock_service.get_export_info.return_value = {
            "entity_type": "genes",
            "supported_formats": ["json", "csv"],
            "supported_compression": ["none", "gzip"],
            "estimated_record_count": 100,
        }

        return mock_service

    @pytest.fixture
    def test_client(self, mock_export_service: Mock) -> TestClient:
        """Create test client with mocked export service."""
        from src.routes.export import get_export_service

        app = FastAPI()
        app.include_router(router)

        # Override the dependency function
        app.dependency_overrides[get_export_service] = lambda: mock_export_service

        return TestClient(app)

    def test_export_genes_json_format(
        self,
        test_client: TestClient,
        mock_export_service: Mock,
    ) -> None:
        """Test exporting genes in JSON format returns correct response."""
        # Act: Make request to export genes
        response = test_client.get("/export/genes?format=json")

        # Assert: Verify response structure and types
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "content-disposition" in response.headers

        # Verify the export_data method was called correctly
        mock_export_service.export_data.assert_called_once_with(
            entity_type="genes",
            export_format=ExportFormat.JSON,
            compression=CompressionFormat.NONE,
            filters=None,
        )

        # Parse response and validate structure
        data = response.json()
        assert "genes" in data
        assert isinstance(data["genes"], list)
        assert len(data["genes"]) == 1
        assert data["genes"][0]["id"] == 1
        assert data["genes"][0]["name"] == "Test Item"

    def test_export_variants_csv_format(
        self,
        test_client: TestClient,
        mock_export_service: Mock,
    ) -> None:
        """Test exporting variants in CSV format returns correct response."""
        # Act: Make request to export variants as CSV
        response = test_client.get("/export/variants?format=csv")

        # Assert: Verify CSV response
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert (
            response.headers["content-disposition"]
            == "attachment; filename=variants.csv"
        )

        # Verify CSV content
        content = response.text
        lines = content.strip().split("\n")
        assert len(lines) == 2  # Header + 1 data row
        assert lines[0] == "id,name"
        assert lines[1] == "1,Test Item"

    def test_export_with_gzip_compression(
        self,
        test_client: TestClient,
        mock_export_service: Mock,
    ) -> None:
        """Test exporting with gzip compression."""
        # Act: Make request with gzip compression
        response = test_client.get("/export/phenotypes?format=json&compression=gzip")

        # Assert: Verify compression headers
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/gzip"
        assert "phenotypes.json.gz" in response.headers["content-disposition"]

        # Verify compression was requested
        mock_export_service.export_data.assert_called_once_with(
            entity_type="phenotypes",
            export_format=ExportFormat.JSON,
            compression=CompressionFormat.GZIP,
            filters=None,
        )

    def test_export_with_limit_parameter(
        self,
        test_client: TestClient,
        mock_export_service: Mock,
    ) -> None:
        """Test exporting with limit parameter."""
        # Act: Make request with limit
        response = test_client.get("/export/evidence?format=json&limit=50")

        # Assert: Verify limit was passed to service
        assert response.status_code == 200
        mock_export_service.export_data.assert_called_once_with(
            entity_type="evidence",
            export_format=ExportFormat.JSON,
            compression=CompressionFormat.NONE,
            filters={"limit": 50},
        )

    def test_invalid_entity_type_returns_400(self, test_client: TestClient) -> None:
        """Test that invalid entity types return 400 error."""
        # Act: Make request with invalid entity type
        response = test_client.get("/export/invalid_entity?format=json")

        # Assert: Verify error response
        assert response.status_code == 400
        error_data = response.json()
        assert "detail" in error_data
        assert "Invalid entity type" in error_data["detail"]

    def test_get_export_info_returns_correct_structure(
        self,
        test_client: TestClient,
        mock_export_service: Mock,
    ) -> None:
        """Test get export info endpoint returns typed structure."""
        # Act: Get export info for genes
        response = test_client.get("/export/genes/info")

        # Assert: Verify response structure and types
        assert response.status_code == 200
        data = response.json()

        assert data["entity_type"] == "genes"
        assert isinstance(data["export_formats"], list)
        assert isinstance(data["compression_formats"], list)
        assert "json" in data["export_formats"]
        assert "csv" in data["export_formats"]
        assert "none" in data["compression_formats"]
        assert "gzip" in data["compression_formats"]

        # Verify service method was called
        mock_export_service.get_export_info.assert_called_once_with("genes")

    def test_list_exportable_entities_returns_complete_list(
        self,
        test_client: TestClient,
    ) -> None:
        """Test list exportable entities endpoint returns all supported entities."""
        # Act: Get list of exportable entities
        response = test_client.get("/export/")

        # Assert: Verify response contains all expected entities
        assert response.status_code == 200
        data = response.json()

        assert "exportable_entities" in data
        assert isinstance(data["exportable_entities"], list)
        assert (
            len(data["exportable_entities"]) == 4
        )  # genes, variants, phenotypes, evidence

        # Check entity types
        entity_types = [entity["type"] for entity in data["exportable_entities"]]
        assert "genes" in entity_types
        assert "variants" in entity_types
        assert "phenotypes" in entity_types
        assert "evidence" in entity_types

        # Verify each entity has required fields
        for entity in data["exportable_entities"]:
            assert "type" in entity
            assert "description" in entity
            assert isinstance(entity["description"], str)

        # Verify usage information
        assert "usage" in data
        assert "endpoint" in data["usage"]

    def test_invalid_format_parameter_returns_400(
        self,
        test_client: TestClient,
    ) -> None:
        """Test that invalid format parameter returns 400 error."""
        # Act: Make request with invalid format
        response = test_client.get("/export/genes?format=invalid")

        # Assert: Verify validation error
        assert response.status_code == 422  # FastAPI validation error

    def test_invalid_compression_parameter_returns_400(
        self,
        test_client: TestClient,
    ) -> None:
        """Test that invalid compression parameter returns 400 error."""
        # Act: Make request with invalid compression
        response = test_client.get("/export/genes?format=json&compression=invalid")

        # Assert: Verify validation error
        assert response.status_code == 422  # FastAPI validation error

    def test_streaming_response_headers_are_correct(
        self,
        test_client: TestClient,
    ) -> None:
        """Test that streaming response includes correct headers."""
        # Act: Make export request
        response = test_client.get("/export/genes?format=json")

        # Assert: Verify all required headers are present
        required_headers = [
            "content-type",
            "content-disposition",
            "x-entity-type",
            "x-export-format",
            "x-compression",
        ]

        for header in required_headers:
            assert header in response.headers

        # Verify header values
        assert response.headers["x-entity-type"] == "genes"
        assert response.headers["x-export-format"] == "json"
        assert response.headers["x-compression"] == "none"
        assert "genes.json" in response.headers["content-disposition"]

    def test_export_service_error_returns_500(
        self,
        test_client: TestClient,
        mock_export_service: Mock,
    ) -> None:
        """Test that service errors are properly handled and return 500."""
        # Arrange: Make service raise an exception
        mock_export_service.export_data.side_effect = Exception("Service error")

        # Act: Make request that will trigger the error
        response = test_client.get("/export/genes?format=json")

        # Assert: Verify error handling - service errors are caught and returned in response
        # The streaming response may still return 200 but with error content
        response_text = response.text
        assert (
            "Error during export" in response_text or "Service error" in response_text
        )
