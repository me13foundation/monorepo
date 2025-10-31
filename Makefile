# MED13 Resource Library - Development Makefile
# Automates common development, testing, and deployment tasks

.PHONY: help install install-dev test test-verbose test-cov test-watch lint format format-check type-check type-check-report security-audit security-full clean clean-all docker-build docker-run docker-push db-migrate db-create db-reset db-seed deploy-staging deploy-prod setup-dev setup-gcp cloud-logs cloud-db-connect cloud-secrets-list ci check-env docs-serve backup-db restore-db

# Default target
help: ## Show this help message
	@echo "MED13 Resource Library - Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install production dependencies
	pip3 install -r requirements.txt

install-dev: ## Install development dependencies
	pip3 install -r requirements.txt
	pip3 install -r requirements-dev.txt

# Development setup
setup-dev: install-dev ## Set up development environment
	pip3 install pre-commit --quiet || true
	pre-commit install || true
	@echo "Development environment setup complete!"

setup-gcp: ## Set up Google Cloud SDK and authenticate
	@echo "Setting up Google Cloud..."
	gcloud auth login
	gcloud config set project YOUR_PROJECT_ID
	gcloud services enable run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com storage.googleapis.com

# Testing
test: ## Run all tests
	pytest

test-verbose: ## Run tests with verbose output
	pytest -v --tb=short

test-cov: ## Run tests with coverage report
	pytest --cov=src --cov-report=html --cov-report=term-missing

test-watch: ## Run tests in watch mode
	ptw

# Code Quality
lint: ## Run all linting tools (flake8, ruff, mypy, bandit)
	@echo "Running flake8..."
	flake8 src tests --max-line-length=88 --extend-ignore=E203,W503
	@echo "Running ruff..."
	ruff check src tests
	@echo "Running mypy..."
	mypy src
	@echo "Running bandit..."
	bandit -r src -f json -o bandit-results.json || true

format: ## Format code with Black and sort imports with ruff
	black src tests
	ruff check --fix src tests

format-check: ## Check code formatting without making changes
	black --check src tests
	ruff check src tests

type-check: ## Run mypy type checking with strict settings
	mypy src --strict --show-error-codes

type-check-report: ## Generate mypy type checking report
	mypy src --html-report mypy-report

security-audit: ## Run comprehensive security audit (pip-audit, safety, bandit)
	@echo "Running pip-audit..."
	pip3 install pip-audit --quiet || true
	pip-audit --format json | tee pip-audit-results.json || true
	@echo "Running safety..."
	pip3 install safety --quiet || true
	safety check --output json | tee safety-results.json || true
	@echo "Running bandit..."
	bandit -r src -f json -o bandit-results.json || true

security-full: security-audit ## Full security assessment with all tools

# Local Development
run-local: ## Run the application locally
	python3 -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload

run-dash: ## Run the Dash curation interface locally
	python3 -c "from src.dash_app import app; app.run_server(host='0.0.0.0', port=8050, debug=True)"

run-docker: docker-build ## Build and run with Docker
	docker run -p 8080:8080 med13-resource-library

# Docker
docker-build: ## Build Docker image
	docker build -t med13-resource-library .

docker-run: ## Run Docker container
	docker run -p 8080:8080 med13-resource-library

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
	python scripts/seed_database.py

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

# Cloud Operations
cloud-logs: ## View Cloud Run logs
	gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=med13-resource-library" --limit=50

cloud-db-connect: ## Connect to Cloud SQL database
	gcloud sql connect med13-db --user=med13_user

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

# CI/CD Simulation
ci: install-dev lint test security-audit ## Run full CI pipeline locally

# Environment checks
check-env: ## Check if development environment is properly set up
	@echo "Checking Python version..."
	python3 --version
	@echo "Checking pip version..."
	pip3 --version
	@echo "Checking if requirements are installed..."
	python3 -c "import fastapi, uvicorn, sqlalchemy, pydantic; print('Core dependencies OK')"
	@echo "Checking pre-commit..."
	pre-commit --version || echo "pre-commit not installed"

# Documentation
docs-serve: ## Serve documentation locally
	cd docs && python3 -m http.server 8000

# Backup and Recovery
backup-db: ## Create database backup
	@echo "Creating database backup..."
	gcloud sql export sql med13-db gs://med13-data-archive/backup-$(shell date +%Y%m%d-%H%M%S).sql \
		--database=med13_library

restore-db: ## Restore database from backup (specify FILE variable)
	@echo "Restoring database from $(FILE)..."
	gcloud sql import sql med13-db gs://med13-data-archive/$(FILE) \
		--database=med13_library
