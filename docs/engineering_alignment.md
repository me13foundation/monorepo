# Engineering Alignment Roadmap

## Objective
Deliver the highest engineering maturity score by resolving architecture
deficiencies and strengthening quality practices across the MED13 Resource
Library. This document translates the assessment findings into actionable work.

## Current Gaps To Close
- Domain entities and value objects are thin re-exports of Pydantic DTOs.
- Domain services depend directly on SQLAlchemy ORM models and infrastructure.
- Business rules live in services instead of in rich domain objects.
- Layer boundaries blur, making inversion of control difficult to enforce.

## Strategic Initiatives

### 1. Model a True Domain Layer
1. Define entity classes under `src/domain/entities/` that encapsulate state and
   domain rules (e.g., `Gene`, `Variant`, `Phenotype`, `Publication`).
2. Introduce value objects (gene symbol, genomic coordinates, provenance) that
   validate invariants without referencing Pydantic.
3. Relocate business logic from services into entities (e.g., coordinate
   validation, variant association rules, identifier normalization).
4. Provide domain-to-DTO mappers so presentation layers can project entities
   into API responses cleanly.

### 2. Invert Dependencies and Isolate Infrastructure
1. Redesign repositories to work with domain entities rather than ORM models;
   establish mappers between domain entities and SQLAlchemy models.
2. Adjust services to depend on domain repositories through interfaces so the
   domain no longer imports infrastructure modules.
3. Move SQLAlchemy-specific behaviors (sessions, query helpers) behind clearly
   named adapters in `src/infrastructure/database/`.
4. When creating new integrations, ensure dependencies point inward (application
   -> domain) and outward only through defined ports.

### 3. Establish Rich Domain Services
1. Create domain service modules for cross-entity operations (e.g., gene-variant
   association policies, evidence aggregation logic).
2. Keep application services responsible for orchestration, transactions, and
   coordination with adapters.
3. Document service responsibilities with concise docstrings and diagrams in
   `docs/architecture/` to guard against scope creep.

### 4. Strengthen Testing and Quality Gates
1. Add unit tests for each domain entity and value object to lock down business
   invariants.
2. Introduce integration tests covering repository adapters to ensure mappings
   between domain entities and ORM models remain correct.
3. Expand contract tests for service orchestration to validate dependency
   inversion boundaries.
4. Maintain strict MyPy, Ruff, Flake8 gates via `make all`; update CI to block
   merges without full suite success.

### 5. Governance and Documentation
1. Update architecture decision records (ADRs) to reflect the refactored domain
   model and dependency flow.
2. Provide onboarding guides describing the domain-driven design approach,
   naming conventions, and layering rules.
3. Schedule recurring architecture reviews to evaluate adherence to the new
   boundaries and capture follow-up actions.

## Integration Notes
- Start introducing mapper modules (e.g., `src/infrastructure/mappers/gene_mapper.py`)
  that translate between SQLAlchemy models and the new domain entities while keeping
  the domain layer free of infrastructure imports.
- Until repositories are refactored, services can instantiate domain entities via
  `Gene.create` and hand them to mappers for persistence, enabling incremental
  adoption without a big-bang rewrite.
- Capture mapping invariants (required fields, timestamp handling, provenance
  translation) alongside the mapper implementations to keep the domain contract
  explicit.

## Success Metrics
- Domain layer offers complete business behavior without referencing Pydantic or
  ORM classes.
- Services depend only on domain interfaces and infrastructure adapters.
- CI runs achieve 100% pass rate with enhanced domain, integration, and contract
  tests.
- Maturity assessment checkpoints rate architecture, SOLID, and maintainability
  at the maximum score.
