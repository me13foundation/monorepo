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
- **STRICT TYPE SAFETY**: Never use `Any` - always provide proper type annotations
- **Clean Architecture layers**: Domain logic in `src/domain`, application services in `src/application`, API endpoints in `src/routes`, UI in `src/web` (Next.js); `src/presentation` is reserved
- **Pydantic models**: Use Pydantic BaseModel for domain entities and API schemas; use TypedDicts from `src/type_definitions/` for updates, JSON payloads, and API response shapes
- **Type definitions**: Use existing types from `src/type_definitions/` instead of creating new ones
- **Follow biomedical domain rules**: Respect MED13-specific validation and business logic
- **Implement proper error handling**: Use domain-specific exceptions and validation

### Type Management Rules
- **NEVER USE `Any`**: This is a strict requirement - use proper union types, generics, or specific types
- **Use existing types**: Check `src/type_definitions/` for existing TypedDict, Protocol, and union types
- **JSON types**: Use `JSONObject` and `JSONValue` (use `list[JSONValue]` for arrays)
- **External APIs**: Use validation results from `src/type_definitions/external_apis.py`
- **Update operations**: Use TypedDict classes like `GeneUpdate`, `VariantUpdate`, etc.
- **Test fixtures**: Use `tests/test_types/fixtures.py` and `tests/test_types/mocks.py` for typed test data
- **API responses**: Use `APIResponse` and `PaginatedResponse` from `src/type_definitions/common.py`

#### Type Definition Locations
- **Common types**: `src/type_definitions/common.py` (JSON, API responses, pagination)
- **Domain entities**: `src/domain/entities/` (Pydantic models)
- **External APIs**: `src/type_definitions/external_apis.py` (ClinVar, UniProt, etc.)
- **Update types**: `src/type_definitions/common.py` (GeneUpdate, VariantUpdate, etc.)
- **Test types**: `tests/test_types/` (fixtures, mocks, test data)

### File Organization Rules
- **New features**: Follow existing module structure (`/domain`, `/application`, `/infrastructure`)
- **API endpoints**: Add to `/routes` with proper FastAPI router patterns
- **Database changes**: Create Alembic migrations in `/alembic/versions`
- **UI components**: Implement in the Next.js app (`/src/web`) with shared typed contracts from the backend
- **AI agents**: Follow the agent architecture pattern (see below)

### AI Agent Development Guidelines

When working with AI agents (Flujo-based):

#### Agent Architecture Pattern
```
src/domain/agents/           # Domain layer - contracts, contexts, ports
├── contracts/               # Pydantic models with evidence fields
├── contexts/                # Pipeline context classes
└── ports/                   # Interface definitions (ABC classes)

src/application/agents/      # Application layer - orchestration
└── services/               # Use case services

src/infrastructure/llm/      # Infrastructure - Flujo implementation
├── adapters/               # Port implementations
├── factories/              # Agent creation
├── pipelines/              # Pipeline definitions with governance
├── prompts/                # System prompts
├── skills/                 # Skill registry
└── state/                  # State backend management
```

#### Creating New Agents
1. **Define contract** in `src/domain/agents/contracts/` extending `BaseAgentContract`
2. **Define context** in `src/domain/agents/contexts/` extending `BaseAgentContext`
3. **Define port** in `src/domain/agents/ports/` as an ABC class
4. **Create prompt** in `src/infrastructure/llm/prompts/`
5. **Create factory** in `src/infrastructure/llm/factories/`
6. **Create pipeline** in `src/infrastructure/llm/pipelines/`
7. **Create adapter** in `src/infrastructure/llm/adapters/`
8. **Create service** in `src/application/agents/services/`

#### Agent Contract Requirements
```python
from src.domain.agents.contracts.base import BaseAgentContract

class MyAgentContract(BaseAgentContract):
    """All contracts must include evidence-first fields."""

    # Inherited from BaseAgentContract:
    # - confidence_score: float (0.0-1.0)
    # - rationale: str
    # - evidence: list[EvidenceItem]

    # Agent-specific fields:
    result: str
    decision: Literal["success", "fallback", "escalate"]
```

#### Type Safety Exception for Flujo
The Flujo library uses `Any` types in some internal generics. This is a **documented exception** - the files are listed in `scripts/validate_architecture.py` `ALLOWED_ANY_USAGE`. Keep `Any` confined to infrastructure layer only. Domain contracts must be fully typed.

**See:** `docs/flujo/agent_architecture.md` for complete guide

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

