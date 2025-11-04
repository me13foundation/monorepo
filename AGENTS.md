# MED13 Resource Library - Agent Guidelines

This document provides comprehensive guidance for AI agents working on the MED13 Resource Library, including our strong engineering architecture, type safety practices, and development standards.

## 🏗️ Strong Engineering Architecture

### Clean Architecture Principles
The MED13 Resource Library implements a **Clean Architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 FastAPI REST API • Dash UI              │ │
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
├── Presentation Layer (Dash UI with Bootstrap components)
└── Quality Assurance (Type safety, testing, validation)
```

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

validation = APIResponseValidator.validate_clinvar_search_response(raw_data)
if validation["is_valid"]:
    typed_response = cast(ClinVarSearchResponse, validation["sanitized_data"])
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
├── dash_app.py                 # Dash UI application
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
├── presentation/              # UI & presentation logic
│   └── dash/                  # Dash-specific components
tests/                          # Test suites
docs/                          # Documentation
```

### Build, Test, and Development Commands
- `make setup-dev`: Clean Python 3.12 virtualenv + dependencies
- `make run-local`: Start FastAPI on port 8080
- `make run-dash`: Start Dash UI on port 8050
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
- **UI/UX**: Professional Dash interface with Bootstrap components
- **Quality Assurance**: Type-safe throughout, ready for production

### Architecture Improvements
- **Clean Architecture**: Proper layer separation implemented
- **Type Safety**: 100% MyPy compliance maintained
- **Testing**: Comprehensive test suites with high coverage
- **CI/CD**: Automated quality gates and security scanning

## 📚 Key Documentation References

- `docs/type_examples.md`: Comprehensive type safety patterns and examples
- `docs/EngineeringArchitecturePlan.md`: Detailed architectural roadmap
- `data_sources_plan.md`: Complete Data Sources module specification
- `docs/implementation_plan.md`: Technical implementation details

## 🎯 Development Philosophy

**"Build systems that are maintainable, testable, and evolvable. Type safety is not optional—it's foundational. Clean architecture enables confident refactoring and feature development."**

- **First Principles**: Strip problems to core truths, challenge assumptions
- **Robust Solutions**: Always implement the most robust solution possible
- **Long-term Focus**: Design for maintainability and evolution
- **Quality First**: Never compromise on type safety or architectural principles
