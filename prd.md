# PRD: Migrate Flujo State Storage from SQLite to PostgreSQL

**Document Version:** 1.0
**Date:** January 18, 2026
**Status:** Ready for Implementation
**Priority:** High
**Estimated Effort:** 1-2 days

---

## 1. Executive Summary

### 1.1 Objective

Migrate the Flujo AI orchestration framework's state storage from SQLite (`flujo_state.db`) to PostgreSQL, using a dedicated `flujo` schema within our existing `med13_dev` database. This aligns our AI infrastructure with the project's existing database strategy and improves production readiness.

### 1.2 Background

The MED13 Resource Library uses the **Flujo** Python library (`flujo>=0.6.3`) to orchestrate AI-powered query generation for data sources (currently PubMed). Flujo maintains persistent state for:

- Workflow execution history
- Step-by-step audit trails
- Token usage and cost tracking
- Debugging traces

Currently, this state is stored in a local SQLite file (`flujo_state.db`), which is unsuitable for production deployments with multiple instances.

### 1.3 Business Value

| Benefit | Description |
|:--------|:------------|
| **Production Readiness** | PostgreSQL handles concurrent AI operations across multiple app instances |
| **Unified Infrastructure** | Single database technology simplifies operations, backups, and monitoring |
| **Auditability** | AI decision trails stored alongside application data for compliance |
| **Scalability** | No SQLite file locking issues in multi-pod Kubernetes deployments |
| **Observability** | Query Flujo audit trails via standard PostgreSQL tooling |

---

## 2. Current State

### 2.1 Flujo Configuration

**File:** `flujo.toml`

```toml
# Current configuration (SQLite)
state_uri = "sqlite:///flujo_state.db"

[settings]
test_mode = false
memory_indexing_enabled = false

[architect]
state_machine_default = false

[cost]
strict = false

[cost.providers.openai."gpt-4o-mini"]
prompt_tokens_per_1k = 0.00015
completion_tokens_per_1k = 0.0006
```

### 2.2 Files Using Flujo

| File | Purpose |
|:-----|:--------|
| `src/infrastructure/llm/flujo_agent_adapter.py` | Core adapter implementing `AiAgentPort` |
| `src/infrastructure/dependency_injection/service_factories.py` | DI container factory |
| `src/infrastructure/factories/data_source_ai_test_factory.py` | AI test service factory |
| `src/infrastructure/factories/ingestion_scheduler_factory.py` | Ingestion scheduler factory |

### 2.3 Existing PostgreSQL Setup

**Database:** `med13_dev` (configurable via `MED13_POSTGRES_DB`)
**Docker Compose:** `docker-compose.postgres.yml`
**URL Resolution:** `src/database/url_resolver.py`
**Environment Variables:**
- `DATABASE_URL` - Sync SQLAlchemy URL
- `ASYNC_DATABASE_URL` - Async SQLAlchemy URL (optional override)

---

## 3. Target State

### 3.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                       │
│                       (med13_dev)                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────┐    ┌─────────────────────────────┐ │
│  │   public schema     │    │      flujo schema           │ │
│  │                     │    │                             │ │
│  │  - users            │    │  - workflow_state           │ │
│  │  - genes            │    │  - runs                     │ │
│  │  - variants         │    │  - steps                    │ │
│  │  - phenotypes       │    │  - traces                   │ │
│  │  - publications     │    │  - spans                    │ │
│  │  - evidence         │    │  - system_state             │ │
│  │  - research_spaces  │    │  - flujo_schema_versions    │ │
│  │  - user_data_sources│    │  - evaluations              │ │
│  │  - ingestion_jobs   │    │  - memories (optional)      │ │
│  │  - ... (15 more)    │    │                             │ │
│  └─────────────────────┘    └─────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Flujo Tables (Created Automatically)

| Table Name | Description |
|:-----------|:------------|
| `workflow_state` | Current state, context, and history of active workflows |
| `runs` | High-level execution records for every workflow run |
| `steps` | Detailed results, logs, and token usage for individual steps |
| `traces` | Full execution traces stored as JSON blobs for debugging |
| `spans` | Granular timing and status for observability (OpenTelemetry) |
| `system_state` | General-purpose key-value store for internal state |
| `flujo_schema_versions` | Migration tracking table |
| `evaluations` | Scores, feedback, and metadata for workflow evaluations |
| `memories` | Vector storage/RAG (requires `pgvector` extension; migration runs even if indexing is disabled) |

**Note:** No naming conflicts exist with our 24 existing tables in the `public` schema.

