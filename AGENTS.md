# MED13 Resource Library - AGENTS.md

**A README for AI coding agents working on the MED13 Resource Library.**

This document provides essential context and instructions for AI agents building on our biomedical data platform. Complementing the human-facing `README.md`, this file helps agents understand our Clean Architecture, domain-specific requirements, and development workflow.

## 📋 Project Overview

**MED13 Resource Library** is a curated biomedical data platform for MED13 genetic variants, phenotypes, and evidence. It implements Clean Architecture with:

- **Domain**: MED13-specific business logic and validation rules
- **Architecture**: FastAPI backend with a Next.js admin interface (Dash UI sunset in favor of Next.js)
- **Tech Stack**: Python 3.12+, TypeScript, PostgreSQL, Clean Architecture patterns
- **Purpose**: Provide researchers and administrators with reliable, type-safe biomedical data management

**Key Characteristics:**
- **Healthcare Domain**: Strict data integrity and privacy requirements
- **Next.js-Only UI**: The Dash curation client has been retired; the admin UI is the canonical interface
- **Type Safety First**: 100% MyPy compliance, Pydantic validation
- **Clean Architecture**: Domain-driven design with clear layer separation

## 🤖 Agent-Specific Instructions

**How AI agents should work with this codebase:**

### Code Generation Guidelines
- **Always use Clean Architecture layers**: Domain logic goes in `/domain`, UI logic in `/presentation`
- **Maintain type safety**: Never use `Any`, always provide proper type annotations
- **Follow biomedical domain rules**: Respect MED13-specific validation and business logic
- **Use Pydantic models**: All data structures should be Pydantic BaseModel subclasses
- **Implement proper error handling**: Use domain-specific exceptions and validation

### File Organization Rules
- **New features**: Follow existing module structure (`/domain`, `/application`, `/infrastructure`)
- **API endpoints**: Add to `/routes` with proper FastAPI router patterns
- **Database changes**: Create Alembic migrations in `/alembic/versions`
- **UI components**: Implement in the Next.js app (`/src/web`) with shared typed contracts from the backend

### Testing Requirements
- **Unit tests**: Required for all domain logic and services
- **Integration tests**: Required for API endpoints and repository operations
- **Type checking**: All code must pass MyPy strict mode
- **Coverage**: Maintain >85% test coverage for business logic

### Security Considerations
- **Never commit PHI**: No protected health information in code or tests
- **Input validation**: All user inputs validated through Pydantic models
- **Authentication**: Use existing auth patterns for new endpoints
- **Audit logging**: Log all data access and modifications

## 🔧 Build & Development Commands

**Essential commands for AI agents to set up and work with the codebase:**

### Environment Setup
```bash
make setup-dev          # Create Python 3.12 venv + install dependencies
source venv/bin/activate # Activate virtual environment
```

### Development Servers
```bash
make run-local          # Start FastAPI backend (port 8080)
make run-web            # Start Next.js admin interface (port 3000)
```

### Quality Assurance
```bash
make all                # Full quality gate (format, lint, type-check, tests)
make format            # Black + Ruff formatting
make lint              # Ruff + Flake8 linting
make type-check        # MyPy static analysis
make test              # Pytest execution
make test-cov          # Coverage reporting
```

### Database Operations
```bash
alembic revision --autogenerate -m "Add new table"  # Create migration
alembic upgrade head                                 # Apply migrations
```

## 🏗️ Strong Engineering Architecture

### Clean Architecture Principles
The MED13 Resource Library implements a **Clean Architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 FastAPI REST API • Next.js UI           │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │             Application Services & Use Cases            │ │
│  │  • SourceManagementService • TemplateService            │ │
│  │  • ValidationService • IngestionSchedulingService      │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 Business Logic & Entities               │ │
│  │  • UserDataSource • SourceTemplate • IngestionJob      │ │
│  │  • Domain Services • Value Objects • Business Rules     │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │             External Concerns & Adapters               │ │
│  │  • SQLAlchemy Repositories • API Clients               │ │
│  │  • File Storage • Message Queues • External Services   │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Architectural Features
- **Domain-Driven Design (DDD)**: Business logic isolated from technical concerns
- **Dependency Inversion**: Interfaces in domain, implementations in infrastructure
- **SOLID Principles**: Single responsibility, open/closed, Liskov substitution, interface segregation, dependency inversion
- **Hexagonal Architecture**: Ports & adapters pattern for external dependencies
- **CQRS Pattern**: Separate command and query responsibilities where appropriate

