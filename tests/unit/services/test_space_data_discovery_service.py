"""Tests for SpaceDataDiscoveryService."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from src.domain.entities.data_discovery_parameters import AdvancedQueryParameters
from src.domain.entities.discovery_preset import (
    DiscoveryPreset,
    DiscoveryProvider,
    PresetScope,
)
from tests.test_types.data_discovery_fixtures import create_test_source_catalog_entry
from tests.test_types.fixtures import create_test_space_discovery_session
from tests.test_types.mocks import create_mock_space_discovery_service


def test_create_session_enforces_space_id() -> None:
    """Ensure new sessions are pinned to the scoped space."""
    space_id = uuid4()
    service, base_service = create_mock_space_discovery_service(space_id)
    params = AdvancedQueryParameters(gene_symbol="MED13", search_term=None)

    result = service.create_session(
        owner_id=uuid4(),
        name="Scoped Session",
        parameters=params,
    )

    base_service.create_session.assert_called_once()
    assert result.research_space_id == space_id


def test_list_sessions_uses_space_filter() -> None:
    """Delegates to base service and returns results."""
    space_id = uuid4()
    expected_session = create_test_space_discovery_session(space_id)
    service, base_service = create_mock_space_discovery_service(
        space_id,
        sessions=[expected_session],
    )

    owner_id = uuid4()
    sessions = service.list_sessions(owner_id=owner_id, include_inactive=False)

    base_service.get_sessions_for_space.assert_called_once_with(
        space_id,
        owner_id=owner_id,
        include_inactive=False,
    )
    assert sessions == [expected_session]


def test_session_access_blocked_for_other_space() -> None:
    """Sessions that belong to another space are hidden."""
    space_id = uuid4()
    other_space_id = uuid4()
    foreign_session = create_test_space_discovery_session(other_space_id)
    service, base_service = create_mock_space_discovery_service(
        space_id,
        sessions=[foreign_session],
    )
    result = service.get_session_for_owner(foreign_session.id, foreign_session.owner_id)

    assert result is None


def test_get_catalog_scopes_requests_to_space() -> None:
    """Ensure catalog fetches include research space context."""
    space_id = uuid4()
    catalog_entry = create_test_source_catalog_entry(entry_id="clinvar")
    service, base_service = create_mock_space_discovery_service(
        space_id,
        catalog_entries=[catalog_entry],
    )

    entries = service.get_catalog()

    base_service.get_source_catalog.assert_called_once_with(
        None,
        None,
        research_space_id=space_id,
    )
    assert entries == [catalog_entry]


def test_get_default_parameters_returns_latest_session() -> None:
    space_id = uuid4()
    owner_id = uuid4()
    session = create_test_space_discovery_session(
        space_id,
        owner_id=owner_id,
        current_parameters=AdvancedQueryParameters(
            gene_symbol="TP53",
            search_term="cancer",
        ),
    )
    service, base_service = create_mock_space_discovery_service(
        space_id,
        sessions=[session],
    )

    result = service.get_default_parameters(owner_id=owner_id)

    base_service.get_sessions_for_space.assert_called_with(
        space_id,
        owner_id=owner_id,
        include_inactive=True,
    )
    assert result.gene_symbol == "TP53"
    assert result.search_term == "cancer"


def test_get_default_parameters_falls_back_to_preset() -> None:
    space_id = uuid4()
    owner_id = uuid4()
    preset = DiscoveryPreset(
        id=uuid4(),
        owner_id=owner_id,
        provider=DiscoveryProvider.PUBMED,
        scope=PresetScope.USER,
        name="Fallback",
        description=None,
        parameters=AdvancedQueryParameters(gene_symbol="MED13", search_term="cardiac"),
        metadata={},
        research_space_id=space_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    service, base_service = create_mock_space_discovery_service(
        space_id,
        sessions=[],
        presets=[preset],
    )

    result = service.get_default_parameters(owner_id=owner_id)

    base_service.get_sessions_for_space.assert_called_with(
        space_id,
        owner_id=owner_id,
        include_inactive=True,
    )
    assert result.gene_symbol == "MED13"
    assert result.search_term == "cardiac"


def test_list_pubmed_presets_forwards_to_config_service() -> None:
    space_id = uuid4()
    owner_id = uuid4()
    service, _ = create_mock_space_discovery_service(space_id)

    service.list_pubmed_presets(owner_id)

    config_mock = service._config_service_mock
    config_mock.list_pubmed_presets.assert_called_once_with(
        owner_id,
        research_space_id=space_id,
    )
