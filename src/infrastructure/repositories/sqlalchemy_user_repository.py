"""
SQLAlchemy implementation of UserRepository for MED13 Resource Library.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import and_, delete, desc, func, select, update

from src.domain.entities.user import User, UserRole, UserStatus
from src.domain.repositories.user_repository import UserRepository
from src.models.database.user import UserModel

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import AsyncIterator
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyUserRepository(UserRepository):
    """
    SQLAlchemy implementation of user repository.

    Provides asynchronous database operations for user management using
    SQLAlchemy models mapped to domain entities.
    """

    def __init__(self, session_factory: Any) -> None:
        """
        Initialize repository with session factory.

        Args:
            session_factory: Async session factory for creating database sessions.
        """
        self._session_factory = session_factory

    @asynccontextmanager
    async def _session(self) -> AsyncIterator[AsyncSession]:
        """Provide an async session context."""
        async with self._session_factory() as session:
            yield session

    @staticmethod
    def _to_domain(model: UserModel | None) -> User | None:
        """Convert a SQLAlchemy model to a domain entity."""
        if model is None:
            return None
        return User.model_validate(model)

    @staticmethod
    def _to_domain_list(models: list[UserModel]) -> list[User]:
        """Convert a list of SQLAlchemy models to domain entities."""
        return [User.model_validate(user_model) for user_model in models]

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        async with self._session() as session:
            stmt = select(UserModel).where(UserModel.id == user_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_domain(model)

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email address."""
        async with self._session() as session:
            stmt = select(UserModel).where(UserModel.email == email)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_domain(model)

    async def get_by_username(self, username: str) -> User | None:
        """Get user by username."""
        async with self._session() as session:
            stmt = select(UserModel).where(UserModel.username == username)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_domain(model)

    async def create(self, user: User) -> User:
        """Create a new user."""
        async with self._session() as session:
            now = datetime.now(UTC)
            data = user.model_dump(mode="python")
            data.setdefault("created_at", now)
            data.setdefault("updated_at", now)

            db_user = UserModel(**data)
            session.add(db_user)
            await session.commit()
            await session.refresh(db_user)
            return User.model_validate(db_user)

    async def update(self, user: User) -> User:
        """Update an existing user."""
        async with self._session() as session:
            db_user = await session.get(UserModel, user.id)
            if db_user is None:
                message = f"User with id {user.id} not found"
                raise ValueError(message)

            data = user.model_dump(mode="python")
            data.pop("id", None)
            data.pop("created_at", None)
            data["updated_at"] = datetime.now(UTC)

            for field, value in data.items():
                setattr(db_user, field, value)

            await session.commit()
            await session.refresh(db_user)
            return User.model_validate(db_user)

    async def delete(self, user_id: UUID) -> None:
        """Delete a user by ID."""
        async with self._session() as session:
            stmt = delete(UserModel).where(UserModel.id == user_id)
            await session.execute(stmt)
            await session.commit()

    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists with given email."""
        async with self._session() as session:
            stmt = select(func.count()).where(UserModel.email == email)
            result = await session.execute(stmt)
            count = result.scalar_one()
            return int(count) > 0

    async def exists_by_username(self, username: str) -> bool:
        """Check if user exists with given username."""
        async with self._session() as session:
            stmt = select(func.count()).where(UserModel.username == username)
            result = await session.execute(stmt)
            count = result.scalar_one()
            return int(count) > 0

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: str | None = None,
        status: UserStatus | None = None,
    ) -> list[User]:
        """List users with optional filtering."""
        async with self._session() as session:
            stmt = select(UserModel)

            if role is not None:
                role_enum = UserRole(role)
                stmt = stmt.where(UserModel.role == role_enum)
            if status is not None:
                stmt = stmt.where(UserModel.status == status)

            stmt = stmt.order_by(desc(UserModel.created_at)).offset(skip).limit(limit)
            result = await session.execute(stmt)
            models = list(result.scalars().all())
            return self._to_domain_list(models)

    async def count_users(
        self,
        role: str | None = None,
        status: UserStatus | None = None,
    ) -> int:
        """Count users with optional filtering."""
        async with self._session() as session:
            stmt = select(func.count()).select_from(UserModel)

            if role is not None:
                role_enum = UserRole(role)
                stmt = stmt.where(UserModel.role == role_enum)
            if status is not None:
                stmt = stmt.where(UserModel.status == status)

            result = await session.execute(stmt)
            count = result.scalar_one()
            return int(count)

    async def count_users_by_status(self, status: UserStatus) -> int:
        """Count users by status."""
        async with self._session() as session:
            stmt = select(func.count()).where(UserModel.status == status)
            result = await session.execute(stmt)
            count = result.scalar_one()
            return int(count)

    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp."""
        async with self._session() as session:
            now = datetime.now(UTC)
            stmt = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(last_login=now, updated_at=now)
            )
            await session.execute(stmt)
            await session.commit()

    async def increment_login_attempts(self, user_id: UUID) -> int:
        """Increment login attempts counter."""
        async with self._session() as session:
            stmt = select(UserModel.login_attempts).where(UserModel.id == user_id)
            result = await session.execute(stmt)
            current_attempts = result.scalar_one_or_none()

            if current_attempts is None:
                return 0

            new_attempts = current_attempts + 1
            now = datetime.now(UTC)

            update_stmt = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(login_attempts=new_attempts, updated_at=now)
            )
            await session.execute(update_stmt)
            await session.commit()

            return new_attempts

    async def reset_login_attempts(self, user_id: UUID) -> None:
        """Reset login attempts counter."""
        async with self._session() as session:
            now = datetime.now(UTC)
            stmt = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(login_attempts=0, locked_until=None, updated_at=now)
            )
            await session.execute(stmt)
            await session.commit()

    async def lock_account(self, user_id: UUID, locked_until: datetime) -> None:
        """Lock user account until specified time."""
        async with self._session() as session:
            stmt = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(
                    locked_until=locked_until,
                    status=UserStatus.SUSPENDED,
                    updated_at=datetime.now(UTC),
                )
            )
            await session.execute(stmt)
            await session.commit()

    async def unlock_account(self, user_id: UUID) -> None:
        """Unlock user account."""
        async with self._session() as session:
            now = datetime.now(UTC)
            stmt = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(
                    locked_until=None,
                    status=UserStatus.ACTIVE,
                    login_attempts=0,
                    updated_at=now,
                )
            )
            await session.execute(stmt)
            await session.commit()

    async def get_recent_logins(self, limit: int = 10) -> list[User]:
        """Get users with most recent login activity."""
        async with self._session() as session:
            stmt = (
                select(UserModel)
                .where(
                    and_(
                        UserModel.last_login.is_not(None),
                        UserModel.status == UserStatus.ACTIVE,
                    ),
                )
                .order_by(desc(UserModel.last_login))
                .limit(limit)
            )
            result = await session.execute(stmt)
            models = list(result.scalars().all())
            return self._to_domain_list(models)

    async def get_users_pending_verification(self) -> list[User]:
        """Get users pending email verification."""
        async with self._session() as session:
            stmt = (
                select(UserModel)
                .where(
                    and_(
                        UserModel.status == UserStatus.PENDING_VERIFICATION,
                        UserModel.email_verification_token.is_not(None),
                    ),
                )
                .order_by(UserModel.created_at)
            )
            result = await session.execute(stmt)
            models = list(result.scalars().all())
            return self._to_domain_list(models)

    async def get_users_by_role(self, role: UserRole) -> list[User]:
        """Get all users with specific role."""
        async with self._session() as session:
            stmt = select(UserModel).where(UserModel.role == role)
            result = await session.execute(stmt)
            models = list(result.scalars().all())
            return self._to_domain_list(models)