### Flujo State Backend
- `FLUJO_STATE_URI` overrides `flujo.toml` `state_uri`; use `search_path=flujo,public` for schema isolation.
- Run `make init-flujo-schema` (or `make setup-postgres`) to create the `flujo` schema before first use.

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
│   │   └── agents/              # AI agent contracts, contexts, ports
│   ├── application/             # Use cases (shared)
│   │   └── agents/              # AI agent orchestration services
│   ├── infrastructure/          # External adapters (shared)
│   │   └── llm/                 # Flujo-based AI agent implementation
│   │       ├── adapters/        # Port implementations
│   │       ├── factories/       # Agent creation
│   │       ├── pipelines/       # Pipeline definitions
│   │       ├── prompts/         # System prompts
│   │       ├── skills/          # Skill registry
│   │       └── state/           # State backend management
│   ├── presentation/            # Reserved for future UI adapters
│   ├── web/                     # Next.js admin interface
│   └── routes/                  # API endpoints
├── docs/                         # Documentation
│   └── flujo/                   # AI agent documentation
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
- **Mock external deps**: Use `tests/test_types/mocks.py` for repositories
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

#### **100% MyPy Compliance - Strict "Never Any" Policy**
The MED13 Resource Library implements **100% MyPy compliance** with strict type checking. **Using `Any` is strictly forbidden** - this is a foundational requirement for healthcare software reliability.

#### **Core Type Safety Features**
- **Strict MyPy Configuration**: No `Any` types, comprehensive coverage
- **Pydantic Models**: Runtime type validation with rich error messages
- **Generic Types**: Proper typing for collections and containers
- **Protocol Classes**: Structural typing for interfaces
- **Type Guards**: Runtime type checking functions

#### **Essential Type Management Patterns**

**1. JSON-Compatible Types** (from `src/type_definitions/common.py`):
```python
from src.type_definitions.common import JSONObject, JSONValue

# For JSON data structures
def process_api_response(data: JSONObject) -> JSONValue:
    return data.get("result", [])

# For external API responses
def validate_external_data(raw: dict[str, JSONValue]) -> JSONObject:
    return dict(raw)
```

**2. API Response Types**:
```python
from src.type_definitions.common import APIResponse, PaginatedResponse, JSONObject

# Type-safe API responses
def get_users() -> APIResponse:
    users: list[JSONObject] = [{"id": "user-1", "email": "user@example.com"}]
    return {
        "data": users,
        "total": len(users),
        "page": 1,
        "per_page": 50,
    }

# Paginated responses
def get_paginated_genes(page: int) -> PaginatedResponse:
    genes: list[JSONObject] = [{"id": "gene-1", "symbol": "MED13"}]
    return {
        "items": genes,
        "total": len(genes),
        "page": page,
        "per_page": 50,
        "total_pages": 1,
        "has_next": False,
        "has_prev": False,
    }
```

**3. Update Operations** (from `src/type_definitions/common.py`):
```python
from src.type_definitions.common import GeneUpdate, VariantUpdate

# Type-safe updates
def update_gene(id: str, updates: GeneUpdate) -> Gene:
    # Only allows valid Gene fields
    return gene_service.update(id, updates)

# Example usage:
updates: GeneUpdate = {
    symbol: "MED13",
    name: "Updated name",
    ensembl_id: "ENSG00000108510"
}
```

**4. External API Validation** (from `src/type_definitions/external_apis.py`):
```python
from src.infrastructure.validation.api_response_validator import APIResponseValidator
from src.type_definitions.common import JSONValue
from src.type_definitions.external_apis import (
    ClinVarSearchResponse,
    ClinVarSearchValidationResult,
)

def process_clinvar_data(raw_data: dict[str, JSONValue]) -> ClinVarSearchResponse:
    validation: ClinVarSearchValidationResult = (
        APIResponseValidator.validate_clinvar_search_response(raw_data)
    )
    if not validation["is_valid"] or validation["sanitized_data"] is None:
        raise ValueError(f"Validation failed: {validation['issues']}")
    return validation["sanitized_data"]
```

**5. Typed Test Fixtures** (from `tests/test_types/fixtures.py`):
```python
from tests.test_types.fixtures import create_test_gene, TEST_GENE_MED13
from tests.test_types.mocks import create_mock_gene_service

def test_gene_operations():
    # Typed test data
    test_gene = create_test_gene(
        gene_id="TEST001",
        symbol="TEST",
        name="Test Gene"
    )

    # Type-safe mock service
    service = create_mock_gene_service([test_gene])

    # Full type safety throughout test
    result = service.get_gene_by_symbol("TEST")
    assert result.symbol == "TEST"
```

