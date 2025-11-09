"""
Unit tests for Data Discovery domain entities.

Following type safety patterns from type_examples.md with proper
fixture usage and comprehensive test coverage.
"""

from uuid import uuid4

import pytest

from src.domain.entities.data_discovery_session import (
    QueryParameters,
    QueryParameterType,
    TestResultStatus,
)
from tests.test_types.data_discovery_fixtures import (
    TEST_RESULT_ERROR,
    TEST_RESULT_SUCCESS,
    TEST_SESSION_EMPTY,
    TEST_SOURCE_CLINVAR,
    TEST_SOURCE_HPO,
    TEST_SOURCE_VARIANTFORMER,
    create_test_data_discovery_session,
    create_test_query_test_result,
    create_test_source_catalog_entry,
)


class TestSourceCatalogEntry:
    """Test SourceCatalogEntry domain entity."""

    def test_create_valid_entry(self) -> None:
        """Test creating a valid source catalog entry."""
        entry = create_test_source_catalog_entry()

        assert entry.id == "test-source"
        assert entry.name == "Test Source"
        assert entry.category == "Genomic Variant Databases"
        assert entry.param_type == QueryParameterType.GENE
        assert entry.is_active is True
        assert entry.usage_count == 10
        assert entry.success_rate == 0.85

    def test_is_testable_gene_source(self) -> None:
        """Test that gene sources are testable."""
        assert TEST_SOURCE_CLINVAR.is_testable() is True
        assert TEST_SOURCE_CLINVAR.supports_parameter(QueryParameterType.GENE) is True

    def test_is_testable_term_source(self) -> None:
        """Test that term sources are testable."""
        assert TEST_SOURCE_HPO.is_testable() is True
        assert TEST_SOURCE_HPO.supports_parameter(QueryParameterType.TERM) is True

    def test_is_testable_api_source(self) -> None:
        """Test that API sources are testable."""
        assert TEST_SOURCE_VARIANTFORMER.is_testable() is True
        # API sources support any parameter type (validation happens elsewhere)
        assert (
            TEST_SOURCE_VARIANTFORMER.supports_parameter(QueryParameterType.GENE)
            is True
        )

    def test_supports_parameter_combinations(self) -> None:
        """Test parameter type compatibility."""
        # GeneAndTerm sources support both individual types
        gene_and_term_source = create_test_source_catalog_entry(
            param_type="gene_and_term",
        )

        assert gene_and_term_source.supports_parameter(QueryParameterType.GENE) is True
        assert gene_and_term_source.supports_parameter(QueryParameterType.TERM) is True
        assert (
            gene_and_term_source.supports_parameter(QueryParameterType.GENE_AND_TERM)
            is True
        )

    def test_tags_validation(self) -> None:
        """Test tag validation and normalization."""
        entry = create_test_source_catalog_entry(
            tags=["Test", "MOCK", "duplicate", "duplicate"],
        )

        # Should be lowercase and deduplicated
        assert "test" in entry.tags
        assert "mock" in entry.tags
        assert entry.tags.count("duplicate") == 1  # Only once

    def test_tags_max_limit(self) -> None:
        """Test that too many tags raises an error."""
        with pytest.raises(ValueError, match="Maximum 10 tags allowed"):
            create_test_source_catalog_entry(tags=[f"tag{i}" for i in range(15)])


class TestDataDiscoverySession:
    """Test DataDiscoverySession domain entity."""

    def test_create_valid_session(self) -> None:
        """Test creating a valid data discovery session."""
        session = create_test_data_discovery_session()

        assert isinstance(session.id, type(uuid4()))
        assert isinstance(session.owner_id, type(uuid4()))
        assert session.name == "Test Session"
        assert session.current_parameters.gene_symbol == "MED13L"
        assert session.is_active is True
        assert session.total_tests_run == 0

    def test_update_parameters(self) -> None:
        """Test updating session parameters."""
        session = TEST_SESSION_EMPTY
        new_params = QueryParameters(gene_symbol="TP53", search_term="cancer")

        updated = session.update_parameters(new_params)

        assert updated.current_parameters.gene_symbol == "TP53"
        assert updated.current_parameters.search_term == "cancer"
        assert updated.updated_at > session.updated_at
        assert updated.last_activity_at > session.last_activity_at

    def test_toggle_source_selection(self) -> None:
        """Test toggling source selection."""
        session = TEST_SESSION_EMPTY

        # Select a source
        updated1 = session.toggle_source_selection("clinvar")
        assert "clinvar" in updated1.selected_sources

        # Deselect the same source
        updated2 = updated1.toggle_source_selection("clinvar")
        assert "clinvar" not in updated2.selected_sources

    def test_record_successful_test(self) -> None:
        """Test recording a successful test."""
        session = TEST_SESSION_EMPTY

        updated = session.record_test("clinvar", success=True)

        assert updated.total_tests_run == 1
        assert updated.successful_tests == 1
        assert "clinvar" in updated.tested_sources

    def test_record_failed_test(self) -> None:
        """Test recording a failed test."""
        session = TEST_SESSION_EMPTY

        updated = session.record_test("clinvar", success=False)

        assert updated.total_tests_run == 1
        assert updated.successful_tests == 0
        assert "clinvar" in updated.tested_sources

    def test_get_success_rate(self) -> None:
        """Test calculating success rate."""
        # No tests
        assert TEST_SESSION_EMPTY.get_success_rate() == 0.0

        # All successful
        session = create_test_data_discovery_session(
            total_tests_run=3,
            successful_tests=3,
        )
        assert session.get_success_rate() == 1.0

        # Mixed results
        session = create_test_data_discovery_session(
            total_tests_run=4,
            successful_tests=3,
        )
        assert session.get_success_rate() == 0.75

    def test_source_selection_status(self) -> None:
        """Test source selection status checks."""
        session = create_test_data_discovery_session(
            selected_sources=["clinvar", "hpo"],
            tested_sources=["clinvar"],
        )

        assert session.is_source_selected("clinvar") is True
        assert session.is_source_selected("hpo") is True
        assert session.is_source_selected("omim") is False

        assert session.is_source_tested("clinvar") is True
        assert session.is_source_tested("hpo") is False


