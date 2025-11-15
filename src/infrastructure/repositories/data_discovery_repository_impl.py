"""
Infrastructure repository implementations for Data Discovery.

These implementations provide concrete SQLAlchemy-based data access
for data discovery sessions, source catalogs, and query test results.
"""

from uuid import UUID

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from src.database.sqlite_utils import retry_on_sqlite_lock
from src.domain.entities.data_discovery_session import (
    DataDiscoverySession,
    QueryTestResult,
    SourceCatalogEntry,
)
from src.domain.repositories.data_discovery_repository import (
    DataDiscoverySessionRepository,
    QueryTestResultRepository,
    SourceCatalogRepository,
)
from src.infrastructure.mappers.data_discovery_mapper import (
    query_result_to_entity,
    query_result_to_model,
    session_to_entity,
    session_to_model,
    source_catalog_to_entity,
    source_catalog_to_model,
)
from src.models.database.data_discovery import (
    DataDiscoverySessionModel,
    QueryTestResultModel,
    SourceCatalogEntryModel,
)

LEGACY_OWNER_ID_THRESHOLD = 1_000


def _expand_identifier(
    identifier: UUID | str,
    *,
    allow_legacy_formats: bool = True,
) -> list[str]:
    """
    Generate identifier variations that may exist in legacy rows.

    Some historical data persisted UUIDs without hyphens. Modern inserts
    always include hyphens, so we try both representations when looking up
    records to keep behaviour robust.
    """
    raw_value = str(identifier)
    if not allow_legacy_formats:
        return [raw_value]

    candidates = {raw_value}
    compact = raw_value.replace("-", "")
    if compact:
        candidates.add(compact)
    return list(candidates)


def _owner_identifier_candidates(
    identifier: UUID | str,
    *,
    allow_legacy_formats: bool,
) -> list[str]:
    """
    Build owner identifier candidates, optionally adding hyphenless/numeric fallbacks.
    """
    raw_value = str(identifier)
    if not allow_legacy_formats:
        return [raw_value]

    candidates = {raw_value}
    compact = raw_value.replace("-", "")
    if compact:
        candidates.add(compact)
        stripped = compact.lstrip("0")
        if stripped and stripped.isdigit():
            int_value = int(stripped)
            if int_value < LEGACY_OWNER_ID_THRESHOLD:
                candidates.add(str(int_value))
    return list(candidates)


def _dialect_name_for_session(session: Session) -> str:
    try:
        bind = session.get_bind()
    except RuntimeError:
        return ""
    if not isinstance(bind, Engine):
        return ""
    return bind.dialect.name


