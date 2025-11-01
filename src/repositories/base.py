"""
Base repository class for MED13 Resource Library.
Provides common database operations following repository pattern.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Any, Dict, Type
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import Session, DeclarativeBase
from sqlalchemy.exc import IntegrityError, NoResultFound

from src.database.session import get_session

T = TypeVar("T", bound=DeclarativeBase)  # Model type
ID = TypeVar("ID")  # ID type


class RepositoryError(Exception):
    """Base exception for repository operations."""

    pass


class NotFoundError(RepositoryError):
    """Raised when an entity is not found."""

    pass


class DuplicateError(RepositoryError):
    """Raised when attempting to create a duplicate entity."""

    pass


class BaseRepository(Generic[T, ID], ABC):
    """
    Base repository class providing common CRUD operations.

    This abstract base class defines the interface for all repositories
    and provides implementations for common database operations.
    """

    def __init__(self, session: Optional[Session] = None):
        """Initialize repository with optional session."""
        self._session = session

    @property
    @abstractmethod
    def model_class(self) -> Type[T]:
        """Return the SQLAlchemy model class for this repository."""
        pass

    @property
    def session(self) -> Session:
        """Get the current database session."""
        if self._session is None:
            # Get session from context manager
            self._session = next(get_session())
        return self._session

    def get_by_id(self, id: ID) -> Optional[T]:
        """
        Retrieve an entity by its primary key.

        Args:
            id: Primary key value

        Returns:
            Entity instance or None if not found
        """
        stmt = select(self.model_class).where(
            self.model_class.id == id  # type: ignore[attr-defined]
        )
        result = self.session.execute(stmt).scalar_one_or_none()
        return result

    def get_by_id_or_fail(self, id: ID) -> T:
        """
        Retrieve an entity by its primary key, raising NotFoundError if not found.

        Args:
            id: Primary key value

        Returns:
            Entity instance

        Raises:
            NotFoundError: If entity is not found
        """
        entity = self.get_by_id(id)
        if entity is None:
            raise NotFoundError(f"{self.model_class.__name__} with id {id} not found")
        return entity

    def find_all(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[T]:
        """
        Retrieve all entities with optional pagination.

        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip

        Returns:
            List of entities
        """
        stmt = select(self.model_class)
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars())

    def find_by_criteria(
        self, criteria: Dict[str, Any], limit: Optional[int] = None
    ) -> List[T]:
        """
        Find entities matching the given criteria.

        Args:
            criteria: Dictionary of field names to values for filtering
            limit: Maximum number of entities to return

        Returns:
            List of matching entities
        """
        stmt = select(self.model_class)
        for field, value in criteria.items():
            if hasattr(self.model_class, field):
                stmt = stmt.where(getattr(self.model_class, field) == value)

        if limit:
            stmt = stmt.limit(limit)

        return list(self.session.execute(stmt).scalars())

    def create(self, entity: T) -> T:
        """
        Create a new entity in the database.

        Args:
            entity: Entity instance to create

        Returns:
            Created entity with assigned ID

        Raises:
            DuplicateError: If entity violates unique constraints
        """
        try:
            self.session.add(entity)
            self.session.flush()  # Flush to get the ID without committing
            return entity
        except IntegrityError as e:
            self.session.rollback()
            raise DuplicateError(
                f"Duplicate {self.model_class.__name__}: {str(e)}"
            ) from e

    def update(self, id: ID, updates: Dict[str, Any]) -> T:
        """
        Update an existing entity.

        Args:
            id: Primary key of entity to update
            updates: Dictionary of field names to new values

        Returns:
            Updated entity

        Raises:
            NotFoundError: If entity is not found
        """
        stmt = (
            update(self.model_class)
            .where(self.model_class.id == id)  # type: ignore[attr-defined]
            .values(**updates)
            .returning(self.model_class)
        )

        try:
            result = self.session.execute(stmt).scalar_one()
            self.session.flush()
            return result
        except NoResultFound:
            raise NotFoundError(f"{self.model_class.__name__} with id {id} not found")

    def delete(self, id: ID) -> bool:
        """
        Delete an entity by its primary key.

        Args:
            id: Primary key of entity to delete

        Returns:
            True if entity was deleted, False if not found
        """
        stmt = delete(self.model_class).where(
            self.model_class.id == id  # type: ignore[attr-defined]
        )
        result = self.session.execute(stmt)
        self.session.flush()
        return bool(
            result.rowcount and result.rowcount > 0  # type: ignore[attr-defined]
        )

    def count(self) -> int:
        """
        Count total number of entities.

        Returns:
            Total count of entities
        """
        stmt = select(func.count()).select_from(self.model_class)
        return self.session.execute(stmt).scalar_one()

    def exists(self, id: ID) -> bool:
        """
        Check if an entity with the given ID exists.

        Args:
            id: Primary key to check

        Returns:
            True if entity exists, False otherwise
        """
        stmt = (
            select(func.count())
            .select_from(self.model_class)
            .where(self.model_class.id == id)  # type: ignore[attr-defined]
        )
        count = self.session.execute(stmt).scalar_one()
        return count > 0

    def save(self) -> None:
        """Commit current transaction."""
        self.session.commit()

    def rollback(self) -> None:
        """Rollback current transaction."""
        self.session.rollback()
