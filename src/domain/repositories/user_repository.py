"""
User repository interface for MED13 Resource Library.

Defines the contract for user data persistence operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from ..entities.user import User, UserStatus


class UserRepository(ABC):
    """
    Abstract repository interface for user data operations.

    Defines the contract that all user repository implementations must follow.
    """

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User's unique identifier

        Returns:
            User entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: User's email address

        Returns:
            User entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: User's username

        Returns:
            User entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def create(self, user: User) -> User:
        """
        Create a new user.

        Args:
            user: User entity to create

        Returns:
            Created user entity with any generated fields
        """
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        """
        Update an existing user.

        Args:
            user: User entity with updated data

        Returns:
            Updated user entity
        """
        pass

    @abstractmethod
    async def delete(self, user_id: UUID) -> None:
        """
        Delete a user by ID.

        Args:
            user_id: User's unique identifier
        """
        pass

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """
        Check if user exists with given email.

        Args:
            email: Email address to check

        Returns:
            True if user exists, False otherwise
        """
        pass

    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """
        Check if user exists with given username.

        Args:
            username: Username to check

        Returns:
            True if user exists, False otherwise
        """
        pass

    @abstractmethod
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        status: Optional[UserStatus] = None,
    ) -> List[User]:
        """
        List users with optional filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            role: Filter by user role
            status: Filter by user status

        Returns:
            List of user entities
        """
        pass

    @abstractmethod
    async def count_users(
        self, role: Optional[str] = None, status: Optional[UserStatus] = None
    ) -> int:
        """
        Count users with optional filtering.

        Args:
            role: Filter by user role
            status: Filter by user status

        Returns:
            Number of users matching criteria
        """
        pass

    @abstractmethod
    async def count_users_by_status(self, status: UserStatus) -> int:
        """
        Count users by status.

        Args:
            status: User status to count

        Returns:
            Number of users with given status
        """
        pass

    @abstractmethod
    async def update_last_login(self, user_id: UUID) -> None:
        """
        Update user's last login timestamp.

        Args:
            user_id: User's unique identifier
        """
        pass

    @abstractmethod
    async def increment_login_attempts(self, user_id: UUID) -> int:
        """
        Increment login attempts counter.

        Args:
            user_id: User's unique identifier

        Returns:
            New login attempts count
        """
        pass

    @abstractmethod
    async def reset_login_attempts(self, user_id: UUID) -> None:
        """
        Reset login attempts counter.

        Args:
            user_id: User's unique identifier
        """
        pass

    @abstractmethod
    async def lock_account(self, user_id: UUID, locked_until: datetime) -> None:
        """
        Lock user account until specified time.

        Args:
            user_id: User's unique identifier
            locked_until: Time until account is locked
        """
        pass

    @abstractmethod
    async def unlock_account(self, user_id: UUID) -> None:
        """
        Unlock user account.

        Args:
            user_id: User's unique identifier
        """
        pass
