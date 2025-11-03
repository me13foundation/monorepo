"""
Base repository interfaces and specifications for domain data access.

Defines the fundamental contracts for repository patterns with proper
separation of concerns and dependency inversion.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar
from dataclasses import dataclass


TEntity = TypeVar("TEntity")
TId = TypeVar("TId")


@dataclass
class QuerySpecification:
    """Base class for query specifications."""

    filters: Dict[str, Any]
    sort_by: Optional[str] = None
    sort_order: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class Repository(Generic[TEntity, TId], ABC):
    """
    Abstract base repository interface.

    Defines the contract for data access operations without specifying
    the underlying implementation technology.
    """

    @abstractmethod
    def get_by_id(self, entity_id: TId) -> Optional[TEntity]:
        """Retrieve an entity by its ID."""
        pass

    @abstractmethod
    def find_all(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[TEntity]:
        """Retrieve all entities with optional pagination."""
        pass

    @abstractmethod
    def exists(self, entity_id: TId) -> bool:
        """Check if an entity exists."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Count total entities."""
        pass

    @abstractmethod
    def create(self, entity: TEntity) -> TEntity:
        """Create a new entity."""
        pass

    @abstractmethod
    def update(self, entity_id: TId, updates: Dict[str, Any]) -> TEntity:
        """Update an existing entity."""
        pass

    @abstractmethod
    def delete(self, entity_id: TId) -> bool:
        """Delete an entity."""
        pass

    @abstractmethod
    def find_by_criteria(self, spec: QuerySpecification) -> List[TEntity]:
        """Find entities matching the given specification."""
        pass


class UnitOfWork(ABC):
    """
    Unit of Work pattern for managing transactions across repositories.

    Ensures atomic operations across multiple repositories.
    """

    @abstractmethod
    def begin(self) -> None:
        """Begin a transaction."""
        pass

    @abstractmethod
    def commit(self) -> None:
        """Commit the transaction."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the transaction."""
        pass

    @abstractmethod
    def __enter__(self) -> "UnitOfWork":
        """Context manager entry."""
        pass

    @abstractmethod
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        pass


__all__ = [
    "Repository",
    "UnitOfWork",
    "QuerySpecification",
    "TEntity",
    "TId",
]
