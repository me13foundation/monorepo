"""
Session entity for MED13 Resource Library authentication system.

Manages user sessions, JWT token tracking, and session lifecycle.
"""

from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone
from enum import Enum


class SessionStatus(str, Enum):
    """Session status enumeration."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class UserSession(BaseModel):
    """
    User session domain entity with JWT token management.

    Tracks user sessions, token lifecycle, and security monitoring.
    """

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID

    # JWT tokens
    session_token: Optional[str] = None  # Access token
    refresh_token: Optional[str] = None

    # Session metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None

    # Session lifecycle
    status: SessionStatus = SessionStatus.ACTIVE
    expires_at: datetime
    refresh_expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def validate_session_times(self) -> "UserSession":
        """Validate session timing constraints."""
        # Refresh token must expire after access token
        if self.refresh_expires_at <= self.expires_at:
            raise ValueError("Refresh token must expire after access token")

        # Session should not be created with expired tokens
        now = datetime.now(timezone.utc)
        if self.expires_at <= now:
            raise ValueError("Cannot create session with already expired access token")

        return self

    def is_expired(self) -> bool:
        """Check if access token is expired."""
        return datetime.now(timezone.utc) > self.expires_at

    def is_refresh_expired(self) -> bool:
        """Check if refresh token is expired."""
        return datetime.now(timezone.utc) > self.refresh_expires_at

    def is_active(self) -> bool:
        """Check if session is active (not expired or revoked)."""
        return self.status == SessionStatus.ACTIVE and not self.is_expired()

    def can_refresh(self) -> bool:
        """Check if session can be refreshed."""
        return self.status == SessionStatus.ACTIVE and not self.is_refresh_expired()

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now(timezone.utc)

    def revoke(self) -> None:
        """Revoke the session (logout)."""
        self.status = SessionStatus.REVOKED

    def extend(
        self,
        access_token_expiry: timedelta = timedelta(minutes=15),
        refresh_token_expiry: timedelta = timedelta(days=7),
    ) -> None:
        """Extend session with new tokens."""
        now = datetime.now(timezone.utc)
        self.expires_at = now + access_token_expiry
        self.refresh_expires_at = now + refresh_token_expiry
        self.update_activity()

    def generate_device_fingerprint(
        self,
        ip_address: str,
        user_agent: str,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate a device fingerprint for session tracking."""
        import hashlib

        # Create fingerprint from device characteristics
        fingerprint_data = f"{ip_address}|{user_agent}"

        if additional_data:
            # Add additional device data if available
            fingerprint_data += f"|{additional_data}"

        # Hash for consistent length and privacy
        fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
        self.device_fingerprint = fingerprint
        return fingerprint

    def is_suspicious_activity(self, new_ip: str, new_user_agent: str) -> bool:
        """Check if session activity appears suspicious."""
        if not self.ip_address or not self.user_agent:
            return False  # Cannot determine without baseline

        # Check for IP address changes (basic heuristic)
        if self.ip_address != new_ip:
            # Could be legitimate (VPN, mobile network change)
            # More sophisticated logic could be added here
            return True

        # Check for user agent changes
        if self.user_agent != new_user_agent:
            # Could indicate different device/browser
            return True

        return False

    def time_since_activity(self) -> timedelta:
        """Calculate time since last activity."""
        return datetime.now(timezone.utc) - self.last_activity

    def time_until_expiry(self) -> timedelta:
        """Calculate time until access token expires."""
        return self.expires_at - datetime.now(timezone.utc)

    def time_until_refresh_expiry(self) -> timedelta:
        """Calculate time until refresh token expires."""
        return self.refresh_expires_at - datetime.now(timezone.utc)

    def __str__(self) -> str:
        """String representation for logging."""
        return (
            f"UserSession(id={self.id}, user_id={self.user_id}, "
            f"status={self.status.value}, expires_at={self.expires_at})"
        )

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"UserSession(id={self.id!r}, user_id={self.user_id!r}, "
            f"status={self.status!r}, expires_at={self.expires_at!r}, "
            f"last_activity={self.last_activity!r})"
        )