#### **Common Type Pitfalls to Avoid**

❌ **NEVER DO THIS:**
```python
# Wrong: Using Any
from typing import Any

# Wrong: Using Any
def process_data(data: Any) -> Any:
    return data.get("result")

# Wrong: Plain dict for structured data
def create_user(data: dict[str, Any]) -> User:
    return User(data)

# Wrong: Untyped external API responses
def fetch_clinvar_data(raw_response: Any) -> list[Any]:
    return raw_response.get("esearchresult", {}).get("idlist", [])
```

✅ **DO THIS INSTEAD:**
```python
# Correct: Use proper types
from src.infrastructure.validation.api_response_validator import APIResponseValidator
from src.type_definitions.common import JSONObject, JSONValue
from src.type_definitions.external_apis import (
    ClinVarSearchResponse,
    ClinVarSearchValidationResult,
)

def process_data(data: JSONObject) -> JSONValue:
    return data.get("result")

def create_user(data: UserCreate) -> User:
    return user_service.create(data)

def fetch_clinvar_data(raw_data: JSONValue) -> ClinVarSearchResponse:
    validation: ClinVarSearchValidationResult = (
        APIResponseValidator.validate_clinvar_search_response(raw_data)
    )
    if not validation["is_valid"] or validation["sanitized_data"] is None:
        raise ValueError(f"Invalid response: {validation['issues']}")
    return validation["sanitized_data"]
```

### **Type Safety Benefits**
- **Runtime Safety**: Pydantic validates all input/output at runtime
- **IDE Support**: Full autocomplete and refactoring capabilities
- **Documentation**: Types serve as living documentation
- **Testing**: Type-safe mocks and fixtures reduce test brittleness
- **Maintenance**: Refactoring is safe and reliable
- **Healthcare Compliance**: Prevents data corruption in medical research

#### **Type Safety Resources**
- **Complete patterns**: See `docs/type_examples.md` for comprehensive examples
- **Type definitions**: `src/type_definitions/` - existing types to reuse
- **Test types**: `tests/test_types/` - typed fixtures and mocks
- **Validation**: `src/infrastructure/validation/` - API response validators

## 📋 Development Standards