### Data Sources Module Architecture
The recently implemented Data Sources module demonstrates our architectural strength:

```
Phase 1-3 Complete: ✅
├── Domain Entities (Pydantic models with business logic)
├── Application Services (Use cases & orchestration)
├── Infrastructure Repositories (SQLAlchemy implementations)
├── Presentation Layer (Next.js admin interface)
└── Quality Assurance (Type safety, testing, validation)
```

## 📁 Monorepo Structure & Organization

**MED13 uses a monorepo with clear service boundaries:**

```
med13-resource-library/
├── src/                          # Shared Python backend
│   ├── domain/                  # Business logic (shared)
│   ├── application/             # Use cases (shared)
│   ├── infrastructure/          # External adapters (shared)
│   ├── presentation/            # Reserved for future UI adapters
│   ├── web/                     # Next.js admin interface
│   └── routes/                  # API endpoints
├── docs/                         # Documentation
├── tests/                        # Backend tests
├── node_js_migration_prd.md      # Next.js migration plan
├── data_sources_plan.md          # Data sources specification
└── Makefile                     # Build orchestration
```

**Service Boundaries:**
- **FastAPI Backend** (`src/`): Core business logic, shared across services
- **Next.js Admin UI** (`src/web/`): Administrative and research workflows (Dash UI retired)
- **Template Catalog**: `/admin/templates` endpoints expose reusable data source templates for the Next.js admin experience

**Cross-Service Dependencies:**
- The Next.js UI consumes the FastAPI REST API
- Shared TypeScript types generated from Pydantic models
- Common domain entities and business rules

## 🔄 Workflow & CI/CD Instructions

### Commit Message Conventions
**Use conventional commits for automated deployments:**
```bash
feat(api): add data source management endpoints
fix(web): resolve table sorting bug in admin UI
docs: update API documentation
ci: update deployment configuration
```

### Pull Request Workflow
**Standard PR process for AI-generated changes:**
1. **Branch naming**: `feature/`, `fix/`, `docs/`, `ci/`
2. **PR title**: Follow conventional commit format
3. **PR description**: Include what, why, and testing approach
4. **Required checks**: `make all` must pass
5. **Review**: At least one maintainer review required

### CI/CD Pipeline
**Automated quality gates:**
```bash
# Pre-commit (local)
make all

# CI Pipeline
├── Code formatting (Black, Ruff)
├── Linting (Ruff, Flake8, MyPy)
├── Security scanning (Bandit, Safety)
├── Testing (Pytest with coverage)
└── Deployment (Cloud Run)
```

### Deployment Strategy
**Multi-service independent deployments:**
```bash
# Backend deployment
gcloud run deploy med13-api --source .

# Future: Next.js deployment
gcloud run deploy med13-admin --source .
```

## 🧪 Testing Instructions

**How AI agents should write and run tests:**

### Test Frameworks & Structure
- **Unit Tests**: `tests/unit/` - Domain logic, services, utilities
- **Integration Tests**: `tests/integration/` - API endpoints, repositories, external services
- **E2E Tests**: `tests/e2e/` - Complete user workflows
- **Type Tests**: MyPy validation for all code

### Test Execution
```bash
# Run specific test types
make test              # All tests
pytest tests/unit/     # Unit tests only
pytest tests/integration/  # Integration tests only
pytest tests/e2e/      # End-to-end tests

# With coverage
make test-cov          # Coverage report
```

### Test Writing Guidelines
- **File naming**: `test_<feature>.py`
- **Test isolation**: Each test independent, no shared state
- **Mock external deps**: Use `tests/types/mocks.py` for repositories
- **Type safety**: All test fixtures properly typed
- **Coverage target**: >85% for business logic

### Schema Validation Testing
```python
# Always test Pydantic models
def test_data_source_validation():
    # Test valid data
    source = UserDataSource(
        id=UUID(), owner_id=UUID(),
        name="Test Source", source_type=SourceType.API
    )
    assert source.name == "Test Source"

    # Test invalid data
    with pytest.raises(ValidationError):
        UserDataSource(name="")  # Empty name should fail
```

## 💅 Code Style & Conventions

**Language and formatting standards for AI-generated code:**

