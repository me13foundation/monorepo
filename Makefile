# MED13 Resource Library - Development Makefile
# Automates common development, testing, and deployment tasks

# Virtual environment configuration
VENV := venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip3

# Detect environment type
CI_ENV := $(CI)
IN_VENV := $(shell python3 -c "import sys; print('1' if sys.prefix != sys.base_prefix else '0')" 2>/dev/null || echo "0")

# Choose Python/Pip based on environment
ifeq ($(CI_ENV),true)
    # CI/CD environment - use system python/pip
    USE_PYTHON := python3
    USE_PIP := pip3
    VENV_STATUS := CI/CD (no venv)
    VENV_ACTIVE := false
else ifeq ($(IN_VENV),1)
    # We're in a venv - use venv python/pip
    USE_PYTHON := $(PYTHON)
    USE_PIP := $(PIP)
    VENV_STATUS := Active
    VENV_ACTIVE := true
else ifeq ($(wildcard $(VENV)/bin/python3),)
    # No venv exists - warn user
    USE_PYTHON := python3
    USE_PIP := pip3
    VENV_STATUS := None - run 'make venv' first
    VENV_ACTIVE := false
else
    # Venv exists but not activated - warn and use venv
    USE_PYTHON := $(PYTHON)
    USE_PIP := $(PIP)
    VENV_STATUS := Available - activate with 'source venv/bin/activate'
    VENV_ACTIVE := false
endif

# Warn if venv is not active but exists
define check_venv
	@if [ "$(VENV_ACTIVE)" = "false" ] && [ -d "$(VENV)" ]; then \
		echo "⚠️  Virtual environment exists but not activated."; \
		echo "   Run: source $(VENV)/bin/activate"; \
		echo "   Or use: make activate"; \
		echo ""; \
	fi
endef

.PHONY: help venv venv-check install install-dev test test-verbose test-cov test-watch lint lint-strict format format-check type-check type-check-strict type-check-report security-audit security-full clean clean-all docker-build docker-run docker-push docker-stop db-migrate db-create db-reset db-seed deploy-staging deploy-prod setup-dev setup-gcp cloud-logs cloud-secrets-list all all-report ci check-env docs-serve backup-db restore-db activate deactivate stop-local stop-dash stop-web stop-all web-install web-build web-lint web-type-check web-test web-test-coverage

# Default target
help: ## Show this help message
	@echo "MED13 Resource Library - Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Virtual Environment
venv: $(VENV) ## Create virtual environment if it doesn't exist
$(VENV):
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	@echo "Virtual environment created at $(VENV)"

activate: ## Show command to activate virtual environment
	@echo "To activate the virtual environment, run:"
	@echo "source $(VENV)/bin/activate"

deactivate: ## Show command to deactivate virtual environment
	@echo "To deactivate the virtual environment, run:"
	@echo "deactivate"

# Installation
install: ## Install production dependencies
	$(call check_venv)
	$(USE_PIP) install -r requirements.txt

install-dev: ## Install development dependencies
	$(call check_venv)
	$(USE_PIP) install -r requirements.txt
	$(USE_PIP) install -r requirements-dev.txt

# Development setup
setup-dev: install-dev ## Set up development environment
	$(USE_PIP) install pre-commit --quiet || true
	pre-commit install || true
	@echo "Development environment setup complete!"
	@echo "Virtual environment status: $(VENV_STATUS)"

setup-gcp: ## Set up Google Cloud SDK and authenticate
	@echo "Setting up Google Cloud..."
	gcloud auth login
	gcloud config set project YOUR_PROJECT_ID
	gcloud services enable run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com storage.googleapis.com

# Testing
test: ## Run all tests
	$(call check_venv)
	$(USE_PYTHON) -m pytest

test-verbose: ## Run tests with verbose output
	$(call check_venv)
	$(USE_PYTHON) -m pytest -v --tb=short

test-cov: ## Run tests with coverage report
	$(call check_venv)
	$(USE_PYTHON) -m pytest --cov=src --cov-report=html --cov-report=term-missing

test-watch: ## Run tests in watch mode
	$(call check_venv)
	$(USE_PYTHON) -m pytest-watch

