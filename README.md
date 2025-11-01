# MED13 Resource Library (Phase 0) 🏥

A curated resource library for MED13 variants, phenotypes, and supporting evidence. Built with FastAPI, SQLite, and designed for Google Cloud Run deployment.

## 📋 Overview

Phase 0 creates a **FAIR-compliant knowledge base** aggregating validated MED13-related data from trusted biomedical sources. This preparatory phase establishes the foundation for Phase 1's knowledge graph integration.

### 🎯 Key Features
- **Curated Data**: Variants, phenotypes, publications, and evidence relationships
- **FAIR Compliance**: Findable, Accessible, Interoperable, Reusable data packaging
- **Open Access**: Built from CC0/CC-BY licensed biomedical resources
- **API-First**: REST/GraphQL endpoints for data access
- **Cloud-Native**: Serverless deployment with automated CI/CD

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Git
- Google Cloud SDK (for deployment)

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd med13-resource-library

# Set up development environment (creates venv automatically)
make setup-dev

# Run the API locally
make run-local

# Access the API at http://localhost:8080
```

### Environment Status Check

```bash
make check-env
```

## 📁 Project Structure

```
med13-resource-library/
├── src/                    # Source code
│   ├── main.py            # FastAPI application
│   ├── database/          # Database configuration
│   ├── models/            # Pydantic data models
│   └── routes/            # API endpoints
├── tests/                 # Test suite
├── docs/                  # Documentation
├── .github/workflows/     # CI/CD pipelines
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── Makefile              # Development automation
├── Procfile              # Cloud Run configuration
└── pytest.ini            # Test configuration
```

## 🛠️ Development Workflow

### Available Commands

```bash
# Environment Management
make venv              # Create virtual environment
make activate          # Show activation command
make check-env         # Check environment status

# Setup & Installation
make install           # Install production dependencies
make install-dev       # Install development dependencies
make setup-dev         # Complete development setup

# Development
make run-local         # Start FastAPI server
make run-dash          # Start Dash curation interface

# Code Quality
make lint              # Run all linters (flake8, ruff, mypy, bandit)
make format            # Auto-format code (Black + Ruff)
make type-check        # Type checking with mypy

# Testing
make test              # Run all tests
make test-cov          # Tests with coverage report
make test-verbose      # Verbose test output

# Database
make db-migrate        # Run database migrations
make db-create         # Create new migration
make db-reset          # Reset database (WARNING!)
make db-seed           # Seed with test data
make backup-db         # Backup SQLite database
make restore-db        # Restore from backup

# Security
make security-audit    # Run security scans

# CI/CD
make ci                # Run full CI pipeline locally

# Cloud Operations
make cloud-logs        # View Cloud Run logs
make cloud-secrets-list # List GCP secrets

# Documentation
make docs-serve        # Serve docs locally
```

### Smart Environment Detection

The Makefile automatically detects your environment:

- **Local Development**: Uses virtual environment when available
- **CI/CD**: Uses system Python for GitHub Actions compatibility
- **Cloud Run**: Works seamlessly in containerized production

### Example Workflow

```bash
# Fresh development setup
make setup-dev

# Make some changes, then:
make format            # Auto-format code
make lint              # Check code quality
make test              # Run tests
make type-check        # Verify types

# Deploy when ready
make deploy-staging    # Test deployment
make deploy-prod       # Production deployment
```

## 🗄️ Database

### Local Development
- **Database**: SQLite (`med13.db`)
- **ORM**: SQLAlchemy 2.0 with Alembic migrations
- **Setup**: Automatic file creation, zero configuration

### Production
- **Database**: SQLite (included in Cloud Run deployment)
- **Backup**: Manual file-based backups
- **Migration**: Alembic schema versioning

### Data Sources
- **ClinVar/ClinGen**: Variant interpretations and curation status
- **HPO**: Human Phenotype Ontology terms and hierarchies
- **PubMed/LitVar**: Literature references and variant links
- **OMIM/Orphanet**: Gene-disease associations
- **UniProt/GTEx**: Functional and expression metadata

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific tests
pytest tests/test_health.py -v

# Watch mode for development
make test-watch
```

## 🚀 Deployment

### Automated CI/CD
- **GitHub Actions**: Runs on push/PR and releases
- **Staging**: Automatic deployment on merged PRs
- **Production**: Deployment on published releases
- **Security**: Automated dependency scanning

### Cloud Run Configuration
- **Service**: `med13-resource-library` (production)
- **Staging**: `med13-resource-library-staging`
- **Source Deployment**: Uses `Procfile` configuration
- **Database**: SQLite file included in deployment

### Manual Deployment

```bash
# Deploy to staging
make deploy-staging

# Deploy to production (requires release)
make deploy-prod
```

## 🔒 Security & Quality

### Code Quality Gates
- **Linting**: Flake8, Ruff (import sorting, formatting)
- **Type Checking**: MyPy with strict settings
- **Formatting**: Black code formatter
- **Security**: Bandit security linter

### Dependency Security
- **Automated Scanning**: Safety and pip-audit
- **Vulnerability Checks**: Run in CI/CD pipeline
- **License Compliance**: All data sources verified

## 📚 Documentation

- **`docs/goal.md`**: Project objectives and data model
- **`docs/infra.md`**: Infrastructure setup and deployment guide
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following the established patterns
4. Run `make ci` to verify quality gates
5. Submit a pull request

### Development Standards
- **Code Style**: Black formatting, Ruff linting
- **Type Safety**: Full MyPy coverage with strict settings
- **Testing**: Comprehensive test suite with pytest
- **Documentation**: Clear docstrings and comments

## 📄 License

This project uses data from multiple biomedical sources. Refer to `docs/goal.md` for detailed licensing information and attribution requirements.

## 🆘 Support

- **Issues**: GitHub Issues for bugs and feature requests
- **Documentation**: See `docs/` directory for detailed guides
- **CI/CD**: Automated pipelines provide immediate feedback

---

**Phase 0: Building the Foundation for MED13 Research** 🔬