---

## 4. Implementation Requirements

### 4.1 Configuration Changes

#### 4.1.1 Update `flujo.toml`

```toml
# Flujo configuration for MED13 Resource Library
# FLUJO_STATE_URI (env) overrides this fallback.
state_uri = "sqlite:///flujo_state.db"

[settings]
test_mode = false
memory_indexing_enabled = false

[architect]
state_machine_default = false

[cost]
strict = false

[cost.providers.openai."gpt-4o-mini"]
prompt_tokens_per_1k = 0.00015
completion_tokens_per_1k = 0.0006
```

**Important:** Flujo reads `FLUJO_STATE_URI` (env) and/or `state_uri` in `flujo.toml`. If you remove `state_uri` and do not set `FLUJO_STATE_URI`, Flujo falls back to `sqlite:///.../flujo_ops.db`, not `flujo_state.db`.

#### 4.1.2 Environment Variable Configuration

Add environment variable for Flujo state backend:

| Variable | Description | Example Value |
|:---------|:------------|:--------------|
| `FLUJO_STATE_URI` | PostgreSQL connection string for Flujo | `postgresql://user:pass@localhost:5432/med13_dev?options=-c%20search_path=flujo,public` |

**Alternative approach:** Derive from existing `DATABASE_URL` programmatically, then set `FLUJO_STATE_URI` before Flujo initializes. Use a plain `postgresql://` DSN for asyncpg (no `+psycopg2`/`+asyncpg` suffix).

### 4.2 Code Changes

#### 4.2.1 Create Flujo URL Resolver

**New File:** `src/infrastructure/llm/flujo_config.py`

```python
"""
Flujo database configuration helpers.

Provides PostgreSQL connection configuration for Flujo's state backend,
using a dedicated 'flujo' schema to isolate AI orchestration state from
application data.
"""

from __future__ import annotations

import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from src.database.url_resolver import resolve_sync_database_url


def resolve_flujo_state_uri() -> str:
    """
    Resolve the Flujo state backend URI.

    Priority:
    1. FLUJO_STATE_URI environment variable (explicit override)
    2. Derive from DATABASE_URL with flujo schema

    Returns:
        PostgreSQL connection string configured for the flujo schema.
    """
    explicit_uri = os.getenv("FLUJO_STATE_URI")
    if explicit_uri:
        return explicit_uri

    # Derive from application DATABASE_URL
    base_url = resolve_sync_database_url()

    # For SQLite (dev/test), return as-is (Flujo will use file-based state)
    if base_url.startswith("sqlite"):
        return "sqlite:///flujo_state.db"

    # For PostgreSQL, normalize driver scheme and add schema search path
    return _add_flujo_schema(_normalize_postgres_dsn(base_url))


def _normalize_postgres_dsn(database_url: str) -> str:
    """Ensure asyncpg-compatible DSN (strip SQLAlchemy driver suffixes)."""
    replacements = (
        ("postgresql+psycopg2://", "postgresql://"),
        ("postgresql+psycopg://", "postgresql://"),
        ("postgresql+asyncpg://", "postgresql://"),
    )
    for prefix, replacement in replacements:
        if database_url.startswith(prefix):
            return database_url.replace(prefix, replacement, 1)
    return database_url


def _add_flujo_schema(postgres_url: str) -> str:
    """Add flujo schema to PostgreSQL connection string."""
    split = urlsplit(postgres_url)
    query_items = parse_qsl(split.query, keep_blank_values=True)

    # Check if options already set
    existing_options = [v for k, v in query_items if k == "options"]

    if existing_options:
        # Append to existing options
        new_options = f"{existing_options[0]} -c search_path=flujo,public"
        query_items = [(k, v) for k, v in query_items if k != "options"]
        query_items.append(("options", new_options))
    else:
        query_items.append(("options", "-c search_path=flujo,public"))

    rebuilt_query = urlencode(query_items, doseq=True)
    return urlunsplit((
        split.scheme,
        split.netloc,
        split.path,
        rebuilt_query,
        split.fragment,
    ))
```

#### 4.2.2 Update FlujoAgentAdapter Initialization

**File:** `src/infrastructure/llm/flujo_agent_adapter.py`

Set `FLUJO_STATE_URI` before Flujo initializes. Avoid `flujo.configure()`-style placeholders unless confirmed by Flujo docs.

```python
# Add import at top
from src.infrastructure.llm.flujo_config import resolve_flujo_state_uri

# In __init__ or module-level initialization, configure Flujo's state backend
os.environ.setdefault("FLUJO_STATE_URI", resolve_flujo_state_uri())
```

