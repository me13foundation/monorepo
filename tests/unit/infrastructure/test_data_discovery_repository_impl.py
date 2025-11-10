from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.infrastructure.repositories.data_discovery_repository_impl import (
    SQLAlchemyDataDiscoverySessionRepository,
    SQLAlchemyQueryTestResultRepository,
    _owner_identifier_candidates,
)
from src.models.database.base import Base
from src.models.database.data_discovery import (
    DataDiscoverySessionModel,
    QueryTestResultModel,
)


@pytest.fixture
def sa_session() -> Session:
    """Provide an in-memory SQLAlchemy session for repository tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Factory = sessionmaker(bind=engine)
    session = Factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _make_session_model(
    session_id: str,
    owner_id: str = "00000000-0000-0000-0000-000000000001",
) -> DataDiscoverySessionModel:
    """Create a DataDiscoverySessionModel with the given identifier."""
    return DataDiscoverySessionModel(
        id=session_id,
        owner_id=owner_id,
        research_space_id=None,
        name="Discovery Session",
        gene_symbol=None,
        search_term=None,
        selected_sources=[],
        tested_sources=[],
        total_tests_run=0,
        successful_tests=0,
        is_active=True,
        last_activity_at=datetime.now(UTC),
    )


def test_find_by_id_supports_hyphenless_identifiers(sa_session: Session) -> None:
    """Ensure repository resolves sessions stored without hyphens."""
    repo = SQLAlchemyDataDiscoverySessionRepository(sa_session)
    session_id = uuid4()
    sa_session.add(_make_session_model(str(session_id).replace("-", "")))
    sa_session.commit()

    result = repo.find_by_id(session_id)

    assert result is not None
    assert result.id == session_id


def test_delete_supports_hyphenless_identifiers(sa_session: Session) -> None:
    """Ensure delete removes rows stored without UUID hyphens."""
    repo = SQLAlchemyDataDiscoverySessionRepository(sa_session)
    session_id = uuid4()
    sa_session.add(_make_session_model(str(session_id).replace("-", "")))
    sa_session.commit()

    deleted = repo.delete(session_id)

    assert deleted is True
    assert repo.find_by_id(session_id) is None


def test_query_results_lookup_accepts_hyphenless_ids(sa_session: Session) -> None:
    """Ensure query test repository matches hyphenless session identifiers."""
    session_id = uuid4()
    result_id = uuid4()
    sa_session.add(_make_session_model(str(session_id).replace("-", "")))
    sa_session.add(
        QueryTestResultModel(
            id=str(result_id),
            session_id=str(session_id).replace("-", ""),
            catalog_entry_id="clinvar",
            status="success",
            gene_symbol=None,
            search_term=None,
            response_data=None,
            response_url=None,
            error_message=None,
            execution_time_ms=None,
            data_quality_score=None,
            completed_at=datetime.now(UTC),
        ),
    )
    sa_session.commit()

    query_repo = SQLAlchemyQueryTestResultRepository(sa_session)
    results = query_repo.find_by_session(session_id)

    assert len(results) == 1
    assert results[0].session_id == session_id


def test_find_by_owner_handles_legacy_numeric_ids_with_sqlite(
    sa_session: Session,
) -> None:
    """Ensure legacy numeric owner identifiers remain discoverable on SQLite."""
    repo = SQLAlchemyDataDiscoverySessionRepository(sa_session)
    legacy_owner = "1"
    legacy_session_id = str(uuid4())
    sa_session.add(_make_session_model(legacy_session_id, owner_id=legacy_owner))
    sa_session.commit()

    sessions = repo.find_by_owner(UUID("00000000-0000-0000-0000-000000000001"))

    assert len(sessions) == 1
    assert str(sessions[0].owner_id) == "00000000-0000-0000-0000-000000000001"
    assert sessions[0].id == UUID(legacy_session_id)


def test_owner_identifier_candidates_skip_numeric_when_legacy_disabled() -> None:
    """Ensure legacy numeric fallback is disabled when not allowed."""
    owner_uuid = UUID("00000000-0000-0000-0000-000000000001")

    candidates = _owner_identifier_candidates(
        owner_uuid,
        allow_legacy_formats=False,
    )

    assert candidates == [str(owner_uuid)]


def test_owner_identifier_candidates_include_numeric_with_legacy_enabled() -> None:
    """Ensure legacy numeric fallback remains available for SQLite."""
    owner_uuid = UUID("00000000-0000-0000-0000-000000000001")

    candidates = set(
        _owner_identifier_candidates(
            owner_uuid,
            allow_legacy_formats=True,
        ),
    )

    assert str(owner_uuid) in candidates
    assert "1" in candidates
