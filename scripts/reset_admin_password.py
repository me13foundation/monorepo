#!/usr/bin/env python3
"""Reset admin user password for MED13 Resource Library.

This script resets the password for the admin user, useful when
the password is forgotten or needs to be reset.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path before importing project modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.exc import SQLAlchemyError

from src.database.session import SessionLocal
from src.infrastructure.security.password_hasher import PasswordHasher
from src.models.database.user import UserModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reset_admin_password(
    email: str = "admin@med13.org",
    password: str = "admin123",
) -> bool:
    """
    Reset password for admin user.

    Args:
        email: Admin email address
        password: New password (will be hashed)

    Returns:
        True if password was reset, False if user not found
    """
    session = SessionLocal()
    password_hasher = PasswordHasher()

    try:
        # Find admin user
        admin = session.query(UserModel).filter(UserModel.email == email).first()

        if not admin:
            logger.error("Admin user with email %s not found!", email)
            logger.info("Run 'make db-seed-admin' to create the admin user.")
            return False

        # Reset password
        admin.hashed_password = password_hasher.hash_password(password)
        session.commit()

        logger.info("✅ Admin password reset successfully!")
        logger.info("   Email: %s", email)
        logger.info("   Username: %s", admin.username)
        logger.warning("   New Password: %s", password)
        logger.warning("   ⚠️  Please change the password after first login!")

    except SQLAlchemyError:
        session.rollback()
        logger.exception("Failed to reset admin password")
        raise
    else:
        return True
    finally:
        session.close()


def verify_admin_user(email: str = "admin@med13.org") -> bool:
    """
    Verify admin user exists and show details.

    Args:
        email: Admin email address

    Returns:
        True if user exists, False otherwise
    """
    session = SessionLocal()

    try:
        admin = session.query(UserModel).filter(UserModel.email == email).first()

        if not admin:
            logger.error("Admin user with email %s not found!", email)
            logger.info("Run 'make db-seed-admin' to create the admin user.")
            return False

        logger.info("✅ Admin user found!")
        logger.info("   Email: %s", admin.email)
        logger.info("   Username: %s", admin.username)
        logger.info("   Full Name: %s", admin.full_name)
        logger.info("   Role: %s", admin.role)
        logger.info("   Status: %s", admin.status)
        logger.info("   Email Verified: %s", admin.email_verified)

    except SQLAlchemyError:
        logger.exception("Failed to verify admin user")
        raise
    else:
        return True
    finally:
        session.close()


def main() -> None:
    """Main entry point for password reset."""
    parser = argparse.ArgumentParser(
        description="Reset admin user password for MED13 Resource Library",
    )
    parser.add_argument(
        "--email",
        default="admin@med13.org",
        help="Admin email address (default: admin@med13.org)",
    )
    parser.add_argument(
        "--password",
        default="admin123",
        help="New password (default: admin123)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify admin user exists, don't reset password",
    )

    args = parser.parse_args()

    try:
        if args.verify_only:
            success = verify_admin_user(email=args.email)
        else:
            success = reset_admin_password(email=args.email, password=args.password)

        if not success:
            sys.exit(1)

    except (SQLAlchemyError, ValueError, RuntimeError):
        logger.exception("Failed to reset admin password")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    main()
