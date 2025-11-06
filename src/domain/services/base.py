"""
Base domain service class for pure business logic.

Provides common functionality for domain services that encapsulate
business rules without infrastructure dependencies.
"""

from typing import Any, TypeVar

T = TypeVar("T")


class DomainService:
    """
    Base class for domain services.

    Domain services encapsulate business logic that operates on
    domain entities and value objects without depending on infrastructure.
    """

    def validate_business_rules(
        self,
        _entity: Any,
        _operation: str,
        _context: dict[str, Any] | None = None,
    ) -> list[str]:
        """
        Validate business rules for an entity operation.

        Args:
            entity: The domain entity to validate
            operation: The operation being performed (create, update, etc.)
            context: Additional context for validation

        Returns:
            List of validation error messages (empty if valid)
        """
        return []

    def apply_business_logic(self, entity: Any, _operation: str) -> Any:
        """
        Apply business logic transformations to an entity.

        Args:
            entity: The domain entity to transform
            operation: The operation being performed

        Returns:
            The transformed entity
        """
        return entity

    def calculate_derived_properties(self, _entity: Any) -> dict[str, Any]:
        """
        Calculate derived properties for an entity.

        Args:
            entity: The domain entity

        Returns:
            Dictionary of derived property names and values
        """
        return {}


__all__ = ["DomainService"]
