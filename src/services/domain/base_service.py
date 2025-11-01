"""
Base service class for MED13 Resource Library.
Common functionality for domain services.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, Any
from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseService(Generic[T], ABC):
    """
    Base class for domain services providing common functionality.

    This abstract base class defines the interface for domain services
    and provides common operations like transaction management.
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        """Initialize service with optional session."""
        self._session = session

    @property
    @abstractmethod
    def repository(self) -> Any:
        """Return the repository instance for this service."""
        pass

    def commit(self) -> None:
        """Commit current transaction."""
        if self._session:
            self._session.commit()

    def rollback(self) -> None:
        """Rollback current transaction."""
        if self._session:
            self._session.rollback()

    def save_changes(self) -> None:
        """Save all changes in current transaction."""
        self.commit()
