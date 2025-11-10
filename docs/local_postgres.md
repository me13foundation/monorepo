# Local Postgres Workflow

SQLite is still the out-of-the-box persistence layer for quick prototyping, but
some workflows (rate limiting, foreign keys, concurrent writes) behave more like
production when backed by Postgres. This guide walks through spinning up a
Dockerized Postgres instance for local development and testing without touching
the global Makefile or architecture docs.

## When to Use This Setup

- Reproducing rate-limit or locking issues that are hidden by SQLite
- Exercising Alembic migrations against the same engine used in production
- Running integration tests that rely on stricter foreign-key enforcement
- Validating Next.js admin flows that create many concurrent sessions

## 1. Prepare Environment Variables

```bash
cp .env.postgres.example .env.postgres
# adjust passwords/ports if desired
```

The template defines:

- `MED13_POSTGRES_*` values consumed by Docker Compose
- `DATABASE_URL` (`postgresql+psycopg2://...`) for all synchronous code paths
- `ASYNC_DATABASE_URL` (`postgresql+asyncpg://...`) for the async auth stack
- `ALEMBIC_DATABASE_URL` so migrations pick up the same connection string

> Keep `.env.postgres` out of git; it is already ignored via `.gitignore`.

## 2. Start the Database Container

```bash
make docker-postgres-up
```

The Makefile copies the template if needed and runs `docker compose` with the
correct env file. The compose file provisions a Postgres 16 instance backed by
a persistent Docker volume (`med13-postgres-data`). Use `make docker-postgres-destroy`
when you need a clean slate.

## 3. Apply Database Migrations

Export the env vars (or prefix each command) so Alembic targets Postgres:

```bash
set -a && source .env.postgres && set +a
alembic upgrade head
```

You only need to re-run migrations when models change.

## 4. Run the Stack Against Postgres

`make docker-postgres-up` drops a `.postgres-active` flag so standard commands
automatically target Postgres and run migrations up front:

```bash
make run-local           # FastAPI backend on port 8080 (auto Postgres)
make run-web             # Next.js admin (auto Postgres + seeding)
make test                # Pytest suite against Postgres
# Alembic migrations run automatically before each command when Postgres is active.
# For explicit control:
make run-local-postgres  # Force Postgres even if flag disabled
make postgres-cmd CMD="alembic upgrade head"
```

Any script that relies on `src/database/session` or the dependency container now
reads the Postgres URLs through the shared resolver.

### Resetting Data

```bash
make docker-postgres-destroy
make docker-postgres-up
alembic upgrade head
```

### Troubleshooting

- **Cannot connect to server**: Ensure the container is healthy
  (`docker ps --filter name=med13-postgres --format '{{.Status}}'`).
- **Role/password errors**: Update `.env.postgres` and restart the container to
  recreate the database, or `psql` into the container to change credentials.
- **Driver missing**: Re-run `make setup-dev` so `psycopg2-binary` and `asyncpg`
  are installed from the updated dependency lists.
- **Migrations still hitting SQLite**: Confirm `ALEMBIC_DATABASE_URL` is set or
  that `DATABASE_URL` was exported before running Alembic.

## Command Cheat Sheet

```bash
make docker-postgres-up        # Start DB (creates .env.postgres if needed)
make docker-postgres-status    # Show container health
make docker-postgres-logs      # Tail logs (Ctrl+C to stop)
make docker-postgres-down      # Stop DB (data persists)
make docker-postgres-destroy   # Stop DB and wipe data volume
make postgres-disable          # Keep DB running but revert to SQLite defaults
```

With this workflow in place you can hop between SQLite (default) and Postgres
simply by toggling the Postgres helper targets—no manual env exports needed.
