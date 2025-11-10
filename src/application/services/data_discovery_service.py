"""
Application service for Data Discovery operations.

Orchestrates data discovery sessions, source catalog management, and query testing
following Clean Architecture principles with dependency injection.
"""

import logging
from collections.abc import Sequence
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from src.application.services.source_management_service import (
    CreateSourceRequest,
    SourceManagementService,
)
from src.domain.entities.data_discovery_session import (
    DataDiscoverySession,
    QueryParameters,
    QueryParameterType,
    QueryTestResult,
    SourceCatalogEntry,
    TestResultStatus,
)
from src.domain.entities.user_data_source import SourceConfiguration, SourceType
from src.domain.repositories.data_discovery_repository import (
    DataDiscoverySessionRepository,
    QueryTestResultRepository,
    SourceCatalogRepository,
    SourceQueryClient,
)
from src.domain.repositories.source_template_repository import SourceTemplateRepository

logger = logging.getLogger(__name__)


class CreateDataDiscoverySessionRequest(BaseModel):
    """Request model for creating a new data discovery session."""

    owner_id: UUID
    name: str = "Untitled Session"
    research_space_id: UUID | None = None
    initial_parameters: QueryParameters = Field(
        default_factory=lambda: QueryParameters(
            gene_symbol=None,
            search_term=None,
        ),
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class UpdateSessionParametersRequest(BaseModel):
    """Request model for updating session parameters."""

    session_id: UUID
    parameters: QueryParameters

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ExecuteQueryTestRequest(BaseModel):
    """Request model for executing a query test."""

    session_id: UUID
    catalog_entry_id: str
    timeout_seconds: int = 30

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AddSourceToSpaceRequest(BaseModel):
    """Request model for adding a tested source to a research space."""

    session_id: UUID
    catalog_entry_id: str
    research_space_id: UUID
    source_config: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class DataDiscoveryService:
    """
    Application service for Data Discovery operations.

    Orchestrates data discovery sessions, source discovery, query testing,
    and integration with data source management.
    """

    def __init__(  # noqa: PLR0913 - explicit dependency wiring for Clean Architecture
        self,
        data_discovery_session_repository: DataDiscoverySessionRepository,
        source_catalog_repository: SourceCatalogRepository,
        query_result_repository: QueryTestResultRepository,
        source_query_client: SourceQueryClient,
        source_management_service: SourceManagementService,
        source_template_repository: SourceTemplateRepository | None = None,
    ):
        """
        Initialize the data discovery service.

        Args:
            data_discovery_session_repository: Repository for data discovery sessions
            source_catalog_repository: Repository for source catalog
            query_result_repository: Repository for query test results
            source_query_client: Client for executing external queries
            source_management_service: Service for data source management
            source_template_repository: Repository for source templates
        """
        self._session_repo = data_discovery_session_repository
        self._catalog_repo = source_catalog_repository
        self._query_repo = query_result_repository
        self._query_client = source_query_client
        self._source_service = source_management_service
        self._template_repo = source_template_repository

    def create_session(
        self,
        request: CreateDataDiscoverySessionRequest,
    ) -> DataDiscoverySession:
        """
        Create a new data discovery session.

        Args:
            request: Creation request with session details

        Returns:
            The created data discovery session
        """
        # Create new session entity
        session = DataDiscoverySession(
            id=uuid4(),  # Will be set by repository
            owner_id=request.owner_id,
            research_space_id=request.research_space_id,
            name=request.name,
            current_parameters=request.initial_parameters,
        )

        # Save to repository
        saved_session = self._session_repo.save(session)
        logger.info(
            "Created data discovery session %s for user %s",
            saved_session.id,
            request.owner_id,
        )
        return saved_session

    def get_session(self, session_id: UUID) -> DataDiscoverySession | None:
        """
        Get a data discovery session by ID.

        Args:
            session_id: The session ID

        Returns:
            The session if found, None otherwise
        """
        return self._session_repo.find_by_id(session_id)

    def get_user_sessions(
        self,
        owner_id: UUID,
        *,
        include_inactive: bool = False,
    ) -> list[DataDiscoverySession]:
        """
        Get all sessions for a user.

        Args:
            owner_id: The user ID
            include_inactive: Whether to include inactive sessions

        Returns:
            List of user's sessions
        """
        return self._session_repo.find_by_owner(
            owner_id,
            include_inactive=include_inactive,
        )

    def update_session_parameters(
        self,
        request: UpdateSessionParametersRequest,
    ) -> DataDiscoverySession | None:
        """
        Update parameters for a data discovery session.

        Args:
            request: Update request with new parameters

        Returns:
            Updated session or None if not found
        """
        session = self._session_repo.find_by_id(request.session_id)
        if not session:
            return None

        # Update parameters
        updated_session = session.update_parameters(request.parameters)

        # Save updated session
        saved_session = self._session_repo.save(updated_session)
        logger.info("Updated parameters for session %s", request.session_id)
        return saved_session

    def toggle_source_selection(
        self,
        session_id: UUID,
        catalog_entry_id: str,
    ) -> DataDiscoverySession | None:
        """
        Toggle source selection in a data discovery session.

        Args:
            session_id: The session ID
            catalog_entry_id: The catalog entry ID

        Returns:
            Updated session or None if not found
        """
        session = self._session_repo.find_by_id(session_id)
        if not session:
            logger.warning(
                "Unable to toggle source %s; session %s not found",
                catalog_entry_id,
                session_id,
            )
            return None

        catalog_entry = self._catalog_repo.find_by_id(catalog_entry_id)
        if not catalog_entry:
            logger.warning(
                "Catalog entry %s missing while toggling selection on session %s",
                catalog_entry_id,
                session_id,
            )
            return None

        if not catalog_entry.is_active:
            logger.warning(
                "Attempted to select inactive catalog entry %s on session %s",
                catalog_entry_id,
                session_id,
            )
            return None

        if catalog_entry.param_type != QueryParameterType.NONE:
            current_parameters = session.current_parameters
            if not current_parameters.can_run_query(catalog_entry.param_type):
                logger.warning(
                    "Session %s lacks required parameters for catalog entry %s",
                    session_id,
                    catalog_entry_id,
                )
                return None

        # Toggle selection
        updated_session = session.toggle_source_selection(catalog_entry_id)

        # Save updated session
        saved_session = self._session_repo.save(updated_session)
        logger.info(
            "Toggled source %s selection in session %s",
            catalog_entry_id,
            session_id,
        )
        return saved_session

    def set_source_selection(
        self,
        session_id: UUID,
        catalog_entry_ids: Sequence[str],
    ) -> DataDiscoverySession | None:
        """
        Explicitly set session selections to the provided catalog entries.
        """
        session = self._session_repo.find_by_id(session_id)
        if not session:
            logger.warning("Unable to set selections; session %s not found", session_id)
            return None

        if not catalog_entry_ids:
            updated_session = session.with_selected_sources([])
            return self._session_repo.save(updated_session)

        valid_sources: list[str] = []
        seen_sources: set[str] = set()
        for catalog_entry_id in catalog_entry_ids:
            if catalog_entry_id in seen_sources:
                continue
            seen_sources.add(catalog_entry_id)

            catalog_entry = self._catalog_repo.find_by_id(catalog_entry_id)
            if not catalog_entry:
                logger.warning(
                    "Catalog entry %s missing while bulk updating selection on session %s",
                    catalog_entry_id,
                    session_id,
                )
                continue
            if not catalog_entry.is_active:
                logger.warning(
                    "Attempted to select inactive catalog entry %s on session %s",
                    catalog_entry_id,
                    session_id,
                )
                continue
            if catalog_entry.param_type != QueryParameterType.NONE:
                current_parameters = session.current_parameters
                if not current_parameters.can_run_query(catalog_entry.param_type):
                    logger.warning(
                        "Session %s lacks required parameters for catalog entry %s",
                        session_id,
                        catalog_entry_id,
                    )
                    continue

            valid_sources.append(catalog_entry_id)

        updated_session = session.with_selected_sources(valid_sources)
        saved_session = self._session_repo.save(updated_session)
        logger.info(
            "Updated selections for session %s (%d sources retained)",
            session_id,
            len(valid_sources),
        )
        return saved_session

    def get_source_catalog(
        self,
        category: str | None = None,
        search_query: str | None = None,
    ) -> list[SourceCatalogEntry]:
        """
        Get the source catalog, optionally filtered.

        Args:
            category: Optional category filter
            search_query: Optional search query

        Returns:
            List of catalog entries
        """
        if search_query:
            return self._catalog_repo.search(search_query, category)
        if category:
            return self._catalog_repo.find_by_category(category)
        return self._catalog_repo.find_all_active()

    async def execute_query_test(
        self,
        request: ExecuteQueryTestRequest,
    ) -> QueryTestResult | None:
        """
        Execute a query test against a data source.

        Args:
            request: Test execution request

        Returns:
            Test result or None if session/entry not found
        """
        # Get session and catalog entry
        session = self._session_repo.find_by_id(request.session_id)
        catalog_entry = self._catalog_repo.find_by_id(request.catalog_entry_id)

        if not session or not catalog_entry:
            logger.warning(
                "Session %s or catalog entry %s not found",
                request.session_id,
                request.catalog_entry_id,
            )
            return None

        # Validate parameters
        if not self._query_client.validate_parameters(
            catalog_entry,
            session.current_parameters,
        ):
            logger.warning("Invalid parameters for source %s", request.catalog_entry_id)
            # Create failed result
            failed_result = QueryTestResult(
                id=uuid4(),
                catalog_entry_id=request.catalog_entry_id,
                session_id=request.session_id,
                parameters=session.current_parameters,
                status=TestResultStatus.VALIDATION_FAILED,
                error_message="Invalid parameters for this source",
                response_data=None,
                response_url=None,
                execution_time_ms=None,
                data_quality_score=None,
                completed_at=None,
            )
            return self._query_repo.save(failed_result)

        error_message: str | None = None
        response_data: dict[str, Any] | None = None
        response_url: str | None = None

        try:
            # Execute the query
            if catalog_entry.param_type == QueryParameterType.API:
                # For API sources, execute actual query
                result_data = await self._query_client.execute_query(
                    catalog_entry,
                    session.current_parameters,
                    request.timeout_seconds,
                )
                status = TestResultStatus.SUCCESS
                response_data = result_data
                response_url = None
            else:
                # For URL sources, generate URL
                response_url = self._query_client.generate_url(
                    catalog_entry,
                    session.current_parameters,
                )
                status = (
                    TestResultStatus.SUCCESS if response_url else TestResultStatus.ERROR
                )
                response_data = None
                if not response_url:
                    error_message = "Failed to generate URL"

            # Create test result
            test_result = QueryTestResult(
                id=uuid4(),
                catalog_entry_id=request.catalog_entry_id,
                session_id=request.session_id,
                parameters=session.current_parameters,
                status=status,
                response_data=response_data,
                response_url=response_url,
                error_message=error_message,
                execution_time_ms=None,
                data_quality_score=None,
                completed_at=None,
            )

            # Save result
            saved_result = self._query_repo.save(test_result)

            # Update session statistics
            updated_session = session.record_test(
                request.catalog_entry_id,
                success=status == TestResultStatus.SUCCESS,
            )
            self._session_repo.save(updated_session)

            # Update catalog usage stats
            self._catalog_repo.update_usage_stats(
                request.catalog_entry_id,
                success=status == TestResultStatus.SUCCESS,
            )

        except Exception as e:
            logger.exception(
                "Query test failed for source %s",
                request.catalog_entry_id,
            )

            # Create error result
            error_result = QueryTestResult(
                id=uuid4(),
                catalog_entry_id=request.catalog_entry_id,
                session_id=request.session_id,
                parameters=session.current_parameters,
                status=TestResultStatus.ERROR,
                error_message=str(e),
                response_data=None,
                response_url=None,
                execution_time_ms=None,
                data_quality_score=None,
                completed_at=None,
            )
            saved_result = self._query_repo.save(error_result)

            # Update session with failed test
            updated_session = session.record_test(
                request.catalog_entry_id,
                success=False,
            )
            self._session_repo.save(updated_session)

            return saved_result
        else:
            logger.info(
                "Executed query test for source %s in session %s",
                request.catalog_entry_id,
                request.session_id,
            )
            return saved_result

    def get_session_test_results(self, session_id: UUID) -> list[QueryTestResult]:
        """
        Get all test results for a session.

        Args:
            session_id: The session ID

        Returns:
            List of test results
        """
        return self._query_repo.find_by_session(session_id)

    async def add_source_to_space(
        self,
        request: AddSourceToSpaceRequest,
    ) -> UUID | None:
        """
        Add a tested source to a research space as a UserDataSource.

        Args:
            request: Request to add source to space

        Returns:
            ID of created UserDataSource or None if failed
        """
        # Get session and catalog entry
        session = self._session_repo.find_by_id(request.session_id)
        catalog_entry = self._catalog_repo.find_by_id(request.catalog_entry_id)

        if not session or not catalog_entry:
            logger.warning(
                "Session %s or catalog entry %s not found",
                request.session_id,
                request.catalog_entry_id,
            )
            return None

        # Check if source has a template
        template = None
        if catalog_entry.source_template_id and self._template_repo:
            template = self._template_repo.find_by_id(catalog_entry.source_template_id)

        # Create UserDataSource
        configuration = SourceConfiguration.model_validate(request.source_config or {})
        source_type = template.source_type if template else SourceType.API
        create_request = CreateSourceRequest(
            owner_id=session.owner_id,
            name=f"{catalog_entry.name} (from Data Discovery)",
            source_type=source_type,
            description=f"Added from Data Source Discovery: {catalog_entry.description}",
            template_id=catalog_entry.source_template_id,
            configuration=configuration,
            research_space_id=request.research_space_id,
            tags=["data-discovery", catalog_entry.category.lower()],
        )

        try:
            # Create the data source
            data_source = self._source_service.create_source(create_request)

            # Update session to mark source as added to space
            # Note: This would require extending the session entity to track added sources

        except Exception:
            logger.exception("Failed to add source to space")
            return None
        else:
            logger.info(
                "Added source %s to space %s",
                request.catalog_entry_id,
                request.research_space_id,
            )
            return data_source.id

    def delete_session(self, session_id: UUID) -> bool:
        """
        Delete a data discovery session and all its test results.

        Args:
            session_id: The session ID to delete

        Returns:
            True if deleted successfully
        """
        try:
            # Delete test results first
            self._query_repo.delete_session_results(session_id)

            # Delete session
            success = self._session_repo.delete(session_id)

        except Exception:
            logger.exception("Failed to delete session %s", session_id)
            return False
        else:
            if success:
                logger.info("Deleted data discovery session %s", session_id)
            else:
                logger.warning("Session %s not found for deletion", session_id)

            return success
