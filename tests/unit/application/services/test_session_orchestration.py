"""
Unit tests for SessionOrchestrationService.
"""

from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.application.services.data_discovery_service.dtos import (
    OrchestratedSessionState,
)

# Import after other modules to minimize circular dependency risk in test environment
from src.application.services.data_discovery_service.session_orchestration import (
    SessionOrchestrationService,
)
from src.domain.entities.data_discovery_parameters import (
    AdvancedQueryParameters,
    PubMedSortOption,
)
from src.domain.entities.user_data_source import (
    SourceType,
)


@pytest.fixture
def mock_session_repo():
    return Mock()


@pytest.fixture
def mock_catalog_repo():
    mock = Mock()
    # Setup find_all_active for count calculation (len() is called on result)
    mock.find_all_active.return_value = [Mock() for _ in range(10)]
    return mock


@pytest.fixture
def service(mock_session_repo, mock_catalog_repo):
    return SessionOrchestrationService(mock_session_repo, mock_catalog_repo)


def create_mock_session(selected_sources=None):
    # Create a real AdvancedQueryParameters object instead of a Mock
    params = AdvancedQueryParameters(
        gene_symbol=None,
        search_term=None,
        publication_types=[],
        languages=[],
        sort_by=PubMedSortOption.RELEVANCE,
        max_results=100,
        additional_terms=None,
        variation_types=[],
        clinical_significance=[],
        is_reviewed=None,
        organism=None,
        date_from=None,
        date_to=None,
    )

    # The mapper expects certain attributes to be accessible as simple properties
    # Using a Mock with side_effect or spec can be tricky with Pydantic validation
    # So we'll create a mock that behaves like the entity for the attributes Pydantic reads

    mock = Mock()
    mock.id = uuid4()
    mock.owner_id = uuid4()
    mock.research_space_id = None
    mock.name = "Test Session"
    mock.current_parameters = params
    mock.selected_sources = selected_sources or []
    mock.tested_sources = []  # Changed to list as expected by entity
    mock.total_tests_run = 0
    mock.successful_tests = 0
    mock.is_active = True
    mock.created_at = datetime.now(UTC)
    mock.updated_at = datetime.now(UTC)
    mock.last_activity_at = datetime.now(UTC)

    return mock


def create_mock_source(source_id, category="Genomic"):
    mock = Mock()
    mock.id = source_id
    mock.name = f"Source {source_id}"
    mock.category = category
    mock.subcategory = None
    mock.description = "Test description"
    mock.source_type = SourceType.API
    mock.param_type = "gene"
    mock.is_active = True
    mock.requires_auth = False
    mock.usage_count = 0
    mock.success_rate = 1.0
    mock.tags = []
    mock.capabilities = {"supports_gene_search": True, "supports_term_search": False}

    # Add model_dump method for capabilities if needed by mapper, but capabilities is usually a dict
    return mock


class TestSessionOrchestrationService:
    def test_get_orchestrated_state_success(
        self,
        service,
        mock_session_repo,
        mock_catalog_repo,
    ):
        # Setup
        session_id = uuid4()
        source_id = "clinvar"
        mock_session = create_mock_session(selected_sources=[source_id])
        mock_source = create_mock_source(source_id)

        mock_session_repo.find_by_id.return_value = mock_session
        mock_catalog_repo.find_by_id.return_value = mock_source

        # Execute
        result = service.get_orchestrated_state(session_id)

        # Verify
        assert isinstance(result, OrchestratedSessionState)
        assert result.validation.is_valid is True
        assert result.view_context.selected_count == 1
        assert result.capabilities.supports_gene_search is True

    def test_update_selection_updates_repo(
        self,
        service,
        mock_session_repo,
        mock_catalog_repo,
    ):
        # Setup
        session_id = uuid4()
        mock_session = create_mock_session()
        mock_session_repo.find_by_id.return_value = mock_session
        mock_catalog_repo.find_by_id.side_effect = lambda source_id: create_mock_source(
            source_id,
        )

        new_sources = ["clinvar", "uniprot"]

        # Mock with_selected_sources to return the session itself with updated sources
        # because DataDiscoverySession is immutable and returns a new instance
        def update_sources(ids):
            mock_session.selected_sources = ids
            return mock_session

        mock_session.with_selected_sources.side_effect = update_sources

        # Execute
        service.update_selection(session_id, new_sources)

        # Verify
        mock_session_repo.save.assert_called_once()
        assert mock_session.selected_sources == new_sources

    def test_validation_logic_no_sources(self, service, mock_session_repo):
        # Setup
        session_id = uuid4()
        mock_session = create_mock_session(selected_sources=[])
        mock_session_repo.find_by_id.return_value = mock_session

        # Execute
        result = service.get_orchestrated_state(session_id)

        # Verify
        assert (
            result.validation.is_valid is True
        )  # Technically valid to have empty selection
        assert result.view_context.can_run_search is False  # But cannot run search
