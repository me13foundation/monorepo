"""Tests for SpaceDataDiscoveryService."""

from __future__ import annotations

from uuid import uuid4

from src.domain.entities.data_discovery_session import QueryParameters
from tests.test_types.data_discovery_fixtures import create_test_source_catalog_entry
from tests.test_types.fixtures import create_test_space_discovery_session
from tests.test_types.mocks import create_mock_space_discovery_service


def test_create_session_enforces_space_id() -> None:
    """Ensure new sessions are pinned to the scoped space."""
    space_id = uuid4()
    service, base_service = create_mock_space_discovery_service(space_id)
    params = QueryParameters(gene_symbol="MED13", search_term=None)

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