#### 4.2.3 Create Schema Migration Script

**New File:** `scripts/init_flujo_schema.py`

```python
"""
Initialize the flujo schema in PostgreSQL.

This script creates the 'flujo' schema if it doesn't exist. Flujo will
then auto-migrate its tables into this schema on first connection. Without
the schema present, tables will be created in `public` despite the intended
search_path ordering.

Usage:
    python scripts/init_flujo_schema.py
"""

from __future__ import annotations

import sys

from sqlalchemy import create_engine, text

from src.database.url_resolver import resolve_sync_database_url


def init_flujo_schema() -> None:
    """Create the flujo schema if it doesn't exist."""
    db_url = resolve_sync_database_url()

    if db_url.startswith("sqlite"):
        print("SQLite detected - no schema creation needed for Flujo.")
        return

    engine = create_engine(db_url)

    with engine.connect() as conn:
        # Create schema if not exists
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS flujo"))
        conn.commit()
        print("✓ Schema 'flujo' created or already exists.")

        # Verify schema
        result = conn.execute(text(
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name = 'flujo'"
        ))
        if result.fetchone():
            print("✓ Schema 'flujo' verified.")
        else:
            print("✗ Failed to verify schema creation.")
            sys.exit(1)


if __name__ == "__main__":
    init_flujo_schema()
```

### 4.3 Docker/Deployment Changes

#### 4.3.1 Update Docker Compose (Recommended)

If you want to auto-initialize the schema on container startup and ensure
pgvector is available for Flujo migrations:

**File:** `docker-compose.postgres.yml`

Add an init script volume mount (optional):

```yaml
services:
  postgres:
    # ... existing config ...
    volumes:
      - med13-postgres-data:/var/lib/postgresql/data
      - ./scripts/postgres-init:/docker-entrypoint-initdb.d:ro
```

**New File:** `scripts/postgres-init/01-create-flujo-schema.sql`

```sql
-- Create flujo schema for AI orchestration state
CREATE SCHEMA IF NOT EXISTS flujo;

-- Grant permissions (adjust user as needed)
GRANT ALL PRIVILEGES ON SCHEMA flujo TO med13_dev;
```

**Note:** The default `postgres:16-alpine` image does not include `pgvector`. Use a pgvector-enabled image (e.g., `pgvector/pgvector:pg16`) or install the extension in your Postgres instance so migration `003_vector_store.sql` can run.

### 4.4 Environment Variable Updates

#### 4.4.1 Development (`.env.local` or similar)

```bash
# Flujo State Backend (PostgreSQL with dedicated schema)
# Option A: Explicit URI
FLUJO_STATE_URI=postgresql://med13_dev:med13_dev_password@localhost:5432/med13_dev?options=-c%20search_path=flujo,public

# Option B: Let the app derive from DATABASE_URL (requires code implementation)
# Just ensure DATABASE_URL points to PostgreSQL
DATABASE_URL=postgresql://med13_dev:med13_dev_password@localhost:5432/med13_dev
```

#### 4.4.2 Production (GCP Secret Manager / Environment)

```bash
# Use proper credentials
FLUJO_STATE_URI=postgresql://prod_user:${DB_PASSWORD}@/med13_prod?host=/cloudsql/project:region:instance&options=-c%20search_path=flujo,public&sslmode=require
```

### 4.5 Makefile Updates

**File:** `Makefile`

Add convenience targets:

```makefile
## Flujo Schema Management
.PHONY: init-flujo-schema
init-flujo-schema: ## Initialize the flujo schema in PostgreSQL
	@echo "Creating flujo schema..."
	$(PYTHON) scripts/init_flujo_schema.py

.PHONY: setup-postgres
setup-postgres: ## Full PostgreSQL setup including flujo schema
	docker-compose -f docker-compose.postgres.yml up -d
	$(PYTHON) scripts/wait_for_postgres.py
	alembic upgrade head
	$(MAKE) init-flujo-schema
	@echo "PostgreSQL setup complete with flujo schema."
```

---

## 5. Testing Requirements

### 5.1 Unit Tests

**File:** `tests/unit/infrastructure/llm/test_flujo_config.py`

