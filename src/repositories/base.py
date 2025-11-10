"""
Base repository class for MED13 Resource Library.
Provides common database operations following repository pattern.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import DeclarativeBase, Session

from src.database.session import get_session


class RepositoryProtocol[T: DeclarativeBase, ID](Protocol):
    """Protocol defining the repository interface."""

    @property
    def model_class(self) -> type[T]: ...

    def get_by_id(self, id: ID) -> T | None: ...

    def get_by_id_or_fail(self, id: ID) -> T: ...

    def find_all(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[T]: ...

    def find_by_criteria(
        self,
        criteria: dict[str, Any],
        limit: int | None = None,
    ) -> list[T]: ...

    def create(self, entity: T) -> T: ...

    def update(self, id: ID, updates: dict[str, Any]) -> T: ...

    def delete(self, id: ID) -> bool: ...

    def count(self) -> int: ...

    def exists(self, id: ID) -> bool: ...

    def save(self) -> None: ...

    def rollback(self) -> None: ...


class RepositoryError(Exception):
    """Base exception for repository operations."""


class NotFoundError(RepositoryError):
    """Raised when an entity is not found."""


class DuplicateError(RepositoryError):
    """Raised when attempting to create a duplicate entity."""


class BaseRepository[T: DeclarativeBase, ID](ABC):
    """
    Base repository class providing common CRUD operations.

    This abstract base class defines the interface for all repositories
    and provides implementations for common database operations.
    """

    def __init__(self, session: Session | None = None):
        """Initialize repository with optional session."""
        self._session = session

    @property
    @abstractmethod
    def model_class(self) -> type[T]:
        """Return the SQLAlchemy model class for this repository."""

    @property
    def session(self) -> Session:
        """Get the current database session."""
        if self._session is None:
            # Get session from context manager
            self._session = next(get_session())
        return self._session

    def get_by_id(self, entity_id: ID) -> T | None:
        """
        Retrieve an entity by its primary key.

        Args:
            entity_id: Primary key value

        Returns:
            Entity instance or None if not found
        """
        stmt = select(self.model_class).where(
            self.model_class.id == entity_id,  # type: ignore[attr-defined]
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_id_or_fail(self, entity_id: ID) -> T:
        """
        Retrieve an entity by its primary key, raising NotFoundError if not found.

        Args:
            entity_id: Primary key value

        Returns:
            Entity instance

        Raises:
            NotFoundError: If entity is not found
        """
        entity = self.get_by_id(entity_id)
        if entity is None:
            message = f"{self.model_class.__name__} with id {entity_id} not found"
            raise NotFoundError(message)
        return entity

    def find_all(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[T]:
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
        self,
        criteria: dict[str, Any],
        limit: int | None = None,
    ) -> list[T]:
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
                f"Duplicate {self.model_class.__name__}: {e!s}",
            ) from e

    def update(self, entity_id: ID, updates: dict[str, Any]) -> T:
        """
        Update an existing entity.

        Args:
            entity_id: Primary key of entity to update
            updates: Dictionary of field names to new values

        Returns:
            Updated entity

        Raises:
            NotFoundError: If entity is not found
        """
        stmt = (
            update(self.model_class)
            .where(self.model_class.id == entity_id)  # type: ignore[attr-defined]
            .values(**updates)
            .returning(self.model_class)
        )

        try:
            result = self.session.execute(stmt).scalar_one()
            self.session.flush()
            return result
        except NoResultFound as err:
            message = f"{self.model_class.__name__} with id {entity_id} not found"
            raise NotFoundError(message) from err

    def delete(self, entity_id: ID) -> bool:
        """
        Delete an entity by its primary key.

        Args:
            entity_id: Primary key of entity to delete

        Returns:
            True if entity was deleted, False if not found
        """
        stmt = delete(self.model_class).where(
            self.model_class.id == entity_id,  # type: ignore[attr-defined]
        )
        result = self.session.execute(stmt)
        self.session.flush()
        return bool(
            result.rowcount and result.rowcount > 0,  # type: ignore[attr-defined]
        )

    def count(self) -> int:
        """
        Count total number of entities.

        Returns:
            Total count of entities
        """
        stmt = select(func.count()).select_from(self.model_class)
        return self.session.execute(stmt).scalar_one()

    def exists(self, entity_id: ID) -> bool:
        """
        Check if an entity with the given ID exists.

        Args:
            entity_id: Primary key to check

        Returns:
            True if entity exists, False otherwise
        """
        stmt = (
            select(func.count())
            .select_from(self.model_class)
            .where(self.model_class.id == entity_id)  # type: ignore[attr-defined]
        )
        return self.session.execute(stmt).scalar_one() > 0

    def save(self) -> None:
        """Commit current transaction."""
        self.session.commit()

    def rollback(self) -> None:
        """Rollback current transaction."""
        self.session.rollback()
