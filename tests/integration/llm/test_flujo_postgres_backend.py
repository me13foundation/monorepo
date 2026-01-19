"""Integration tests for Flujo PostgreSQL backend."""

from __future__ import annotations

import pytest
from flujo.state.backends.postgres import PostgresBackend
from sqlalchemy import create_engine, text

from src.database.url_resolver import resolve_sync_database_url
from src.infrastructure.llm.flujo_config import resolve_flujo_state_uri


@pytest.fixture
def postgres_engine():
    """Create engine connected to test database and ensure flujo schema exists."""
    url = resolve_sync_database_url()
    if not url.startswith("postgresql"):
        pytest.skip("PostgreSQL required for this test")
    engine = create_engine(url)
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS flujo"))
        conn.commit()
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
class TestFlujoPostgresIntegration:
    """Integration tests for Flujo with PostgreSQL."""

    async def test_flujo_schema_exists(self, postgres_engine) -> None:
        """Verify flujo schema was created."""
        backend = PostgresBackend(resolve_flujo_state_uri())
        await backend.set_system_state("healthcheck", {"ok": True})
        with postgres_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata "
                    "WHERE schema_name = 'flujo'",
                ),
            )
            assert result.fetchone() is not None

    async def test_flujo_tables_created(self, postgres_engine) -> None:
        """Verify Flujo auto-migrated its tables."""
        backend = PostgresBackend(resolve_flujo_state_uri())
        await backend.set_system_state("healthcheck", {"ok": True})
        with postgres_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'flujo'",
                ),
            )
            tables = {row[0] for row in result.fetchall()}

            expected_core = {"runs", "steps", "workflow_state"}
            assert expected_core.issubset(tables)
