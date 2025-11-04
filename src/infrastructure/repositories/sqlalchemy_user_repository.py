"""
SQLAlchemy implementation of UserRepository for MED13 Resource Library.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.user import User, UserStatus, UserRole
from ...domain.repositories.user_repository import UserRepository


class SqlAlchemyUserRepository(UserRepository):
    """
    SQLAlchemy implementation of user repository.

    Provides asynchronous database operations for user management.
    """

    def __init__(self, session_factory):
        """
        Initialize repository with session factory.

        Args:
            session_factory: Callable that returns AsyncSession
        """
        self.session_factory = session_factory

    async def _get_session(self) -> AsyncSession:
        """Get database session."""
        return self.session_factory()

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        async with self._get_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        async with self._get_session() as session:
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        async with self._get_session() as session:
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """Create a new user."""
        async with self._get_session() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def update(self, user: User) -> User:
        """Update an existing user."""
        async with self._get_session() as session:
            # Merge the user object to handle detached instances
            merged_user = await session.merge(user)
            await session.commit()
            await session.refresh(merged_user)
            return merged_user

    async def delete(self, user_id: UUID) -> None:
        """Delete a user by ID."""
        async with self._get_session() as session:
            stmt = delete(User).where(User.id == user_id)
            await session.execute(stmt)
            await session.commit()

    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists with given email."""
        async with self._get_session() as session:
            stmt = select(func.count(User.id)).where(User.email == email)
            result = await session.execute(stmt)
            count = result.scalar()
            return count > 0

    async def exists_by_username(self, username: str) -> bool:
        """Check if user exists with given username."""
        async with self._get_session() as session:
            stmt = select(func.count(User.id)).where(User.username == username)
            result = await session.execute(stmt)
            count = result.scalar()
            return count > 0

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        status: Optional[UserStatus] = None,
    ) -> List[User]:
        """List users with optional filtering."""
        async with self._get_session() as session:
            stmt = select(User)

            # Apply filters
            if role:
                stmt = stmt.where(User.role == role)
            if status:
                stmt = stmt.where(User.status == status)

            # Apply pagination
            stmt = stmt.offset(skip).limit(limit)

            # Order by creation date (newest first)
            stmt = stmt.order_by(User.created_at.desc())

            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def count_users(
        self, role: Optional[str] = None, status: Optional[UserStatus] = None
    ) -> int:
        """Count users with optional filtering."""
        async with self._get_session() as session:
            stmt = select(func.count(User.id))

            # Apply filters
            if role:
                stmt = stmt.where(User.role == role)
            if status:
                stmt = stmt.where(User.status == status)

            result = await session.execute(stmt)
            return result.scalar()

    async def count_users_by_status(self, status: UserStatus) -> int:
        """Count users by status."""
        async with self._get_session() as session:
            stmt = select(func.count(User.id)).where(User.status == status)
            result = await session.execute(stmt)
            return result.scalar()

    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp."""
        async with self._get_session() as session:
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(last_login=datetime.utcnow(), updated_at=datetime.utcnow())
            )
            await session.execute(stmt)
            await session.commit()

    async def increment_login_attempts(self, user_id: UUID) -> int:
        """Increment login attempts counter."""
        async with self._get_session() as session:
            # Get current attempts
            stmt = select(User.login_attempts).where(User.id == user_id)
            result = await session.execute(stmt)
            current_attempts = result.scalar()

            if current_attempts is None:
                return 0

            new_attempts = current_attempts + 1

            # Update attempts
            update_stmt = (
                update(User)
                .where(User.id == user_id)
                .values(login_attempts=new_attempts, updated_at=datetime.utcnow())
            )
            await session.execute(update_stmt)
            await session.commit()

            return new_attempts

    async def reset_login_attempts(self, user_id: UUID) -> None:
        """Reset login attempts counter."""
        async with self._get_session() as session:
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(
                    login_attempts=0,
                    locked_until=None,  # Clear any lockout
                    updated_at=datetime.utcnow(),
                )
            )
            await session.execute(stmt)
            await session.commit()

    async def lock_account(self, user_id: UUID, locked_until: datetime) -> None:
        """Lock user account until specified time."""
        async with self._get_session() as session:
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(
                    locked_until=locked_until,
                    status=UserStatus.SUSPENDED,
                    updated_at=datetime.utcnow(),
                )
            )
            await session.execute(stmt)
            await session.commit()

    async def unlock_account(self, user_id: UUID) -> None:
        """Unlock user account."""
        async with self._get_session() as session:
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(
                    locked_until=None,
                    status=UserStatus.ACTIVE,
                    login_attempts=0,  # Reset attempts
                    updated_at=datetime.utcnow(),
                )
            )
            await session.execute(stmt)
            await session.commit()

    async def get_recent_logins(self, limit: int = 10) -> List[User]:
        """Get users with most recent login activity."""
        async with self._get_session() as session:
            stmt = (
                select(User)
                .where(
                    and_(User.last_login.isnot(None), User.status == UserStatus.ACTIVE)
                )
                .order_by(User.last_login.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_users_pending_verification(self) -> List[User]:
        """Get users pending email verification."""
        async with self._get_session() as session:
            stmt = (
                select(User)
                .where(
                    and_(
                        User.status == UserStatus.PENDING_VERIFICATION,
                        User.email_verification_token.isnot(None),
                    )
                )
                .order_by(User.created_at.asc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """Get all users with specific role."""
        async with self._get_session() as session:
            stmt = select(User).where(User.role == role)
            result = await session.execute(stmt)
            return list(result.scalars().all())