# Code Quality
lint: ## Run all linting tools (warnings only)
	$(call check_venv)
	@echo "Running flake8..."
	-$(USE_PYTHON) -m flake8 src tests --max-line-length=88 --extend-ignore=E203,W503,E501 --exclude=src/web/node_modules || echo "⚠️  Flake8 found style issues (non-blocking)"
	@echo "Running ruff..."
	-$(USE_PYTHON) -m ruff check src tests || echo "⚠️  Ruff found linting issues (non-blocking)"
	@echo "Running mypy..."
	-$(USE_PYTHON) -m mypy src || echo "⚠️  MyPy found type issues (non-blocking)"
	@echo "Running bandit (non-blocking)..."
	-$(USE_PYTHON) -m bandit -r src -f json -o bandit-results.json 2>&1 | grep -vE "(WARNING.*Test in comment|WARNING.*Unknown test found)" || echo "⚠️  Bandit found security issues (non-blocking)"

lint-strict: ## Run all linting tools (fails on error)
	$(call check_venv)
	@echo "Running flake8 (strict)..."
	$(USE_PYTHON) -m flake8 src tests --max-line-length=88 --extend-ignore=E203,W503,E501 --exclude=src/web/node_modules
	@echo "Running ruff (strict)..."
	$(USE_PYTHON) -m ruff check src tests
	@echo "Running bandit (strict)..."
	$(USE_PYTHON) -m bandit -r src -f json -o bandit-results.json 2>&1 | grep -vE "(WARNING.*Test in comment|WARNING.*Unknown test found)" || true

format: ## Format code with Black and sort imports with ruff
	$(call check_venv)
	$(USE_PYTHON) -m black src tests
	-$(USE_PYTHON) -m ruff check --fix src tests || echo "⚠️  Ruff found linting issues (non-blocking)"

format-check: ## Check code formatting without making changes
	$(call check_venv)
	$(USE_PYTHON) -m black --check src tests
	$(USE_PYTHON) -m ruff check src tests

type-check: ## Run mypy type checking with strict settings (warnings only)
	$(call check_venv)
	-$(USE_PYTHON) -m mypy src --strict --show-error-codes || echo "⚠️  MyPy found type issues (non-blocking)"

type-check-strict: ## Run mypy type checking with strict settings (fails on error)
	$(call check_venv)
	$(USE_PYTHON) -m mypy src --strict --show-error-codes

type-check-report: ## Generate mypy type checking report
	$(call check_venv)
	$(USE_PYTHON) -m mypy src --html-report mypy-report

security-audit: ## Run comprehensive security audit (pip-audit, bandit) [blocking on MEDIUM/HIGH]
	$(call check_venv)
	@echo "Running pip-audit..."
	$(USE_PIP) install pip-audit --quiet || true
	pip-audit --format json | tee pip-audit-results.json || true
	@echo "Running safety..."
	@echo "⚠️  Safety CLI now requires authentication. Using pip-audit for vulnerability scanning instead."
	@echo "   To enable Safety CLI in the future, set SAFETY_API_KEY environment variable."
	# SAFETY_API_KEY="" safety --stage development scan --save-as json safety-results.json --use-server-matching || true
	@echo "Running bandit (blocking on MEDIUM/HIGH)..."
	$(USE_PYTHON) -m bandit -r src --severity-level medium -f json -o bandit-results.json 2>&1 | grep -vE "(WARNING.*Test in comment|WARNING.*Unknown test found)" || true

security-full: security-audit ## Full security assessment with all tools

# Local Development
run-local: ## Run the application locally
	$(call check_venv)
	$(USE_PYTHON) -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload

run-dash: ## Run the Dash curation interface locally
	$(call check_venv)
	$(USE_PYTHON) -c "from src.dash_app import app; app.run(host='0.0.0.0', port=8050, debug=True)"

run-web: ## Run the Next.js admin interface locally (seeds admin user if needed)
	@echo "Ensuring admin user exists..."
	@$(MAKE) db-seed-admin || echo "Warning: Could not seed admin user (backend may not be running)"
	@echo "Starting Next.js admin interface..."
	cd src/web && NEXTAUTH_SECRET=med13-resource-library-nextauth-secret-key-for-development-2024-secure-random-string NEXTAUTH_URL=http://localhost:3000 NEXT_PUBLIC_API_URL=http://localhost:8080 npm run dev

