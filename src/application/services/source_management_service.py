"""
Application service for user data source management.

Orchestrates domain services and repositories to implement
data source management use cases with proper business logic.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

from src.domain.entities.user_data_source import (
    UserDataSource,
    SourceType,
    SourceStatus,
    SourceConfiguration,
    IngestionSchedule,
    QualityMetrics,
)
from src.domain.entities.source_template import SourceTemplate
from src.domain.repositories.user_data_source_repository import UserDataSourceRepository
from src.domain.repositories.source_template_repository import SourceTemplateRepository


class CreateSourceRequest:
    """Request model for creating a new data source."""

    def __init__(
        self,
        owner_id: UUID,
        name: str,
        source_type: SourceType,
        description: str = "",
        template_id: Optional[UUID] = None,
        configuration: Optional[SourceConfiguration] = None,
        tags: Optional[List[str]] = None,
    ):
        self.owner_id = owner_id
        self.name = name
        self.description = description
        self.source_type = source_type
        self.template_id = template_id
        self.configuration = configuration or SourceConfiguration(
            url="",
            file_path="",
            format="",
            auth_type=None,
            auth_credentials={},
            requests_per_minute=None,
            field_mapping={},
            metadata={},
        )
        self.tags = tags or []


class UpdateSourceRequest:
    """Request model for updating a data source."""

    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        configuration: Optional[SourceConfiguration] = None,
        ingestion_schedule: Optional[IngestionSchedule] = None,
        tags: Optional[List[str]] = None,
    ):
        self.name = name
        self.description = description
        self.configuration = configuration
        self.ingestion_schedule = ingestion_schedule
        self.tags = tags


class SourceManagementService:
    """
    Application service for user data source management.

    Orchestrates data source operations including creation, configuration,
    lifecycle management, and quality monitoring.
    """

    def __init__(
        self,
        user_data_source_repository: UserDataSourceRepository,
        source_template_repository: SourceTemplateRepository,
    ):
        """
        Initialize the source management service.

        Args:
            user_data_source_repository: Repository for user data sources
            source_template_repository: Repository for source templates
        """
        self._source_repository = user_data_source_repository
        self._template_repository = source_template_repository

    def create_source(self, request: CreateSourceRequest) -> UserDataSource:
        """
        Create a new user data source.

        Args:
            request: Creation request with source details

        Returns:
            The created UserDataSource entity

        Raises:
            ValueError: If validation fails
        """
        # Validate template if provided
        if request.template_id:
            template = self._template_repository.find_by_id(request.template_id)
            if not template:
                raise ValueError(f"Template {request.template_id} not found")
            if not template.is_available(request.owner_id):
                raise ValueError(f"Template {request.template_id} is not available")

        # Create the source entity
        source = UserDataSource(
            id=UUID(),  # Will be set by repository
            owner_id=request.owner_id,
            name=request.name,
            description=request.description,
            source_type=request.source_type,
            template_id=request.template_id,
            configuration=request.configuration,
            tags=request.tags,
            last_ingested_at=None,
        )

        # Save to repository
        return self._source_repository.save(source)

    def get_source(
        self, source_id: UUID, owner_id: Optional[UUID] = None
    ) -> Optional[UserDataSource]:
        """
        Get a data source by ID.

        Args:
            source_id: The source ID
            owner_id: Optional owner filter for security

        Returns:
            The UserDataSource if found and accessible, None otherwise
        """
        source = self._source_repository.find_by_id(source_id)
        if source and owner_id and source.owner_id != owner_id:
            return None  # Not owned by this user
        return source

    def get_user_sources(
        self, owner_id: UUID, skip: int = 0, limit: int = 50
    ) -> List[UserDataSource]:
        """
        Get all data sources owned by a user.

        Args:
            owner_id: The user ID
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of user's data sources
        """
        return self._source_repository.find_by_owner(owner_id, skip, limit)

    def update_source(
        self, source_id: UUID, request: UpdateSourceRequest, owner_id: UUID
    ) -> Optional[UserDataSource]:
        """
        Update a data source.

        Args:
            source_id: The source ID
            request: Update request
            owner_id: The user making the request (for authorization)

        Returns:
            The updated UserDataSource if successful, None if not found or not authorized
        """
        source = self._source_repository.find_by_id(source_id)
        if not source or source.owner_id != owner_id:
            return None

        # Apply updates
        updated_source = source
        if request.name is not None:
            # This would create a new instance with updated name in a real immutable implementation
            pass
        if request.description is not None:
            updated_source = updated_source.model_copy(
                update={"description": request.description}
            )
        if request.configuration is not None:
            updated_source = updated_source.update_configuration(request.configuration)
        if request.ingestion_schedule is not None:
            updated_source = updated_source.model_copy(
                update={"ingestion_schedule": request.ingestion_schedule}
            )
        if request.tags is not None:
            updated_source = updated_source.model_copy(update={"tags": request.tags})

        return self._source_repository.save(updated_source)

    def delete_source(self, source_id: UUID, owner_id: UUID) -> bool:
        """
        Delete a data source.

        Args:
            source_id: The source ID
            owner_id: The user making the request (for authorization)

        Returns:
            True if deleted, False if not found or not authorized
        """
        source = self._source_repository.find_by_id(source_id)
        if not source or source.owner_id != owner_id:
            return False

        return self._source_repository.delete(source_id)

    def activate_source(
        self, source_id: UUID, owner_id: UUID
    ) -> Optional[UserDataSource]:
        """
        Activate a data source for ingestion.

        Args:
            source_id: The source ID
            owner_id: The user making the request

        Returns:
            The activated source if successful
        """
        source = self._source_repository.find_by_id(source_id)
        if not source or source.owner_id != owner_id:
            return None

        activated_source = source.update_status(SourceStatus.ACTIVE)
        return self._source_repository.save(activated_source)

    def deactivate_source(
        self, source_id: UUID, owner_id: UUID
    ) -> Optional[UserDataSource]:
        """
        Deactivate a data source.

        Args:
            source_id: The source ID
            owner_id: The user making the request

        Returns:
            The deactivated source if successful
        """
        source = self._source_repository.find_by_id(source_id)
        if not source or source.owner_id != owner_id:
            return None

        deactivated_source = source.update_status(SourceStatus.INACTIVE)
        return self._source_repository.save(deactivated_source)

    def record_ingestion_success(self, source_id: UUID) -> Optional[UserDataSource]:
        """
        Record successful data ingestion for a source.

        Args:
            source_id: The source ID

        Returns:
            The updated source if found
        """
        return self._source_repository.record_ingestion(source_id)

    def update_quality_metrics(
        self, source_id: UUID, metrics: QualityMetrics
    ) -> Optional[UserDataSource]:
        """
        Update quality metrics for a source.

        Args:
            source_id: The source ID
            metrics: The new quality metrics

        Returns:
            The updated source if found
        """
        return self._source_repository.update_quality_metrics(source_id, metrics)

    def get_sources_by_type(
        self, source_type: SourceType, skip: int = 0, limit: int = 50
    ) -> List[UserDataSource]:
        """
        Get sources by type.

        Args:
            source_type: The source type to filter by
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of sources of the specified type
        """
        return self._source_repository.find_by_type(source_type, skip, limit)

    def get_active_sources(
        self, skip: int = 0, limit: int = 50
    ) -> List[UserDataSource]:
        """
        Get all active sources.

        Args:
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of active sources
        """
        return self._source_repository.find_active_sources(skip, limit)

    def search_sources(
        self,
        query: str,
        owner_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[UserDataSource]:
        """
        Search sources by name.

        Args:
            query: Search query
            owner_id: Optional owner filter
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of matching sources
        """
        return self._source_repository.search_by_name(query, owner_id, skip, limit)

    def get_available_templates(
        self, user_id: Optional[UUID] = None, skip: int = 0, limit: int = 50
    ) -> List[SourceTemplate]:
        """
        Get templates available to a user.

        Args:
            user_id: The user ID (None for anonymous)
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of available templates
        """
        return self._template_repository.find_available_for_user(user_id, skip, limit)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics about data sources.

        Returns:
            Dictionary with various statistics
        """
        return self._source_repository.get_statistics()

    def validate_source_configuration(self, source: UserDataSource) -> List[str]:
        """
        Validate a source's configuration.

        Args:
            source: The source to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Basic validation
        if not source.name.strip():
            errors.append("Source name cannot be empty")

        if len(source.name) > 200:
            errors.append("Source name cannot exceed 200 characters")

        # Type-specific validation
        if source.source_type == SourceType.API:
            if not source.configuration.url:
                errors.append("API sources require a URL")
            if (
                source.configuration.requests_per_minute
                and source.configuration.requests_per_minute < 1
            ):
                errors.append("Requests per minute must be at least 1")

        elif source.source_type == SourceType.FILE_UPLOAD:
            if not source.configuration.file_path and not hasattr(
                source.configuration, "uploaded_file"
            ):
                errors.append("File upload sources require a file")

        # Template validation
        if source.template_id:
            template = self._template_repository.find_by_id(source.template_id)
            if not template:
                errors.append(
                    f"Referenced template {source.template_id} does not exist"
                )
            elif not template.is_available(source.owner_id):
                errors.append(f"Template {source.template_id} is not available")

        return errors
