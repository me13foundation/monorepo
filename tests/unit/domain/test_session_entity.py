"""
Unit tests for Session domain entity.

Tests session entity behavior, validation, and lifecycle management.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.domain.entities.session import SessionStatus, UserSession


class TestUserSessionEntity:
    def test_session_creation_valid(self):
        """Test successful session creation with valid data."""
        user_id = uuid4()
        expires_at = datetime.now(UTC) + timedelta(minutes=15)
        refresh_expires_at = datetime.now(UTC) + timedelta(days=7)

        session = UserSession(
            user_id=user_id,
            session_token="jwt_access_token",
            refresh_token="jwt_refresh_token",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0...",
            expires_at=expires_at,
            refresh_expires_at=refresh_expires_at,
        )

        assert session.user_id == user_id
        assert session.session_token == "jwt_access_token"
        assert session.refresh_token == "jwt_refresh_token"
        assert session.ip_address == "192.168.1.1"
        assert session.user_agent == "Mozilla/5.0..."
        assert session.status == SessionStatus.ACTIVE
        assert session.id is not None
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.last_activity, datetime)

    def test_session_creation_invalid_timing(self):
        """Test session creation fails with invalid timing."""
        user_id = uuid4()
        past_time = datetime.now(UTC) - timedelta(hours=1)
        future_time = datetime.now(UTC) + timedelta(days=1)

        # Refresh token expires before access token
        with pytest.raises(
            ValueError,
            match="Refresh token must expire after access token",
        ):
            UserSession(
                user_id=user_id,
                session_token="token",
                refresh_token="refresh",
                expires_at=future_time,
                refresh_expires_at=past_time,  # Before access token expiry
            )

        # Access token already expired
        with pytest.raises(ValueError):
            UserSession(
                user_id=user_id,
                session_token="token",
                refresh_token="refresh",
                expires_at=past_time,  # Already expired
                refresh_expires_at=future_time,
            )

    def test_session_status_methods(self):
        """Test session status checking methods."""
        future_time = datetime.now(UTC) + timedelta(hours=1)

        # Active session
        active_session = UserSession(
            user_id=uuid4(),
            session_token="token",
            refresh_token="refresh",
            expires_at=future_time,
            refresh_expires_at=future_time + timedelta(days=1),
        )

        assert active_session.is_active() is True
        assert active_session.is_expired() is False
        assert active_session.can_refresh() is True

    def test_session_activity_tracking(self):
        """Test session activity update functionality."""
        session = UserSession(
            user_id=uuid4(),
            session_token="token",
            refresh_token="refresh",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            refresh_expires_at=datetime.now(UTC) + timedelta(days=1),
        )

        original_activity = session.last_activity

        # Small delay to ensure time difference
        import time

        time.sleep(0.001)

        session.update_activity()

        assert session.last_activity > original_activity

    def test_session_revocation(self):
        """Test session revocation functionality."""
        session = UserSession(
            user_id=uuid4(),
            session_token="token",
            refresh_token="refresh",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            refresh_expires_at=datetime.now(UTC) + timedelta(days=1),
        )

        assert session.status == SessionStatus.ACTIVE
        assert session.is_active() is True

        session.revoke()

        assert session.status == SessionStatus.REVOKED
        assert session.is_active() is False

    def test_session_extension(self):
        """Test session extension functionality."""
        session = UserSession(
            user_id=uuid4(),
            session_token="token",
            refresh_token="refresh",
            expires_at=datetime.now(UTC) + timedelta(minutes=5),  # Short expiry
            refresh_expires_at=datetime.now(UTC) + timedelta(days=1),
        )

        original_expires = session.expires_at
        original_refresh_expires = session.refresh_expires_at

        session.extend(
            access_token_expiry=timedelta(hours=2),
            refresh_token_expiry=timedelta(days=14),
        )

        assert session.expires_at > original_expires
        assert session.refresh_expires_at > original_refresh_expires
        assert session.last_activity > session.created_at

    def test_device_fingerprint_generation(self):
        """Test device fingerprint generation."""
        session = UserSession(
            user_id=uuid4(),
            session_token="token",
            refresh_token="refresh",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            refresh_expires_at=datetime.now(UTC) + timedelta(days=1),
        )

        ip_address = "192.168.1.100"
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

        fingerprint = session.generate_device_fingerprint(ip_address, user_agent)

        assert fingerprint is not None
        assert len(fingerprint) == 16  # Truncated SHA256 hex
        assert session.device_fingerprint == fingerprint

        # Same inputs should generate same fingerprint
        fingerprint2 = session.generate_device_fingerprint(ip_address, user_agent)
        assert fingerprint2 == fingerprint

        # Different inputs should generate different fingerprint
        fingerprint3 = session.generate_device_fingerprint("10.0.0.1", user_agent)
        assert fingerprint3 != fingerprint

    def test_device_fingerprint_with_additional_data(self):
        """Test device fingerprint with additional context."""
        session = UserSession(
            user_id=uuid4(),
            session_token="token",
            refresh_token="refresh",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            refresh_expires_at=datetime.now(UTC) + timedelta(days=1),
        )

        fingerprint1 = session.generate_device_fingerprint(
            "192.168.1.1",
            "Mozilla/5.0",
            {"screen": "1920x1080"},
        )

        fingerprint2 = session.generate_device_fingerprint(
            "192.168.1.1",
            "Mozilla/5.0",
            {"screen": "2560x1440"},
        )

        assert fingerprint1 != fingerprint2

    def test_suspicious_activity_detection(self):
        """Test suspicious activity detection."""
        session = UserSession(
            user_id=uuid4(),
            session_token="token",
            refresh_token="refresh",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows)",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            refresh_expires_at=datetime.now(UTC) + timedelta(days=1),
        )

        # Same IP and user agent - not suspicious
        assert not session.is_suspicious_activity(
            "192.168.1.100",
            "Mozilla/5.0 (Windows)",
        )

        # Different IP - suspicious
        assert session.is_suspicious_activity("10.0.0.1", "Mozilla/5.0 (Windows)")

        # Different user agent - suspicious
        assert session.is_suspicious_activity("192.168.1.100", "Chrome/90.0")

        # Both different - suspicious
        assert session.is_suspicious_activity("10.0.0.1", "Chrome/90.0")

    def test_suspicious_activity_no_baseline(self):
        """Test suspicious activity detection without baseline data."""
        session = UserSession(
            user_id=uuid4(),
            session_token="token",
            refresh_token="refresh",
            # No IP or user agent set
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            refresh_expires_at=datetime.now(UTC) + timedelta(days=1),
        )

        # No baseline data - cannot determine suspicious activity
        assert not session.is_suspicious_activity("192.168.1.100", "Mozilla/5.0")

    def test_time_calculations(self):
        """Test time-based calculations."""
        now = datetime.now(UTC)
        session = UserSession(
            user_id=uuid4(),
            session_token="token",
            refresh_token="refresh",
            expires_at=now + timedelta(minutes=30),
            refresh_expires_at=now + timedelta(days=1),
        )

        # Time until expiry
        time_until_expiry = session.time_until_expiry()
        assert time_until_expiry > timedelta(
            minutes=29,
        )  # Should be close to 30 minutes
        assert time_until_expiry < timedelta(minutes=31)

        # Time until refresh expiry
        time_until_refresh = session.time_until_refresh_expiry()
        assert time_until_refresh > timedelta(hours=23)  # Should be close to 24 hours
        assert time_until_refresh < timedelta(hours=25)

        # Time since activity
        time_since_activity = session.time_since_activity()
        assert time_since_activity >= timedelta(0)
        assert time_since_activity < timedelta(seconds=1)  # Very recent

    def test_string_representations(self):
        """Test string representations for logging/debugging."""
        session_id = uuid4()
        user_id = uuid4()
        future_time = datetime.now(UTC) + timedelta(hours=1)
        session = UserSession(
            id=session_id,
            user_id=user_id,
            session_token="token123",
            refresh_token="refresh456",
            status=SessionStatus.ACTIVE,
            expires_at=future_time,
            refresh_expires_at=future_time + timedelta(days=1),
        )

        str_repr = str(session)
        assert str(session_id) in str_repr
        assert str(user_id) in str_repr
        assert "active" in str_repr

        repr_str = repr(session)
        assert "UserSession(" in repr_str
        assert str(session_id) in repr_str

    def test_session_with_minimal_data(self):
        """Test session creation with minimal required data."""
        user_id = uuid4()
        expires_at = datetime.now(UTC) + timedelta(minutes=15)
        refresh_expires_at = datetime.now(UTC) + timedelta(days=7)

        session = UserSession(
            user_id=user_id,
            session_token="token",
            refresh_token="refresh",
            expires_at=expires_at,
            refresh_expires_at=refresh_expires_at,
            # No IP, user agent, or device fingerprint
        )

        assert session.ip_address is None
        assert session.user_agent is None
        assert session.device_fingerprint is None
        assert session.is_active() is True

    def test_session_status_transitions(self):
        """Test session status transitions."""
        session = UserSession(
            user_id=uuid4(),
            session_token="token",
            refresh_token="refresh",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            refresh_expires_at=datetime.now(UTC) + timedelta(days=1),
        )

        # Start as active
        assert session.status == SessionStatus.ACTIVE

        # Revoke
        session.revoke()
        assert session.status == SessionStatus.REVOKED

        # Cannot reactivate (once revoked, stays revoked)
        assert session.status == SessionStatus.REVOKED