class SQLAlchemyDataDiscoverySessionRepository(DataDiscoverySessionRepository):
    """
    SQLAlchemy implementation of DataDiscoverySessionRepository.

    Provides database operations for data discovery sessions using SQLAlchemy ORM.
    """

    def __init__(self, session: Session):
        """
        Initialize the repository with a database session.

        Args:
            session: SQLAlchemy database session
        """
        self._session = session
        dialect_name = _dialect_name_for_session(session)
        self._allow_legacy_identifiers = dialect_name == "sqlite"
        dialect_name = _dialect_name_for_session(session)
        self._allow_legacy_identifiers = dialect_name == "sqlite"
        dialect_name = _dialect_name_for_session(session)
        self._allow_legacy_owner_formats = dialect_name == "sqlite"

    def save(self, session: DataDiscoverySession) -> DataDiscoverySession:
        """
        Save a data discovery session to the database.

        Args:
            session: The session entity to save

        Returns:
            The saved session entity
        """
        model = session_to_model(session)
        self._session.merge(model)

        def _commit() -> None:
            self._session.commit()

        retry_on_sqlite_lock(_commit)
        return session

    def find_by_id(self, session_id: UUID) -> DataDiscoverySession | None:
        """
        Find a data discovery session by ID.

        Args:
            session_id: The session ID to search for

        Returns:
            The session entity if found, None otherwise
        """
        for candidate in _expand_identifier(
            session_id,
            allow_legacy_formats=self._allow_legacy_owner_formats,
        ):
            model = self._session.get(DataDiscoverySessionModel, candidate)
            if model:
                return session_to_entity(model)
        return None

    def find_owned_session(
        self,
        session_id: UUID,
        owner_id: UUID,
    ) -> DataDiscoverySession | None:
        """
        Find a session by ID constrained to the provided owner.
        """
        session_candidates = _expand_identifier(
            session_id,
            allow_legacy_formats=self._allow_legacy_owner_formats,
        )
        owner_candidates = _owner_identifier_candidates(
            owner_id,
            allow_legacy_formats=self._allow_legacy_owner_formats,
        )
        model = (
            self._session.query(DataDiscoverySessionModel)
            .filter(
                DataDiscoverySessionModel.id.in_(session_candidates),
                DataDiscoverySessionModel.owner_id.in_(owner_candidates),
            )
            .first()
        )
        if model:
            return session_to_entity(model)
        return None

    def find_by_owner(
        self,
        owner_id: UUID | str,
        *,
        include_inactive: bool = False,
    ) -> list[DataDiscoverySession]:
        """
        Find all data discovery sessions for a specific owner.

        Args:
            owner_id: The owner ID to search for
            include_inactive: Whether to include inactive sessions

        Returns:
            List of session entities owned by the user
        """
        owner_candidates = _owner_identifier_candidates(
            owner_id,
            allow_legacy_formats=self._allow_legacy_owner_formats,
        )
        query = self._session.query(DataDiscoverySessionModel).filter(
            DataDiscoverySessionModel.owner_id.in_(owner_candidates),
        )

        if not include_inactive:
            query = query.filter_by(is_active=True)

        models = query.order_by(DataDiscoverySessionModel.last_activity_at.desc()).all()
        return [session_to_entity(model) for model in models]

    def find_by_space(
        self,
        space_id: UUID,
        *,
        include_inactive: bool = False,
    ) -> list[DataDiscoverySession]:
        """
        Find all data discovery sessions for a specific research space.

        Args:
            space_id: The research space ID

        Returns:
            List of session entities in the space
        """
        # Convert UUID to string for database query (database stores UUIDs as strings)
        space_ids = _expand_identifier(
            space_id,
            allow_legacy_formats=self._allow_legacy_owner_formats,
        )
        query = self._session.query(DataDiscoverySessionModel).filter(
            DataDiscoverySessionModel.research_space_id.in_(space_ids),
        )
        if not include_inactive:
            query = query.filter(DataDiscoverySessionModel.is_active.is_(True))

        models = query.order_by(
            DataDiscoverySessionModel.last_activity_at.desc(),
        ).all()
        return [session_to_entity(model) for model in models]

    def delete(self, session_id: UUID) -> bool:
        """
        Delete a workbench session from the database.

        Args:
            session_id: The session ID to delete

        Returns:
            True if deleted, False if not found
        """
        for candidate in _expand_identifier(
            session_id,
            allow_legacy_formats=self._allow_legacy_owner_formats,
        ):
            model = self._session.get(DataDiscoverySessionModel, candidate)
            if model:
                self._session.delete(model)

                def _commit() -> None:
                    self._session.commit()

                retry_on_sqlite_lock(_commit)
                return True
        return False


class SQLAlchemySourceCatalogRepository(SourceCatalogRepository):
    """
    SQLAlchemy implementation of SourceCatalogRepository.

    Provides database operations for the source catalog using SQLAlchemy ORM.
    """

    def __init__(self, session: Session):
        """
        Initialize the repository with a database session.

        Args:
            session: SQLAlchemy database session
        """
        self._session = session

    def save(self, entry: SourceCatalogEntry) -> SourceCatalogEntry:
        """
        Save a source catalog entry to the database.

        Args:
            entry: The catalog entry entity to save

        Returns:
            The saved catalog entry entity
        """
        model = source_catalog_to_model(entry)
        self._session.merge(model)
        self._session.commit()
        return entry

    def find_by_id(self, entry_id: str) -> SourceCatalogEntry | None:
        """
        Find a catalog entry by ID.

        Args:
            entry_id: The entry ID to search for

        Returns:
            The catalog entry entity if found, None otherwise
        """
        model = self._session.get(SourceCatalogEntryModel, entry_id)
        return source_catalog_to_entity(model) if model else None

    def find_all_active(self) -> list[SourceCatalogEntry]:
        """
        Find all active catalog entries.

        Returns:
            List of all active catalog entry entities
        """
        models = (
            self._session.query(SourceCatalogEntryModel)
            .filter_by(is_active=True)
            .order_by(SourceCatalogEntryModel.category, SourceCatalogEntryModel.name)
            .all()
        )
        return [source_catalog_to_entity(model) for model in models]

    def find_all(self) -> list[SourceCatalogEntry]:
        """
        Find all catalog entries regardless of activation state.

        Returns:
            List of catalog entry entities
        """
        models = (
            self._session.query(SourceCatalogEntryModel)
            .order_by(SourceCatalogEntryModel.category, SourceCatalogEntryModel.name)
            .all()
        )
        return [source_catalog_to_entity(model) for model in models]

    def find_by_category(self, category: str) -> list[SourceCatalogEntry]:
        """
        Find catalog entries by category.

        Args:
            category: The category to filter by

        Returns:
            List of catalog entry entities in the category
        """
        models = (
            self._session.query(SourceCatalogEntryModel)
            .filter_by(category=category, is_active=True)
            .order_by(SourceCatalogEntryModel.name)
            .all()
        )
        return [source_catalog_to_entity(model) for model in models]

    def search(
        self,
        query: str,
        category: str | None = None,
    ) -> list[SourceCatalogEntry]:
        """
        Search catalog entries by query.

        Args:
            query: Search query (name, description, tags)
            category: Optional category filter

        Returns:
            List of matching catalog entry entities
        """
        # Build the base query
        db_query = self._session.query(SourceCatalogEntryModel).filter_by(
            is_active=True,
        )

        if category:
            db_query = db_query.filter_by(category=category)

        # Search in name, description, and tags
        search_filter = f"%{query.lower()}%"
        models = (
            db_query.filter(
                (SourceCatalogEntryModel.name.ilike(search_filter))
                | (SourceCatalogEntryModel.description.ilike(search_filter))
                | (SourceCatalogEntryModel.tags.contains([query.lower()])),
            )
            .order_by(SourceCatalogEntryModel.category, SourceCatalogEntryModel.name)
            .all()
        )
        return [source_catalog_to_entity(model) for model in models]

    def update_usage_stats(
        self,
        entry_id: str,
        *,
        success: bool,
    ) -> bool:
        """
        Update usage statistics for a catalog entry.

        Args:
            entry_id: The entry ID to update
            success: Whether the usage was successful

        Returns:
            True if updated successfully
        """
        model = self._session.get(SourceCatalogEntryModel, entry_id)
        if not model:
            return False

        # Update usage count
        model.usage_count += 1

        # Recalculate success rate
        total_uses = model.usage_count
        if success:
            # This is a simplified calculation - in reality you'd track successes separately
            # For now, we'll assume success rate based on current value and new result
            current_successes = int(model.success_rate * (total_uses - 1))
            new_successes = current_successes + 1
            model.success_rate = new_successes / total_uses
        else:
            current_successes = int(model.success_rate * (total_uses - 1))
            model.success_rate = current_successes / total_uses

        def _commit() -> None:
            self._session.commit()

        retry_on_sqlite_lock(_commit)
        return True