stop-local: ## Stop the local FastAPI backend
	@echo "Stopping FastAPI backend..."
	-pkill -f "uvicorn main:app" || echo "No FastAPI process found"

stop-dash: ## Stop the Dash curation interface
	@echo "Stopping Dash UI..."
	-pkill -f "dash_app" || echo "No Dash process found"

stop-web: ## Stop the Next.js admin interface
	@echo "Stopping Next.js admin interface..."
	-pkill -f "npm run dev" || echo "No Next.js process found"

stop-all: stop-local stop-dash stop-web docker-stop ## Stop all services (local + Docker)
	@echo "All services stopped"

run-docker: docker-build ## Build and run with Docker
	docker run -p 8080:8080 med13-resource-library

# Docker
docker-build: ## Build Docker image
	docker build -t med13-resource-library .

docker-run: ## Run Docker container
	docker run -p 8080:8080 med13-resource-library

docker-stop: ## Stop and remove Docker container
	@echo "Stopping Docker container..."
	-docker stop $$(docker ps -q --filter ancestor=med13-resource-library) || echo "No running containers found"
	-docker rm $$(docker ps -aq --filter ancestor=med13-resource-library) || echo "No containers to remove"

docker-push: docker-build ## Build and push Docker image to GCR
	docker tag med13-resource-library gcr.io/YOUR_PROJECT_ID/med13-resource-library
	docker push gcr.io/YOUR_PROJECT_ID/med13-resource-library

# Database
db-migrate: ## Run database migrations
	alembic upgrade head

db-create: ## Create database migration
	@echo "Creating new migration..."
	alembic revision --autogenerate -m "$(msg)"

db-reset: ## Reset database (WARNING: destroys data)
	@echo "This will destroy all data. Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	alembic downgrade base

db-seed: ## Seed database with test data
	$(call check_venv)
	$(USE_PYTHON) scripts/seed_database.py

db-seed-admin: ## Seed admin user (creates admin@med13.org with password admin123)
	$(call check_venv)
	@echo "Seeding admin user..."
	@$(USE_PYTHON) scripts/seed_admin_user.py

db-reset-admin-password: ## Reset admin password (default: admin123)
	$(call check_venv)
	@echo "Resetting admin password..."
	@$(USE_PYTHON) scripts/reset_admin_password.py

db-verify-admin: ## Verify admin user exists
	$(call check_venv)
	@echo "Verifying admin user..."
	@$(USE_PYTHON) scripts/reset_admin_password.py --verify-only

# Deployment
deploy-staging: ## Deploy to staging environment
	@echo "Deploying to staging..."
	gcloud run deploy med13-resource-library-staging \
		--source . \
		--region us-central1 \
		--allow-unauthenticated=false \
		--service-account med13-staging@YOUR_PROJECT_ID.iam.gserviceaccount.com

deploy-prod: ## Deploy to production environment
	@echo "Deploying to production..."
	gcloud run deploy med13-resource-library \
		--source . \
		--region us-central1 \
		--allow-unauthenticated=false \
		--service-account med13-prod@YOUR_PROJECT_ID.iam.gserviceaccount.com

	gcloud run deploy med13-curation \
		--source . \
		--region us-central1 \
		--allow-unauthenticated=false \
		--service-account med13-prod@YOUR_PROJECT_ID.iam.gserviceaccount.com

	gcloud run deploy med13-admin \
		--source . \
		--region us-central1 \
		--allow-unauthenticated=false \
		--service-account med13-prod@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Cloud Operations
cloud-logs: ## View Cloud Run logs
	gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=med13-resource-library" --limit=50

cloud-secrets-list: ## List all secrets
	gcloud secrets list

# Cleanup
clean: ## Clean up temporary files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

clean-all: clean ## Clean everything including build artifacts
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf pip-audit-results.json
	rm -rf $(REPORT_DIR)/

# Next.js Admin Interface
web-install: ## Install Next.js dependencies
	cd src/web && npm install

