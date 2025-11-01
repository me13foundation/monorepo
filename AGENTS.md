# Repository Guidelines

## Project Structure & Module Organization
Application code sits under `src/`, with `main.py` wiring the FastAPI app, `routes/` defining API endpoints, `models/` housing Pydantic schemas, `services/` implementing business logic, and `database/` configuring the SQLAlchemy session. Automated jobs and background docs live in `docs/`, while request fixtures and regression checks belong in `tests/`. Keep deploy assets (`Dockerfile`, `Procfile`, `Makefile`) at the project root and mirror existing directory conventions when adding features.

## Build, Test, and Development Commands
Use `make setup-dev` for a clean Python 3.11 virtualenv and dependency install. Run `make run-local` to start the API on port 8080, or `make run-dash` when working on the curation UI. `make all` executes the full quality gate (format, lint, type-check, tests) and is the pre-commit standard. For focused work, reach for `make format`, `make lint`, `make type-check`, and `make test`.

## Coding Style & Naming Conventions
Follow Black formatting with 4-space indentation and limit lines to 88 characters. Static analysis relies on Ruff, Flake8, and MyPy in strict mode—address warnings instead of suppressing them. Name modules and files with snake_case, reserve CamelCase for Pydantic models, and keep FastAPI route functions descriptive (e.g., `get_resources`). Add docstrings for public endpoints and services when behavior is non-obvious.

## Testing Guidelines
Pytest backs the test suite; add new tests under `tests/` using the `test_<feature>.py` pattern. Target high-value scenarios (positive, edge, and failure paths) and prefer factory helpers over fixtures embedded in tests. Run `make test` during development and `make test-cov` to confirm coverage holds steady—flag any major coverage drops in your pull request.

## Commit & Pull Request Guidelines
Commits follow Conventional Commit prefixes (`feat:`, `docs:`, `fix:`) as seen in the existing history; group related changes and keep messages in imperative voice. Before opening a PR, ensure `make all` passes locally and summarize the change, linked issue, data migrations, and manual verification steps. Include screenshots or curl examples when modifying endpoints, and call out any follow-up work so reviewers can plan next iterations.

## Security & Compliance Checks
Security tooling runs via `make security-audit`, surfacing results from Safety, Bandit, and pip-audit; address critical findings before merge. When dependencies move, update both `requirements.txt` and `requirements-dev.txt`, then rerun the security suite. Never commit secrets—use Cloud Run or GCP Secret Manager and document configuration updates in `docs/infra.md`.