class SQLAlchemyQueryTestResultRepository(QueryTestResultRepository):
    """
    SQLAlchemy implementation of QueryTestResultRepository.

    Provides database operations for query test results using SQLAlchemy ORM.
    """

    def __init__(self, session: Session):
        """
        Initialize the repository with a database session.

        Args:
            session: SQLAlchemy database session
        """
        self._session = session
        dialect_name = _dialect_name_for_session(session)
        self._allow_legacy_identifiers = dialect_name == "sqlite"

    def save(self, result: QueryTestResult) -> QueryTestResult:
        """
        Save a query test result to the database.

        Args:
            result: The test result entity to save

        Returns:
            The saved test result entity
        """
        model = query_result_to_model(result)
        self._session.merge(model)

        def _commit() -> None:
            self._session.commit()

        retry_on_sqlite_lock(_commit)
        return result

    def find_by_session(self, session_id: UUID) -> list[QueryTestResult]:
        """
        Find all test results for a workbench session.

        Args:
            session_id: The session ID

        Returns:
            List of test result entities for the session
        """
        session_ids = _expand_identifier(
            session_id,
            allow_legacy_formats=self._allow_legacy_identifiers,
        )
        models = (
            self._session.query(QueryTestResultModel)
            .filter(QueryTestResultModel.session_id.in_(session_ids))
            .order_by(QueryTestResultModel.started_at.desc())
            .all()
        )
        return [query_result_to_entity(model) for model in models]

    def find_by_source(
        self,
        catalog_entry_id: str,
        limit: int = 50,
    ) -> list[QueryTestResult]:
        """
        Find recent test results for a catalog entry.

        Args:
            catalog_entry_id: The catalog entry ID
            limit: Maximum number of results to return

        Returns:
            List of recent test result entities
        """
        models = (
            self._session.query(QueryTestResultModel)
            .filter_by(catalog_entry_id=catalog_entry_id)
            .order_by(QueryTestResultModel.started_at.desc())
            .limit(limit)
            .all()
        )
        return [query_result_to_entity(model) for model in models]

    def find_by_id(self, result_id: UUID) -> QueryTestResult | None:
        """
        Find a test result by ID.

        Args:
            result_id: The result ID

        Returns:
            The test result entity if found, None otherwise
        """
        # Convert UUID to string for database query (database stores UUIDs as strings)
        result_id_str = str(result_id) if isinstance(result_id, UUID) else result_id
        model = self._session.get(QueryTestResultModel, result_id_str)
        return query_result_to_entity(model) if model else None

    def delete_session_results(self, session_id: UUID) -> int:
        """
        Delete all test results for a session.

        Args:
            session_id: The session ID

        Returns:
            Number of results deleted
        """
        session_ids = _expand_identifier(
            session_id,
            allow_legacy_formats=self._allow_legacy_identifiers,
        )
        deleted_count = (
            self._session.query(QueryTestResultModel)
            .filter(
                QueryTestResultModel.session_id.in_(session_ids),
            )
            .delete(synchronize_session=False)
        )

        def _commit() -> None:
            self._session.commit()

        retry_on_sqlite_lock(_commit)
        return deleted_count