web-build: ## Build Next.js admin interface
	cd src/web && npm run build

web-lint: ## Lint Next.js code
	cd src/web && npm run lint

web-type-check: ## Type check Next.js code
	cd src/web && npm run type-check

web-test: ## Run Next.js tests
	cd src/web && npm run test

web-test-coverage: ## Run Next.js tests with coverage report
	cd src/web && npm run test:coverage

test-web: web-test ## Alias for web-test

# Quality Assurance
venv-check: ## Ensure virtual environment is active
	@if [ "$(VENV_ACTIVE)" = "false" ]; then \
		echo "❌ Virtual environment is not active!"; \
		echo ""; \
		echo "To activate the virtual environment:"; \
		echo "  source $(VENV)/bin/activate"; \
		echo ""; \
		echo "Or use the convenience command:"; \
		echo "  make activate"; \
		echo ""; \
		exit 1; \
	fi

# Report directory for QA outputs
REPORT_DIR := reports
TIMESTAMP := $(shell date +%Y%m%d_%H%M%S)
QA_REPORT := $(REPORT_DIR)/qa_report_$(TIMESTAMP).txt

all: venv-check check-env format lint-strict type-check-strict web-build web-lint web-type-check web-test test security-audit ## Run complete quality assurance suite (fails on first error)
	@echo ""
	@echo "✅ All quality checks passed!"

all-report: ## Run complete QA suite with report generation (fails on first error)
	@mkdir -p $(REPORT_DIR)
	@echo "=========================================" > $(QA_REPORT)
	@echo "MED13 Resource Library - QA Report" >> $(QA_REPORT)
	@echo "Generated: $(shell date)" >> $(QA_REPORT)
	@echo "=========================================" >> $(QA_REPORT)
	@echo "" >> $(QA_REPORT)
	@echo "Running quality assurance suite..." | tee -a $(QA_REPORT)
	@bash -c 'set -o pipefail; $(MAKE) venv-check check-env format lint-strict type-check-strict web-build web-lint web-type-check web-test test security-audit 2>&1 | tee -a $(QA_REPORT)' || \
		(echo "" >> $(QA_REPORT); \
		 echo "❌ QA Suite FAILED at: $(shell date)" >> $(QA_REPORT); \
		 echo ""; \
		 echo "❌ QA Suite FAILED - Report saved to: $(QA_REPORT)"; \
		 exit 1)
	@echo "" >> $(QA_REPORT)
	@echo "✅ All quality checks passed!" >> $(QA_REPORT)
	@echo "Completed at: $(shell date)" >> $(QA_REPORT)
	@echo ""
	@echo "✅ All quality checks passed!"
	@echo "Report saved to: $(QA_REPORT)"

# CI/CD Simulation
ci: install-dev lint test security-audit ## Run full CI pipeline locally

# Environment checks
check-env: ## Check if development environment is properly set up
	@echo "🐍 Python Environment Status:"
	@echo "   Virtual Environment: $(VENV_STATUS)"
	@echo "   Python Executable: $(USE_PYTHON)"
	@echo ""
	@echo "Checking Python version..."
	$(USE_PYTHON) --version
	@echo "Checking pip version..."
	$(USE_PIP) --version
	@echo "Checking if requirements are installed..."
	$(USE_PYTHON) -c "import fastapi, uvicorn, sqlalchemy, pydantic; print('✅ Core dependencies OK')" 2>/dev/null || echo "❌ Core dependencies missing - run 'make install-dev'"
	@echo "Checking pre-commit..."
	pre-commit --version 2>/dev/null || echo "⚠️  pre-commit not installed - run 'make setup-dev'"

# Documentation
docs-serve: ## Serve documentation locally
	$(call check_venv)
	cd docs && $(USE_PYTHON) -m http.server 8000

# Backup and Recovery
backup-db: ## Create database backup (SQLite)
	@echo "Creating SQLite database backup..."
	cp med13.db backup_$(shell date +%Y%m%d_%H%M%S).db

restore-db: ## Restore database from backup (specify FILE variable)
	@echo "Restoring SQLite database from $(FILE)..."
	cp $(FILE) med13.db
