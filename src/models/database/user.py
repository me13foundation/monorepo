"""
User database model for MED13 Resource Library.

SQLAlchemy model for user accounts with security fields and constraints.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import String, Boolean, Integer, TIMESTAMP, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from ...domain.entities.user import UserRole, UserStatus


class UserModel(Base):
    """
    SQLAlchemy model for users.

    Maps to the users table with all authentication and profile fields.
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique user identifier",
    )

    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False, doc="User's email address"
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique username for login",
    )
    full_name: Mapped[str] = mapped_column(
        String(100), nullable=False, doc="User's full display name"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False, doc="Bcrypt hashed password"
    )

    # Authorization
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        nullable=False,
        default=UserRole.VIEWER,
        index=True,
        doc="User's role for authorization",
    )
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus),
        nullable=False,
        default=UserStatus.PENDING_VERIFICATION,
        index=True,
        doc="Account status",
    )

    # Email verification
    email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, doc="Whether email has been verified"
    )
    email_verification_token: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, doc="Token for email verification"
    )

    # Password reset
    password_reset_token: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, doc="Token for password reset"
    )
    password_reset_expires: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        doc="Expiration time for password reset token",
    )

    # Security tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        index=True,
        doc="Last successful login timestamp",
    )
    login_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of consecutive failed login attempts",
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True, doc="Account lockout expiration time"
    )

    # Override base audit fields for explicit control
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="Account creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        doc="Last account update timestamp",
    )

    __table_args__ = (
        # Composite indexes for common queries
        Index("idx_users_email_active", "email", "status"),
        Index("idx_users_role_status", "role", "status"),
        Index("idx_users_created_at", "created_at"),
        {
            "comment": "User accounts with authentication and authorization data",
        },
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<UserModel(id={self.id}, email={self.email}, "
            f"username={self.username}, role={self.role.value}, "
            f"status={self.status.value})>"
        )