### Python Standards
- **Version**: Python 3.12+ required
- **Formatting**: Black with 88-character line length
- **Linting**: Ruff + Flake8 (strict mode, no suppressions)
- **Type Checking**: MyPy strict mode (no `Any` types)

### Naming Conventions
- **Modules**: `snake_case` (e.g., `data_source_service.py`)
- **Classes**: `CamelCase` (e.g., `UserDataSource`, `SourceTemplate`)
- **Functions/Methods**: `snake_case` (e.g., `create_source()`, `validate_config()`)
- **Constants**: `UPPER_CASE` (e.g., `DEFAULT_TIMEOUT = 30`)
- **Variables**: `snake_case` (e.g., `source_config`, `user_permissions`)

### Import Organization
```python
# Standard library imports
from typing import Dict, List, Optional
from uuid import UUID

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

# Local imports (absolute)
from src.domain.entities.user_data_source import UserDataSource
from src.application.services.source_management_service import SourceManagementService
```

### Docstring Standards
```python
def create_data_source(
    self, request: CreateSourceRequest
) -> UserDataSource:
    """
    Create a new data source with validation.

    Args:
        request: Validated creation request with all required fields

    Returns:
        The newly created UserDataSource entity

    Raises:
        ValueError: If source configuration is invalid
        PermissionError: If user lacks creation permissions
    """
```

### Domain-Specific Patterns
- **Entity Creation**: Always validate through domain services, not direct constructors
- **Error Handling**: Use domain-specific exceptions, not generic ones
- **Validation**: All business rules enforced at domain layer
- **Dependencies**: Use dependency injection, not direct instantiation

## 🛡️ Type Safety Excellence

### Comprehensive Type System
The MED13 Resource Library implements **100% MyPy compliance** with strict type checking. See `docs/type_examples.md` for detailed patterns and best practices.

#### Core Type Safety Features
- **Strict MyPy Configuration**: No `Any` types, comprehensive coverage
- **Pydantic Models**: Runtime type validation with rich error messages
- **Generic Types**: Proper typing for collections and containers
- **Protocol Classes**: Structural typing for interfaces
- **Type Guards**: Runtime type checking functions

#### Type Safety Patterns (from `docs/type_examples.md`)

**Typed Test Fixtures**:
```python
from tests.types.fixtures import create_test_gene, TEST_GENE_MED13

# Create typed test data
test_gene = create_test_gene(
    gene_id="CUSTOM001",
    symbol="CUSTOM",
    name="Custom Test Gene"
)
```

**Mock Repository Patterns**:
```python
from tests.types.mocks import MockGeneRepository

# Type-safe mocking
mock_repo = MockGeneRepository(test_genes)
service = GeneDomainService(mock_repo)
```

**API Response Validation**:
```python
from src.infrastructure.validation.api_response_validator import APIResponseValidator
from src.type_definitions.external_apis import ClinVarSearchValidationResult

validation: ClinVarSearchValidationResult = APIResponseValidator.validate_clinvar_search_response(raw_data)
if validation["is_valid"] and validation["sanitized_data"]:
    typed_response = validation["sanitized_data"]
```

### Type Safety Benefits
- **Runtime Safety**: Pydantic validates all input/output at runtime
- **IDE Support**: Full autocomplete and refactoring capabilities
- **Documentation**: Types serve as living documentation
- **Testing**: Type-safe mocks and fixtures reduce test brittleness
- **Maintenance**: Refactoring is safe and reliable

## 📋 Development Standards

### Project Structure & Module Organization
```
src/
├── main.py                     # FastAPI app wiring
├── routes/                     # API endpoint definitions
├── domain/                     # Business logic & entities
│   ├── entities/              # Domain models (Pydantic)
│   ├── repositories/          # Repository interfaces
│   └── services/              # Domain services
├── application/               # Application services & use cases
│   └── services/              # Application layer services
├── infrastructure/            # External concerns & adapters
│   ├── repositories/          # Repository implementations
│   ├── mappers/              # Data mapping
│   └── validation/           # External API validation
├── models/                    # Database models (SQLAlchemy)
├── web/                       # Next.js admin interface
tests/                          # Test suites
docs/                          # Documentation
```

