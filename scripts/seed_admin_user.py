#!/usr/bin/env python3
"""Seed admin user for MED13 Resource Library.

Creates a default admin user for initial system access.
Run this script after database migrations to create the first admin account.
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
from src.domain.entities.user import UserRole, UserStatus
from src.infrastructure.security.password_hasher import PasswordHasher
from src.models.database.user import UserModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_admin_user(
    email: str = "admin@med13.org",
    username: str = "admin",
    password: str = "admin123",  # default password for seed script
    full_name: str = "MED13 Administrator",
) -> None:
    """
    Create an admin user in the database.

    Args:
        email: Admin email address
        username: Admin username
        password: Admin password (will be hashed)
        full_name: Admin full name
    """
    session = SessionLocal()
    password_hasher = PasswordHasher()

    try:
        # Check if admin already exists
        existing = session.query(UserModel).filter(UserModel.email == email).first()

        if existing:
            logger.warning("Admin user with email %s already exists!", email)
            logger.info("Skipping admin user creation.")
            return

        # Create admin user
        admin = UserModel(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=password_hasher.hash_password(password),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            email_verified=True,
        )

        session.add(admin)
        session.commit()

        logger.info("✅ Admin user created successfully!")
        logger.info("   Email: %s", email)
        logger.info("   Username: %s", username)
        logger.warning("   Password: %s", password)
        logger.warning("   ⚠️  Please change the password after first login!")

    except SQLAlchemyError:
        session.rollback()
        logger.exception("Failed to create admin user")
        raise
    finally:
        session.close()


def main() -> None:
    """Main entry point for admin user seeding."""
    parser = argparse.ArgumentParser(
        description="Create admin user for MED13 Resource Library",
    )
    parser.add_argument(
        "--email",
        default="admin@med13.org",
        help="Admin email address (default: admin@med13.org)",
    )
    parser.add_argument(
        "--username",
        default="admin",
        help="Admin username (default: admin)",
    )
    parser.add_argument(
        "--password",
        default="admin123",
        help="Admin password (default: admin123)",
    )
    parser.add_argument(
        "--full-name",
        default="MED13 Administrator",
        help="Admin full name (default: MED13 Administrator)",
    )

    args = parser.parse_args()

    try:
        create_admin_user(
            email=args.email,
            username=args.username,
            password=args.password,
            full_name=args.full_name,
        )
    except (SQLAlchemyError, ValueError, RuntimeError):
        logger.exception("Failed to seed admin user")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    main()
