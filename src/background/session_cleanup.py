"""Background loop for session cleanup and maintenance."""

from __future__ import annotations

import asyncio
import logging

from src.infrastructure.dependency_injection.container import container

logger = logging.getLogger(__name__)


async def run_session_cleanup_loop(interval_seconds: int) -> None:
    """
    Continuously clean up expired sessions at the provided interval.

    This background task:
    1. Revokes sessions that have expired (marks them as EXPIRED)
    2. Deletes old expired/revoked sessions (older than 30 days)

    Args:
        interval_seconds: How often to run cleanup (in seconds)
    """
    while True:
        try:
            auth_service = await container.get_authentication_service()

            # First, revoke sessions that have expired but are still marked ACTIVE
            revoked_count = await auth_service.revoke_expired_sessions()
            if revoked_count > 0:
                logger.info(
                    "Session cleanup: Revoked %d expired sessions",
                    revoked_count,
                )

            # Then, clean up old expired/revoked sessions (older than 30 days)
            cleaned_count = await auth_service.cleanup_expired_sessions()
            if cleaned_count > 0:
                logger.info(
                    "Session cleanup: Deleted %d old expired sessions",
                    cleaned_count,
                )
        except asyncio.CancelledError:  # pragma: no cover - cancellation path
            logger.info("Session cleanup loop cancelled")
            break
        except Exception:  # pragma: no cover - defensive logging
            logger.exception("Session cleanup loop failed")
        await asyncio.sleep(interval_seconds)