class TestQueryParameters:
    """Test QueryParameters value object."""

    def test_has_gene(self) -> None:
        """Test gene symbol presence check."""
        assert QueryParameters(gene_symbol="MED13L").has_gene() is True
        assert QueryParameters().has_gene() is False
        assert QueryParameters(gene_symbol="").has_gene() is False

    def test_has_term(self) -> None:
        """Test search term presence check."""
        assert QueryParameters(search_term="atrial septal defect").has_term() is True
        assert QueryParameters().has_term() is False
        assert QueryParameters(search_term="").has_term() is False

    def test_can_run_gene_query(self) -> None:
        """Test gene query capability."""
        params = QueryParameters(gene_symbol="MED13L")

        assert params.can_run_query(QueryParameterType.GENE) is True
        assert params.can_run_query(QueryParameterType.TERM) is False
        assert params.can_run_query(QueryParameterType.GENE_AND_TERM) is False
        assert params.can_run_query(QueryParameterType.NONE) is True
        assert params.can_run_query(QueryParameterType.API) is True

    def test_can_run_term_query(self) -> None:
        """Test term query capability."""
        params = QueryParameters(search_term="atrial septal defect")

        assert params.can_run_query(QueryParameterType.GENE) is False
        assert params.can_run_query(QueryParameterType.TERM) is True
        assert params.can_run_query(QueryParameterType.GENE_AND_TERM) is False
        assert params.can_run_query(QueryParameterType.NONE) is True
        assert params.can_run_query(QueryParameterType.API) is True

    def test_can_run_combined_query(self) -> None:
        """Test combined query capability."""
        params = QueryParameters(
            gene_symbol="MED13L",
            search_term="atrial septal defect",
        )

        assert params.can_run_query(QueryParameterType.GENE) is True
        assert params.can_run_query(QueryParameterType.TERM) is True
        assert params.can_run_query(QueryParameterType.GENE_AND_TERM) is True
        assert params.can_run_query(QueryParameterType.NONE) is True
        assert params.can_run_query(QueryParameterType.API) is True


class TestQueryTestResult:
    """Test QueryTestResult domain entity."""

    def test_create_success_result(self) -> None:
        """Test creating a successful test result."""
        result = TEST_RESULT_SUCCESS

        assert result.status == TestResultStatus.SUCCESS
        assert result.response_data is not None
        assert result.response_url is not None
        assert result.error_message is None
        assert result.execution_time_ms == 1200
        assert result.data_quality_score == 0.9

    def test_create_error_result(self) -> None:
        """Test creating an error test result."""
        result = TEST_RESULT_ERROR

        assert result.status == TestResultStatus.ERROR
        assert result.error_message == "API timeout"
        assert result.response_data is None
        assert result.data_quality_score is None

    def test_is_successful(self) -> None:
        """Test success status check."""
        assert TEST_RESULT_SUCCESS.is_successful() is True
        assert TEST_RESULT_ERROR.is_successful() is False

    def test_has_data(self) -> None:
        """Test data presence check."""
        assert TEST_RESULT_SUCCESS.has_data() is True

        no_data_result = create_test_query_test_result(
            response_data=None,
            response_url=None,
        )
        assert no_data_result.has_data() is False

    def test_get_duration_ms(self) -> None:
        """Test duration calculation."""
        result = TEST_RESULT_SUCCESS
        assert result.get_duration_ms() is not None
        assert result.get_duration_ms() > 0

        # Test with no completion time
        pending_result = create_test_query_test_result(completed_at=None)
        assert pending_result.get_duration_ms() is None