```python
"""Tests for Flujo configuration helpers."""

import os
from unittest.mock import patch

import pytest

from src.infrastructure.llm.flujo_config import (
    resolve_flujo_state_uri,
    _add_flujo_schema,
    _normalize_postgres_dsn,
)


class TestResolveFlujoUri:
    """Tests for resolve_flujo_database_uri."""

    def test_explicit_uri_takes_precedence(self) -> None:
        """FLUJO_STATE_URI should override derived URL."""
        with patch.dict(os.environ, {"FLUJO_STATE_URI": "postgresql://custom"}):
            assert resolve_flujo_state_uri() == "postgresql://custom"

    def test_sqlite_returns_file_based(self) -> None:
        """SQLite DATABASE_URL should return SQLite Flujo state."""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///test.db"}, clear=True):
            result = resolve_flujo_state_uri()
            assert result == "sqlite:///flujo_state.db"

    def test_postgres_adds_schema(self) -> None:
        """PostgreSQL should have flujo schema added."""
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "postgresql://user:pass@host:5432/db"},
            clear=True,
        ):
            result = resolve_flujo_state_uri()
            assert "search_path=flujo" in result


class TestAddFlujoSchema:
    """Tests for _add_flujo_schema helper."""

    def test_adds_options_to_clean_url(self) -> None:
        """Schema option should be added to URL without options."""
        url = "postgresql://user:pass@host:5432/db"
        result = _add_flujo_schema(url)
        assert "options=-c+search_path%3Dflujo%2Cpublic" in result

    def test_preserves_existing_query_params(self) -> None:
        """Existing query params should be preserved."""
        url = "postgresql://user:pass@host:5432/db?sslmode=require"
        result = _add_flujo_schema(url)
        assert "sslmode=require" in result
        assert "search_path" in result

    def test_normalizes_sqlalchemy_driver(self) -> None:
        """SQLAlchemy driver schemes should be normalized for asyncpg."""
        url = "postgresql+psycopg2://user:pass@host:5432/db"
        assert _normalize_postgres_dsn(url).startswith("postgresql://")
```

### 5.2 Integration Tests

**File:** `tests/integration/llm/test_flujo_postgres_backend.py`

```python
"""Integration tests for Flujo PostgreSQL backend."""

import pytest
from sqlalchemy import create_engine, text

from flujo.state.backends.postgres import PostgresBackend

from src.database.url_resolver import resolve_sync_database_url
from src.infrastructure.llm.flujo_config import resolve_flujo_state_uri


@pytest.mark.integration
@pytest.mark.asyncio
class TestFlujoPostgresIntegration:
    """Integration tests for Flujo with PostgreSQL."""

    @pytest.fixture
    def postgres_engine(self):
        """Create engine connected to test database."""
        url = resolve_sync_database_url()
        if url.startswith("sqlite"):
            pytest.skip("PostgreSQL required for this test")
        return create_engine(url)

    async def test_flujo_schema_exists(self, postgres_engine) -> None:
        """Verify flujo schema was created."""
        backend = PostgresBackend(resolve_flujo_state_uri())
        await backend.set_system_state("healthcheck", {"ok": True})
        with postgres_engine.connect() as conn:
            result = conn.execute(text(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name = 'flujo'"
            ))
            assert result.fetchone() is not None

    async def test_flujo_tables_created(self, postgres_engine) -> None:
        """Verify Flujo auto-migrated its tables."""
        backend = PostgresBackend(resolve_flujo_state_uri())
        await backend.set_system_state("healthcheck", {"ok": True})
        with postgres_engine.connect() as conn:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'flujo'"
            ))
            tables = {row[0] for row in result.fetchall()}

            # Check core tables exist
            expected_core = {"runs", "steps", "workflow_state"}
            assert expected_core.issubset(tables)
```

### 5.3 Test Configuration

Ensure tests can run with both SQLite (fast unit tests) and PostgreSQL (integration):

**File:** `tests/conftest.py` (update)

```python
# Add fixture for PostgreSQL-specific tests
@pytest.fixture(scope="session")
def postgres_required():
    """Skip test if PostgreSQL is not available."""
    url = os.getenv("DATABASE_URL", "")
    if not url.startswith("postgresql"):
        pytest.skip("PostgreSQL required")
```

---

## 6. Migration Plan

### 6.1 Pre-Migration Checklist

- [ ] Backup existing `flujo_state.db` file (if any valuable audit data)
- [ ] Verify PostgreSQL is running and accessible
- [ ] Confirm `DATABASE_URL` points to PostgreSQL (and pgvector is available)
- [ ] Decide whether to keep `state_uri` in `flujo.toml` as SQLite fallback
- [ ] Review Flujo documentation for any version-specific requirements

### 6.2 Migration Steps

