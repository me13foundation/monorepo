"""
Mechanism repository interface - domain contract for mechanism data access.
"""

from abc import abstractmethod

from src.domain.entities.mechanism import Mechanism
from src.domain.repositories.base import Repository
from src.type_definitions.common import MechanismUpdate, QueryFilters


class MechanismRepository(Repository[Mechanism, int, MechanismUpdate]):
    """
    Domain repository interface for Mechanism entities.
    """

    @abstractmethod
    def find_by_name(self, name: str) -> Mechanism | None:
        """Find a mechanism by its name."""

    @abstractmethod
    def search_mechanisms(
        self,
        query: str,
        limit: int = 10,
        filters: QueryFilters | None = None,
    ) -> list[Mechanism]:
        """Search mechanisms by name/description with optional filters."""

    @abstractmethod
    def paginate_mechanisms(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        filters: QueryFilters | None = None,
    ) -> tuple[list[Mechanism], int]:
        """Retrieve paginated mechanisms with optional filters."""

    @abstractmethod
    def update_mechanism(
        self,
        mechanism_id: int,
        updates: MechanismUpdate,
    ) -> Mechanism:
        """Update a mechanism with type-safe update parameters."""


__all__ = ["MechanismRepository"]
