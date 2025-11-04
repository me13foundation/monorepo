"""
Repository interface for Source Template entities.

Defines the contract for data access operations on data source templates,
enabling users to discover and use pre-configured source configurations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.domain.entities.source_template import (
    SourceTemplate,
    TemplateCategory,
)
from src.domain.entities.user_data_source import SourceType


class SourceTemplateRepository(ABC):
    """
    Abstract repository for SourceTemplate entities.

    Defines the interface for CRUD operations and specialized queries
    related to data source templates.
    """

    @abstractmethod
    def save(self, template: SourceTemplate) -> SourceTemplate:
        """
        Save a source template to the repository.

        Args:
            template: The SourceTemplate entity to save

        Returns:
            The saved SourceTemplate with any generated fields populated
        """
        pass

    @abstractmethod
    def find_by_id(self, template_id: UUID) -> Optional[SourceTemplate]:
        """
        Find a source template by its ID.

        Args:
            template_id: The unique identifier of the template

        Returns:
            The SourceTemplate if found, None otherwise
        """
        pass

    @abstractmethod
    def find_by_creator(
        self, creator_id: UUID, skip: int = 0, limit: int = 50
    ) -> List[SourceTemplate]:
        """
        Find all templates created by a specific user.

        Args:
            creator_id: The user ID of the creator
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of SourceTemplate entities created by the user
        """
        pass

    @abstractmethod
    def find_public_templates(
        self, skip: int = 0, limit: int = 50
    ) -> List[SourceTemplate]:
        """
        Find all public templates available for use.

        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of public SourceTemplate entities
        """
        pass

    @abstractmethod
    def find_by_category(
        self, category: TemplateCategory, skip: int = 0, limit: int = 50
    ) -> List[SourceTemplate]:
        """
        Find templates by category.

        Args:
            category: The category to filter by
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of SourceTemplate entities in the specified category
        """
        pass

    @abstractmethod
    def find_by_source_type(
        self, source_type: SourceType, skip: int = 0, limit: int = 50
    ) -> List[SourceTemplate]:
        """
        Find templates for a specific source type.

        Args:
            source_type: The source type to filter by
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of SourceTemplate entities for the specified source type
        """
        pass

    @abstractmethod
    def find_approved_templates(
        self, skip: int = 0, limit: int = 50
    ) -> List[SourceTemplate]:
        """
        Find all approved templates.

        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of approved SourceTemplate entities
        """
        pass

    @abstractmethod
    def find_by_tag(
        self, tag: str, skip: int = 0, limit: int = 50
    ) -> List[SourceTemplate]:
        """
        Find templates that have a specific tag.

        Args:
            tag: The tag to search for
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of SourceTemplate entities with the specified tag
        """
        pass

    @abstractmethod
    def search_by_name(
        self, query: str, skip: int = 0, limit: int = 50
    ) -> List[SourceTemplate]:
        """
        Search templates by name using fuzzy matching.

        Args:
            query: The search query string
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of SourceTemplate entities matching the search
        """
        pass

    @abstractmethod
    def find_available_for_user(
        self, user_id: Optional[UUID] = None, skip: int = 0, limit: int = 50
    ) -> List[SourceTemplate]:
        """
        Find templates available for a specific user (public + their own).

        Args:
            user_id: The user ID (None for anonymous users)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of SourceTemplate entities available to the user
        """
        pass

    @abstractmethod
    def increment_usage(self, template_id: UUID) -> Optional[SourceTemplate]:
        """
        Increment the usage count for a template.

        Args:
            template_id: The ID of the template

        Returns:
            The updated SourceTemplate if found, None otherwise
        """
        pass

    @abstractmethod
    def update_success_rate(
        self, template_id: UUID, success_rate: float
    ) -> Optional[SourceTemplate]:
        """
        Update the success rate for a template.

        Args:
            template_id: The ID of the template
            success_rate: The new success rate (0.0 to 1.0)

        Returns:
            The updated SourceTemplate if found, None otherwise
        """
        pass

    @abstractmethod
    def approve_template(self, template_id: UUID) -> Optional[SourceTemplate]:
        """
        Approve a template for general use.

        Args:
            template_id: The ID of the template to approve

        Returns:
            The updated SourceTemplate if found, None otherwise
        """
        pass

    @abstractmethod
    def make_public(self, template_id: UUID) -> Optional[SourceTemplate]:
        """
        Make a template publicly available.

        Args:
            template_id: The ID of the template

        Returns:
            The updated SourceTemplate if found, None otherwise
        """
        pass

    @abstractmethod
    def delete(self, template_id: UUID) -> bool:
        """
        Delete a template from the repository.

        Args:
            template_id: The ID of the template to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def count_by_creator(self, creator_id: UUID) -> int:
        """
        Count the number of templates created by a user.

        Args:
            creator_id: The user ID

        Returns:
            The count of templates created by the user
        """
        pass

    @abstractmethod
    def count_by_category(self, category: TemplateCategory) -> int:
        """
        Count the number of templates in a category.

        Args:
            category: The category to count

        Returns:
            The count of templates in the specified category
        """
        pass

    @abstractmethod
    def count_public_templates(self) -> int:
        """
        Count the number of public templates.

        Returns:
            The count of public templates
        """
        pass

    @abstractmethod
    def exists(self, template_id: UUID) -> bool:
        """
        Check if a template exists.

        Args:
            template_id: The ID to check

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    def get_popular_templates(self, limit: int = 10) -> List[SourceTemplate]:
        """
        Get the most popular templates by usage count.

        Args:
            limit: Maximum number of templates to return

        Returns:
            List of most popular SourceTemplate entities
        """
        pass

    @abstractmethod
    def get_template_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics about templates.

        Returns:
            Dictionary with various statistics
        """
        pass