### Build, Test, and Development Commands
- `make setup-dev`: Clean Python 3.12 virtualenv + dependencies
- `make run-local`: Start FastAPI on port 8080
- `make run-web`: Start Next.js admin interface on port 3000
- `make all`: Full quality gate (format, lint, type-check, tests)
- `make format`: Black + Ruff formatting
- `make lint`: Ruff + Flake8 linting
- `make type-check`: MyPy static analysis
- `make test`: Pytest execution
- `make test-cov`: Coverage reporting

### Coding Style & Naming Conventions
- **Formatting**: Black with 88 char line length
- **Linting**: Ruff + Flake8 (strict mode, no suppressions)
- **Naming**:
  - `snake_case` for modules, functions, variables
  - `CamelCase` for Pydantic models and classes
  - `UPPER_CASE` for constants
- **Docstrings**: Required for public APIs and complex logic
- **Imports**: Absolute imports, grouped by standard library → third-party → local

### Testing Guidelines
- **Framework**: Pytest with comprehensive fixtures
- **Coverage Target**: >85% with focus on business logic
- **Test Structure**: `tests/test_<feature>.py`
- **Test Types**: Unit, integration, E2E, property-based
- **Mocking**: Type-safe mocks from `tests.types.mocks`
- **Coverage**: `make test-cov` for verification

### Quality Assurance Pipeline
```bash
make all                    # Complete quality gate
├── make format            # Code formatting (Black + Ruff)
├── make lint              # Code quality (Ruff + Flake8)
├── make type-check        # Type safety (MyPy strict)
└── make test              # Test execution (Pytest)
```

### Security & Compliance
- **Static Analysis**: Bandit, Safety, pip-audit
- **Dependency Scanning**: `make security-audit`
- **Secrets Management**: GCP Secret Manager for production
- **Input Validation**: Pydantic models prevent injection attacks
- **Rate Limiting**: Configurable API rate limits
- **CORS Protection**: Properly configured cross-origin policies

## 🚀 Recent Achievements

### Data Sources Module (Phase 1-3 Complete)
- **Domain Modeling**: Full Pydantic entities with business rules
- **Application Services**: Clean use case orchestration
- **Infrastructure**: SQLAlchemy repositories with proper separation
- **UI/UX**: Next.js admin experience with shadcn/ui components
- **Quality Assurance**: Type-safe throughout, ready for production

### Architecture Improvements
- **Clean Architecture**: Proper layer separation implemented
- **Type Safety**: 100% MyPy compliance maintained
- **Testing**: Comprehensive test suites with high coverage
- **CI/CD**: Automated quality gates and security scanning

## 📚 Key Documentation References

**Essential reading for AI agents:**

- `docs/type_examples.md`: Comprehensive type safety patterns and examples
- `docs/EngineeringArchitecture.md`: Detailed architectural roadmap and phase plans
- `data_sources_plan.md`: Complete Data Sources module specification
- `docs/node_js_migration_prd.md`: Next.js admin interface migration plan
- `docs/curator.md`: Researcher curation workflows and UI patterns
- `docs/goal.md`: Project mission and success criteria
- `docs/infra.md`: Infrastructure and deployment details

## 🎯 Development Philosophy

**"Build systems that are maintainable, testable, and evolvable. Type safety is not optional—it's foundational. Clean architecture enables confident refactoring and feature development."**

### Core Principles for AI Agents
- **First Principles**: Strip problems to core truths, challenge assumptions
- **Robust Solutions**: Always implement the most robust solution possible
- **Long-term Focus**: Design for maintainability and evolution over short-term gains
- **Quality First**: Never compromise on type safety or architectural principles

### Healthcare Domain Considerations
- **Patient Safety**: Medical data accuracy is critical - no shortcuts on validation
- **Privacy First**: HIPAA/compliance requirements built into every feature
- **Auditability**: Every data operation must be traceable and logged
- **Reliability**: 99.9%+ uptime requirements for healthcare systems

### AI Agent Guidelines
- **Context Awareness**: Always consider MED13's biomedical domain constraints
- **Type Safety**: Never use `Any` - proper typing prevents medical data errors
- **Testing**: Healthcare software requires extensive validation
- **Documentation**: Clear docs prevent medical misinterpretation
- **Security**: Healthcare data demands fortress-level security practices

---

**This AGENTS.md serves as your comprehensive guide to building on the MED13 Resource Library. Follow these patterns to create reliable, type-safe, healthcare-grade software.** 🏥✨
