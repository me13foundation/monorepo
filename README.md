# MED13 Resource Library 🏥

A comprehensive biomedical data platform for MED13 genetic variants, phenotypes, and evidence. Features a **three-tier architecture** with FastAPI backend, Next.js admin interface, and Dash curation tools. Built for Google Cloud Run deployment with enterprise-grade quality assurance.

**🚀 Currently in Phase 1: Next.js Admin Migration** - Transforming to a modern, scalable platform

## 📋 Overview

A **three-service architecture** biomedical data platform featuring Clean Architecture principles, type safety, and modern web interfaces. Currently implementing **Next.js admin interface migration** alongside existing FastAPI backend and Dash curation tools.

### 🏗️ Architecture

```
MED13 Resource Library
├── FastAPI Backend (med13-api)      # REST API & business logic
├── Next.js Admin (med13-admin)      # Modern admin dashboard
└── Dash Curation (med13-curation)   # Research curation workflows
```

### 🎯 Key Features
- **Three-Tier Architecture**: Independent scaling of admin, API, and curation services
- **Clean Architecture**: Domain-driven design with clear separation of concerns
- **Type Safety**: 100% MyPy compliance with shared TypeScript types
- **Modern Admin UI**: Next.js 14 with Tailwind CSS and shadcn/ui components
- **Comprehensive APIs**: REST endpoints with OpenAPI documentation
- **FAIR Compliance**: Findable, Accessible, Interoperable, Reusable data
- **Cloud-Native**: Multi-service Google Cloud Run deployment
- **Quality Assurance**: Enterprise-grade linting, testing, and security scanning

## 🚀 Quick Start

### Prerequisites
- **Python 3.12+** (FastAPI backend)
- **Node.js 18+** (Next.js admin interface)
- **Git** (version control)
- **Google Cloud SDK** (for deployment)

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd med13-resource-library

# Set up Python environment
make setup-dev

# Install Next.js dependencies
make web-install

# Run all services
make run-local    # Terminal 1: FastAPI backend (port 8080)
make run-web      # Terminal 2: Next.js admin (port 3000)
make run-dash     # Terminal 3: Dash curation (port 8050)

# Access the services
# - API Documentation: http://localhost:8080/docs
# - Admin Dashboard: http://localhost:3000/dashboard
# - Curation Interface: http://localhost:8050
```

### Environment Status Check

```bash
make check-env
```

## 📁 Project Structure

```
med13-resource-library/
├── src/                          # Backend source code
│   ├── main.py                  # FastAPI application entry point
│   ├── database/                # Database configuration
│   ├── models/                  # SQLAlchemy database models
│   ├── routes/                  # API endpoints (including /admin/*)
│   ├── domain/                  # Business logic & entities
│   ├── application/             # Use cases & services
│   ├── infrastructure/          # External adapters & repositories
│   ├── presentation/            # UI implementations
│   │   └── dash/               # Dash curation interface
│   └── shared/                 # Shared types between services
│       └── types/              # TypeScript type definitions
├── src/web/                     # Next.js admin interface
│   ├── app/                    # Next.js app router pages
│   ├── components/             # React components & UI
│   ├── lib/                    # Utilities and configurations
│   ├── types/                  # Frontend type definitions
│   ├── package.json            # Node.js dependencies
│   └── tailwind.config.ts      # Tailwind CSS configuration
├── tests/                      # Backend test suite
├── docs/                       # Documentation
├── .github/workflows/          # CI/CD pipelines
├── requirements.txt            # Python production dependencies
├── requirements-dev.txt        # Python development dependencies
├── Makefile                   # Development automation
├── Procfile                   # Cloud Run configuration
└── pytest.ini                 # Test configuration
```

## 🛠️ Development Workflow

### Available Commands

```bash
# Quality Assurance (Multi-Service)
make all               # Complete quality suite: Python + Next.js (recommended)

# Environment Management
make venv              # Create Python virtual environment
make activate          # Show activation command
make check-env         # Check environment status

# Setup & Installation
make install           # Install Python production dependencies
make install-dev       # Install Python development dependencies
make setup-dev         # Complete Python development setup
make web-install       # Install Next.js dependencies

