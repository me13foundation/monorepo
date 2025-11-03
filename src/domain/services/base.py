"""
Base domain service class for pure business logic.

Provides common functionality for domain services that encapsulate
business rules without infrastructure dependencies.
"""

from abc import ABC
from typing import Any, Dict, List, Optional


class DomainService(ABC):
    """
    Base class for domain services.

    Domain services encapsulate business logic that operates on
    domain entities and value objects without depending on infrastructure.
    """

    def validate_business_rules(
        self, entity: Any, operation: str, context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
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

    def apply_business_logic(self, entity: Any, operation: str) -> Any:
        """
        Apply business logic transformations to an entity.

        Args:
            entity: The domain entity to transform
            operation: The operation being performed

        Returns:
            The transformed entity
        """
        return entity

    def calculate_derived_properties(self, entity: Any) -> Dict[str, Any]:
        """
        Calculate derived properties for an entity.

        Args:
            entity: The domain entity

        Returns:
            Dictionary of derived property names and values
        """
        return {}


__all__ = ["DomainService"]