### Project Structure & Module Organization
```
src/
├── main.py                     # FastAPI app wiring
├── routes/                     # API endpoint definitions
├── domain/                     # Business logic & entities
│   ├── entities/              # Domain models (Pydantic)
│   ├── repositories/          # Repository interfaces
│   ├── services/              # Domain services
│   └── agents/                # AI agent domain layer
│       ├── contracts/         # Output contracts (evidence-first)
│       ├── contexts/          # Pipeline contexts
│       └── ports/             # Agent interfaces
├── application/               # Application services & use cases
│   ├── services/              # Application layer services
│   └── agents/                # AI agent orchestration
│       └── services/          # Agent use case services
├── infrastructure/            # External concerns & adapters
│   ├── repositories/          # Repository implementations
│   ├── mappers/              # Data mapping
│   ├── validation/           # External API validation
│   └── llm/                   # AI agent infrastructure (Flujo)
│       ├── adapters/          # Port implementations
│       ├── config/            # Flujo configuration
│       ├── factories/         # Agent factories
│       ├── pipelines/         # Pipeline definitions
│       ├── prompts/           # System prompts
│       ├── skills/            # Skill registry
│       └── state/             # State backend management
├── models/                    # Database models (SQLAlchemy)
├── web/                       # Next.js admin interface
tests/                          # Test suites
docs/                          # Documentation
└── flujo/                     # AI agent documentation
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

### AI Agent System (Flujo) - Production Ready
- **Contract-First Design**: Evidence-based output contracts with confidence scoring
- **Clean Architecture Alignment**: Domain contracts/ports, application services, infrastructure adapters
- **Governance Patterns**: Confidence-based routing, human-in-the-loop escalation
- **Query Generation Agent**: PubMed Boolean query generation from research context
- **Extensible Framework**: Pattern established for adding new agents (ClinVar, evidence extraction, etc.)
- **Type Safety**: Fully typed domain layer (documented exception for Flujo generics in infrastructure)

### Architecture Improvements
- **Clean Architecture**: Proper layer separation implemented
- **Type Safety**: 100% MyPy compliance maintained
- **Testing**: Comprehensive test suites with high coverage
- **CI/CD**: Automated quality gates and security scanning

## 📚 Key Documentation References

**🚨 TYPE SAFETY FIRST - Essential Reading:**

- **`docs/type_examples.md`**: **CRITICAL** - Complete type safety patterns, examples, and best practices
- **`src/type_definitions/`**: **Reference** - All existing TypedDict, Protocol, and union types
- **`tests/test_types/`**: **Reference** - Typed test fixtures, mocks, and test data patterns

**Project Architecture & Planning:**

- `docs/EngineeringArchitecture.md`: Detailed architectural roadmap and phase plans
- `data_sources_plan.md`: Complete Data Sources module specification
- `docs/goal.md`: Project mission and success criteria

**AI Agents (Flujo):**

- `docs/flujo/agent_architecture.md`: **Complete agent implementation guide** - patterns, examples, adding new agents
- `docs/flujo/reasoning.md`: Reasoning techniques (TreeSearchStep, GranularStep, A* search)
- `docs/flujo/contract_orianted_ai.md`: Contract-first AI development patterns
- `docs/flujo/prod_guide.md`: Production deployment and configuration

**Domain & UI:**

- `docs/curator.md`: Researcher curation workflows and UI patterns
- `docs/node_js_migration_prd.md`: Next.js admin interface migration plan
- `docs/infra.md`: Infrastructure and deployment details

**Type Management Quick Reference:**
- **Never use `Any`** - strict policy for healthcare software
- **Use existing types** from `src/type_definitions/` instead of creating new ones
- **JSON types**: `JSONObject`, `JSONValue` (use `list[JSONValue]` for arrays)
- **API responses**: `APIResponse`, `PaginatedResponse` for type-safe responses
- **Update operations**: `GeneUpdate`, `VariantUpdate`, etc. for partial updates
- **Test fixtures**: Always use `tests/test_types/fixtures.py` and `tests/test_types/mocks.py`

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
- **🚨 TYPE SAFETY FIRST**: Never use `Any` - this is a strict requirement for healthcare software
- **Context Awareness**: Always consider MED13's biomedical domain constraints
- **Type Management**: Use existing types from `src/type_definitions/` instead of creating new ones
- **JSON Handling**: Always use `JSONObject`, `JSONValue` (use `list[JSONValue]` for arrays)
- **API Responses**: Use `APIResponse`, `PaginatedResponse` for type-safe responses
- **Update Operations**: Use `GeneUpdate`, `VariantUpdate`, etc. TypedDict classes
- **Test Fixtures**: Always use `tests/test_types/fixtures.py` and `tests/test_types/mocks.py`
- **External APIs**: Validate responses using `src/infrastructure/validation/`
- **Testing**: Healthcare software requires extensive validation with typed fixtures
- **Documentation**: Clear docs prevent medical misinterpretation
- **Security**: Healthcare data demands fortress-level security practices

### AI Agent (Flujo) Development Guidelines
- **Contract-First**: Always define domain contracts extending `BaseAgentContract` before implementation
- **Evidence-Based**: All agent outputs must include `confidence_score`, `rationale`, and `evidence`
- **Clean Architecture**: Domain contracts/ports in `src/domain/agents/`, implementations in `src/infrastructure/llm/`
- **Governance Patterns**: Use confidence-based routing and human-in-the-loop escalation
- **Lifecycle Management**: Register pipelines with `FlujoLifecycleManager` for proper cleanup
- **State Backend**: Configure PostgreSQL backend with flujo schema for production
- **Factory Pattern**: Use factories for consistent agent configuration and model selection
- **Documented `Any` Exception**: Flujo generics require `Any` - keep confined to infrastructure, never in domain

### AI Agent Reasoning Techniques
Flujo provides structured reasoning primitives - choose based on problem complexity:

| Reasoning Type | Flujo Primitive | When to Use |
|----------------|-----------------|-------------|
| **Simple** | Standard `Step` | Direct query generation, simple tasks |
| **Chain of Thought** | `GranularStep` | Multi-turn reasoning, tool use, ReAct patterns |
| **Tree of Thoughts** | `TreeSearchStep` | Branching exploration, complex planning, backtracking |
| **Native Reasoning** | `Step` + reasoning model | Deep analysis with models like `openai:o1` |

**See:** `docs/flujo/reasoning.md` for TreeSearchStep examples

---

**This AGENTS.md serves as your comprehensive guide to building on the MED13 Resource Library. Follow these patterns to create reliable, type-safe, healthcare-grade software.** 🏥✨
