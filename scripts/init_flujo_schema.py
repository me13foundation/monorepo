"""
Initialize the flujo schema in PostgreSQL.

This script creates the "flujo" schema if it doesn't exist. Flujo will
then auto-migrate its tables into this schema on first connection.

Usage:
    python scripts/init_flujo_schema.py
"""

from __future__ import annotations

from sqlalchemy import create_engine, text

from src.database.url_resolver import resolve_sync_database_url


def init_flujo_schema() -> None:
    """Create the flujo schema if it doesn't exist."""
    db_url = resolve_sync_database_url()

    if db_url.startswith("sqlite"):
        print("SQLite detected - no schema creation needed for Flujo.")
        return

    engine = create_engine(db_url)
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS flujo"))
            conn.commit()
            print("Schema 'flujo' created or already exists.")

            result = conn.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata "
                    "WHERE schema_name = 'flujo'",
                ),
            )
            if result.fetchone() is None:
                print("Failed to verify schema creation.")
                raise SystemExit(1)
            print("Schema 'flujo' verified.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    init_flujo_schema()
