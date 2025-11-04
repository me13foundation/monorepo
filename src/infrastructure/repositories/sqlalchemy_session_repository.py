"""
SQLAlchemy implementation of SessionRepository for MED13 Resource Library.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.session import UserSession, SessionStatus
from ...domain.repositories.session_repository import SessionRepository


class SqlAlchemySessionRepository(SessionRepository):
    """
    SQLAlchemy implementation of session repository.

    Provides asynchronous database operations for session management.
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

    async def create(self, session: UserSession) -> UserSession:
        """Create a new session."""
        async with self._get_session() as session_db:
            session_db.add(session)
            await session_db.commit()
            await session_db.refresh(session)
            return session

    async def get_by_id(self, session_id: UUID) -> Optional[UserSession]:
        """Get session by ID."""
        async with self._get_session() as session:
            stmt = select(UserSession).where(UserSession.id == session_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_access_token(self, access_token: str) -> Optional[UserSession]:
        """Get session by access token."""
        async with self._get_session() as session:
            stmt = select(UserSession).where(UserSession.session_token == access_token)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_refresh_token(self, refresh_token: str) -> Optional[UserSession]:
        """Get session by refresh token."""
        async with self._get_session() as session:
            stmt = select(UserSession).where(UserSession.refresh_token == refresh_token)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_active_by_refresh_token(
        self, refresh_token: str
    ) -> Optional[UserSession]:
        """Get active session by refresh token."""
        async with self._get_session() as session:
            stmt = select(UserSession).where(
                and_(
                    UserSession.refresh_token == refresh_token,
                    UserSession.status == SessionStatus.ACTIVE,
                    UserSession.refresh_expires_at > datetime.utcnow(),
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def update(self, session: UserSession) -> UserSession:
        """Update an existing session."""
        async with self._get_session() as session_db:
            # Merge the session object to handle detached instances
            merged_session = await session_db.merge(session)
            await session_db.commit()
            await session_db.refresh(merged_session)
            return merged_session

    async def delete(self, session_id: UUID) -> None:
        """Delete a session by ID."""
        async with self._get_session() as session:
            stmt = delete(UserSession).where(UserSession.id == session_id)
            await session.execute(stmt)
            await session.commit()

    async def revoke_session(self, session_id: UUID) -> None:
        """Revoke a session (mark as revoked)."""
        async with self._get_session() as session:
            stmt = (
                update(UserSession)
                .where(UserSession.id == session_id)
                .values(status=SessionStatus.REVOKED, last_activity=datetime.utcnow())
            )
            await session.execute(stmt)
            await session.commit()

    async def get_user_sessions(
        self, user_id: UUID, include_expired: bool = False
    ) -> List[UserSession]:
        """Get all sessions for a user."""
        async with self._get_session() as session:
            stmt = select(UserSession).where(UserSession.user_id == user_id)

            if not include_expired:
                stmt = stmt.where(
                    and_(
                        UserSession.status == SessionStatus.ACTIVE,
                        UserSession.expires_at > datetime.utcnow(),
                    )
                )

            stmt = stmt.order_by(UserSession.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_active_sessions(self, user_id: UUID) -> List[UserSession]:
        """Get active sessions for a user."""
        async with self._get_session() as session:
            stmt = (
                select(UserSession)
                .where(
                    and_(
                        UserSession.user_id == user_id,
                        UserSession.status == SessionStatus.ACTIVE,
                        UserSession.expires_at > datetime.utcnow(),
                    )
                )
                .order_by(UserSession.last_activity.desc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def count_active_sessions(self, user_id: UUID) -> int:
        """Count active sessions for a user."""
        async with self._get_session() as session:
            stmt = select(func.count(UserSession.id)).where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.status == SessionStatus.ACTIVE,
                    UserSession.expires_at > datetime.utcnow(),
                )
            )
            result = await session.execute(stmt)
            return result.scalar()

    async def revoke_all_user_sessions(self, user_id: UUID) -> int:
        """Revoke all sessions for a user."""
        async with self._get_session() as session:
            stmt = (
                update(UserSession)
                .where(
                    and_(
                        UserSession.user_id == user_id,
                        UserSession.status == SessionStatus.ACTIVE,
                    )
                )
                .values(status=SessionStatus.REVOKED, last_activity=datetime.utcnow())
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount

    async def revoke_expired_sessions(self) -> int:
        """Revoke all expired sessions."""
        async with self._get_session() as session:
            stmt = (
                update(UserSession)
                .where(
                    and_(
                        UserSession.status == SessionStatus.ACTIVE,
                        UserSession.expires_at <= datetime.utcnow(),
                    )
                )
                .values(status=SessionStatus.EXPIRED, last_activity=datetime.utcnow())
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount

    async def cleanup_expired_sessions(
        self, before_date: Optional[datetime] = None
    ) -> int:
        """Clean up old expired sessions."""
        if before_date is None:
            # Default: clean sessions older than 30 days
            before_date = datetime.utcnow() - timedelta(days=30)

        async with self._get_session() as session:
            # Delete old expired/revoked sessions
            stmt = delete(UserSession).where(
                and_(
                    or_(
                        UserSession.status == SessionStatus.EXPIRED,
                        UserSession.status == SessionStatus.REVOKED,
                    ),
                    UserSession.created_at < before_date,
                )
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount

    async def get_sessions_by_ip(self, ip_address: str) -> List[UserSession]:
        """Get sessions by IP address (for security monitoring)."""
        async with self._get_session() as session:
            stmt = (
                select(UserSession)
                .where(UserSession.ip_address == ip_address)
                .order_by(UserSession.created_at.desc())
                .limit(100)  # Limit for performance
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_session_activity(self, session_id: UUID) -> None:
        """Update session's last activity timestamp."""
        async with self._get_session() as session:
            stmt = (
                update(UserSession)
                .where(UserSession.id == session_id)
                .values(last_activity=datetime.utcnow())
            )
            await session.execute(stmt)
            await session.commit()

    async def get_recent_sessions(self, limit: int = 50) -> List[UserSession]:
        """Get most recently active sessions."""
        async with self._get_session() as session:
            stmt = (
                select(UserSession)
                .where(UserSession.status == SessionStatus.ACTIVE)
                .order_by(UserSession.last_activity.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_sessions_expiring_soon(
        self, within_minutes: int = 60
    ) -> List[UserSession]:
        """Get sessions expiring within specified time."""
        expiration_threshold = datetime.utcnow() + timedelta(minutes=within_minutes)

        async with self._get_session() as session:
            stmt = (
                select(UserSession)
                .where(
                    and_(
                        UserSession.status == SessionStatus.ACTIVE,
                        UserSession.expires_at <= expiration_threshold,
                        UserSession.expires_at > datetime.utcnow(),
                    )
                )
                .order_by(UserSession.expires_at.asc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())