| Step | Action | Command/File | Verification |
|:-----|:-------|:-------------|:-------------|
| 1 | Create feature branch | `git checkout -b feat/flujo-postgres-migration` | Branch exists |
| 2 | Add `flujo_config.py` | Create file per spec | File exists |
| 3 | Add init script | Create `scripts/init_flujo_schema.py` | Script runs |
| 4 | Update Makefile | Add `init-flujo-schema` target | `make init-flujo-schema` works |
| 5 | Update `flujo.toml` | Keep `state_uri` for SQLite fallback or set `FLUJO_STATE_URI` for Postgres | Config valid |
| 6 | Add unit tests | Create test file per spec | `make test` passes |
| 7 | Initialize schema | `make init-flujo-schema` | Schema exists in DB |
| 8 | Test AI features | Trigger AI query generation | Flujo tables created |
| 9 | Verify audit trail | Check `flujo.runs` table | Records present |
| 10 | Remove old SQLite | Delete `flujo_state.db` from `.gitignore` note | Clean state |

### 6.3 Rollback Plan

If issues arise:

1. Set `FLUJO_STATE_URI=sqlite:///flujo_state.db` or restore `state_uri` in `flujo.toml`
2. Flujo will auto-create the SQLite file on next run (default is `flujo_ops.db` if `state_uri` is removed)
3. No data migration needed (new runs will create new records)

---

## 7. Acceptance Criteria

### 7.1 Functional Requirements

- [ ] Flujo state persists in PostgreSQL `flujo` schema
- [ ] AI query generation works identically to before
- [ ] Audit trail (runs, steps) queryable via SQL
- [ ] Multiple app instances can run without conflicts
- [ ] Development environment defaults work (SQLite fallback, or explicit `FLUJO_STATE_URI`)

### 7.2 Non-Functional Requirements

- [ ] No performance regression in AI query generation
- [ ] Connection pooling respects existing limits
- [ ] TLS enforced in production (ensure `FLUJO_STATE_URI` includes `sslmode=require` or derive from `resolve_sync_database_url`)
- [ ] Type safety maintained (no `Any` types introduced)

### 7.3 Documentation

- [ ] Update `AGENTS.md` with Flujo PostgreSQL configuration
- [ ] Update `docs/status/AI_MANAGED_DATA_SOURCES_STATUS.md`
- [ ] Add inline comments explaining schema separation

---

## 8. Security Considerations

| Concern | Mitigation |
|:--------|:-----------|
| Credentials in config | Use environment variables, never hardcode |
| Schema isolation | Dedicated `flujo` schema prevents accidental cross-contamination |
| TLS in production | `FLUJO_STATE_URI` must include TLS params unless derived from `resolve_sync_database_url` |
| Connection string logging | Ensure passwords are not logged (use `***` masking) |

---

## 9. Open Questions

| Question | Owner | Status |
|:---------|:------|:-------|
| Should we set `FLUJO_STATE_URI` in app startup or keep `state_uri` in `flujo.toml`? | Developer | To decide |
| Is `DATABASE_URL` always `postgresql://` or can it include SQLAlchemy driver suffixes? | Developer | To confirm |
| Should we enable `pgvector` for the `memories` table (future RAG)? | Tech Lead | Deferred |
| Do we need to migrate existing SQLite data, or is fresh state acceptable? | Product | Fresh state OK |

---

## 10. References

- **Flujo Documentation:** PostgreSQL backend configuration
- **Project Files:**
  - `src/infrastructure/llm/flujo_agent_adapter.py` - Current Flujo integration
  - `src/database/url_resolver.py` - Database URL patterns
  - `docker-compose.postgres.yml` - PostgreSQL configuration
  - `docs/status/AI_MANAGED_DATA_SOURCES_STATUS.md` - Flujo architecture docs

---

## 11. Appendix: Flujo Tables vs Application Tables

### No Naming Conflicts Confirmed

**Application Tables (public schema):** 24 tables
```
audit_logs, data_discovery_sessions, data_source_activation_rules,
discovery_presets, discovery_search_jobs, evidence, genes, ingestion_jobs,
phenotypes, publications, query_test_results, research_space_memberships,
research_spaces, reviews, sessions, source_catalog_entries, source_templates,
storage_configurations, storage_health_snapshots, storage_operations,
system_status, user_data_sources, users, variants
```

**Flujo Tables (flujo schema):** 9 tables
```
workflow_state, runs, steps, traces, spans, system_state,
flujo_schema_versions, evaluations, memories
```

**Overlap:** None

---

*Document prepared for MED13 Resource Library development team.*