# Development Servers
make run-local         # Start FastAPI backend (port 8080)
make run-web           # Start Next.js admin interface (port 3000)
make run-dash          # Start Dash curation interface (port 8050)

# Code Quality
make lint              # Python linting (flake8, ruff, mypy, bandit)
make format            # Python auto-format (Black + Ruff)
make type-check        # Python type checking with mypy
make web-lint          # Next.js linting
make web-type-check    # Next.js type checking

# Testing
make test              # Python tests
make test-cov          # Python tests with coverage
make test-verbose      # Python tests with verbose output
make web-test          # Next.js tests

# Building
make web-build         # Build Next.js for production

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
make ci                # Run full Python CI pipeline locally

# Cloud Operations
make cloud-logs        # View Cloud Run logs
make cloud-secrets-list # List GCP secrets

# Documentation
make docs-serve        # Serve docs locally
```

### Smart Environment Detection

The Makefile automatically detects your environment:

- **Local Development**: Uses Python venv + Node.js for full-stack development
- **CI/CD**: Uses system Python/Node.js for GitHub Actions compatibility
- **Cloud Run**: Multi-service containerized production deployment

### Multi-Service Development Workflow

```bash
# Initial setup
make setup-dev         # Python environment + dependencies
make web-install       # Next.js dependencies

# Development cycle - run before commit/push
make all               # Complete quality assurance (Python + Next.js)

# Individual quality checks
make format            # Python auto-format
make web-build         # Next.js build check
make lint              # Python linting
make web-lint          # Next.js linting
make type-check        # Python types
make web-type-check    # Next.js types
make test              # Python tests
make web-test          # Next.js tests

# Development servers (run in separate terminals)
make run-local         # FastAPI backend
make run-web           # Next.js admin UI
make run-dash          # Dash curation UI

# Production builds
make web-build         # Build Next.js for production

# Deploy when ready
make deploy-staging    # Test deployment (all services)
make deploy-prod       # Production deployment (all services)
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

### Backend Testing (Python)
```bash
# Run all Python tests
make test

# Run with coverage
make test-cov

# Run specific tests
pytest tests/test_health.py -v

# Watch mode for development
make test-watch

# Verbose output
make test-verbose
```

### Frontend Testing (Next.js)
```bash
# Run Next.js tests
make web-test

# Run with coverage
cd src/web && npm run test:coverage

# Watch mode for development
cd src/web && npm run test:watch
```

### Integration Testing
```bash
# Test API endpoints
curl -X GET "http://localhost:8080/admin/data-sources"
curl -X GET "http://localhost:8080/admin/stats"

# Test frontend connectivity
# Open http://localhost:3000/dashboard
# Verify data loads from API
```

### Quality Assurance Pipeline
```bash
# Run complete multi-service quality suite
make all

# This includes:
# - Python: format, lint, type-check, test, security
# - Next.js: build, lint, type-check, test
# - Integration: cross-service compatibility
```

## 🚀 Deployment

### Multi-Service Architecture
- **FastAPI Backend**: `med13-api` - Core business logic and APIs
- **Next.js Admin**: `med13-admin` - Administrative interface
- **Dash Curation**: `med13-curation` - Research curation workflows

### Automated CI/CD
- **GitHub Actions**: Multi-service pipeline with parallel builds
- **Staging**: Automatic deployment of all services on merged PRs
- **Production**: Independent service deployment on releases
- **Quality Gates**: Python + Next.js quality checks required
- **Security**: Automated dependency scanning for both ecosystems

### Cloud Run Services
- **med13-api**: FastAPI backend with admin endpoints
- **med13-api-staging**: Staging backend service
- **med13-admin**: Next.js admin interface
- **med13-admin-staging**: Staging admin service
- **med13-curation**: Dash curation interface
- **med13-curation-staging**: Staging curation service

### Deployment Commands

```bash
# Deploy individual services to staging
make deploy-staging    # Deploys all services to staging

# Deploy individual services to production
make deploy-prod       # Deploys all services to production

# Or deploy specific services (future enhancement)
# make deploy-api-prod
# make deploy-admin-prod
# make deploy-curation-prod
```

### Service URLs (Production)
- **API**: https://med13-api-[hash]-uc.a.run.app
- **Admin**: https://med13-admin-[hash]-uc.a.run.app
- **Curation**: https://med13-curation-[hash]-uc.a.run.app

## 🔒 Security & Quality

### Multi-Service Quality Gates
- **Python Backend**:
  - Linting: Flake8, Ruff (import sorting, formatting)
  - Type Checking: MyPy with strict settings
  - Formatting: Black code formatter
  - Security: Bandit security linter
- **Next.js Frontend**:
  - Linting: ESLint with Next.js config
  - Type Checking: TypeScript strict mode
  - Formatting: Prettier
  - Testing: Jest + React Testing Library

### Dependency Security
- **Python**: Safety and pip-audit automated scanning
- **Node.js**: npm audit and dependency checks
- **Vulnerability Checks**: CI/CD pipeline for both ecosystems
- **License Compliance**: All biomedical data sources verified

### Type Safety
- **100% MyPy Compliance**: Strict typing across Python codebase
- **Shared Type Definitions**: TypeScript types synced between services
- **Runtime Validation**: Pydantic models ensure data integrity

## 📚 Documentation

### Core Documentation
- **`docs/goal.md`**: Project objectives and biomedical data model
- **`docs/infra.md`**: Multi-service infrastructure and deployment guide
- **`docs/node_js_migration_prd.md`**: Next.js admin interface migration plan
- **`docs/admin_area.md`**: Research Spaces Management System PRD
- **`AGENTS.md`**: AI agent development guidelines and architecture
- **`docs/EngineeringArchitecture.md`**: Current state and growth strategy

### API Documentation
- **OpenAPI/Swagger**: http://localhost:8080/docs (when running)
- **Alternative Docs**: http://localhost:8080/redoc
- **Admin API**: `/admin/*` endpoints for data source management
- **Research Spaces API**: `docs/research-spaces-api.md` - Complete API reference for research spaces endpoints
- **Research Spaces Components**: `docs/research-spaces-components.md` - React component documentation

### Development Guides
- **`docs/type_examples.md`**: Type safety patterns and examples
- **`docs/curator.md`**: Researcher curation workflows
- **Makefile**: Comprehensive development automation reference

## 🤝 Contributing

### Development Workflow
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/your-feature`)
3. **Set up** multi-service environment:
   ```bash
   make setup-dev      # Python environment
   make web-install    # Next.js dependencies
   ```
4. **Develop** following established patterns
5. **Test** all services: `make all` (Python + Next.js quality gates)
6. **Submit** a pull request

### Development Standards

#### Python Backend
- **Code Style**: Black formatting, Ruff linting
- **Type Safety**: 100% MyPy compliance with strict settings
- **Testing**: Comprehensive pytest suite
- **Architecture**: Clean Architecture with domain-driven design

#### Next.js Frontend
- **Code Style**: ESLint, Prettier formatting
- **Type Safety**: TypeScript strict mode
- **Testing**: Jest + React Testing Library
- **UI/UX**: shadcn/ui components, Tailwind CSS

#### Multi-Service Requirements
- **Shared Types**: Consistent TypeScript types across services
- **API Contracts**: OpenAPI specification compliance
- **Integration Tests**: Cross-service compatibility verification
- **Documentation**: Clear docstrings, type hints, and API docs

## 📄 License

This project uses data from multiple biomedical sources. Refer to `docs/goal.md` for detailed licensing information and attribution requirements.

## 🆘 Support

- **Issues**: GitHub Issues for bugs and feature requests
- **Documentation**: See `docs/` directory for detailed guides
- **CI/CD**: Automated pipelines provide immediate feedback

---

**🚀 Phase 1: Next.js Admin Migration - Building Enterprise-Grade Multi-Service Architecture** 🏥✨

*FastAPI Backend • Next.js Admin • Dash Curation • Clean Architecture • Type Safety • Cloud-Native*
