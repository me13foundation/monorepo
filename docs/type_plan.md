# MED13 Resource Library - Type Safety Plan

## Executive Summary

This document outlines the current type safety status of the MED13 Resource Library and provides a comprehensive plan to achieve **100% type coverage** with strict typing standards. The project currently maintains excellent type safety but can be enhanced further.

## Current Type Safety Status

### ✅ Strengths

#### 1. **MyPy Configuration** - Excellent
```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
show_error_codes = true
```

**Status**: ✅ **100% MyPy compliance** - All 198 source files pass strict MyPy checks.

#### 2. **Type Coverage** - Very Good
- **627 `Any` usages across 96 files** - Extensive but mostly justified
- **14 `# type: ignore` comments across 9 files** - Minimal escape hatches
- **Domain entities fully typed** - All core business objects have strict typing
- **Repository interfaces strongly typed** - Generic patterns properly implemented

#### 3. **Quality Tooling** - Robust
- **Black**: Consistent code formatting
- **Ruff**: Fast linting and additional checks
- **Pre-commit hooks**: Automated quality gates
- **CI/CD integration**: Type checks in pipeline

### ⚠️ Areas for Improvement

#### 1. **Any Usage Patterns** - Moderate Concern
**Current Status**: 627 `Any` occurrences
**Impact**: Reduces type safety in dynamic areas
**Priority**: High

**Problematic Patterns**:
```python
# ❌ Generic dictionaries
def update_gene(self, gene_id: str, updates: Dict[str, Any]) -> Gene

# ❌ JSON/API data handling
RawRecord = Dict[str, Any]

# ❌ Validation function inputs
ValidatorFn = Callable[[Any], ValidationOutcome]
```

#### 2. **Domain Service Coverage** - Needs Attention
**Coverage**: ~17-20% for complex domain services
**Issue**: Business logic not fully typed
**Impact**: Harder to catch logic errors

#### 3. **External API Integration** - Partial Coverage
**Current**: Basic typing for HTTP clients
**Missing**: Response schema validation
**Impact**: Runtime errors from malformed API data

#### 4. **Dash UI Layer** - Untyped
**Coverage**: 0% (excluded from type checking)
**Rationale**: Complex dynamic UI framework
**Future Need**: Type-safe component interfaces

## Implementation Plan

### Phase 1: Foundation Enhancement (Weeks 1-2)

#### 1.1 Enable Stricter MyPy Settings
**Goal**: Prevent new `Any` usage in critical paths

```toml
# Add to pyproject.toml
[tool.mypy]
disallow_any_generics = true
disallow_any_unimported = true
disallow_any_expr = false  # Gradual adoption
```

**Files to Update**:
- `pyproject.toml`

**Timeline**: Week 1
**Effort**: 2 hours

#### 1.2 Create Specific Types for Common Patterns
**Goal**: Replace `Dict[str, Any]` with structured types

```python
# New file: src/types/common.py
from typing import TypedDict, Optional

class GeneUpdate(TypedDict, total=False):
    name: Optional[str]
    description: Optional[str]
    gene_type: Optional[str]
    chromosome: Optional[str]
    start_position: Optional[int]
    end_position: Optional[int]
    ensembl_id: Optional[str]
    ncbi_gene_id: Optional[int]
    uniprot_id: Optional[str]

class VariantUpdate(TypedDict, total=False):
    clinical_significance: Optional[str]
    population_frequency: Optional[Dict[str, float]]
    # ... other fields

class APIResponse(TypedDict, total=False):
    data: List[Dict[str, Any]]  # Keep for external APIs
    total: int
    page: int
    per_page: int
    errors: List[str]
```

**Files to Create**:
- `src/types/common.py`
- `src/types/api.py`
- `src/types/domain.py`

**Timeline**: Week 1-2
**Effort**: 8 hours

#### 1.3 Enhance Repository Interfaces
**Goal**: Make update operations type-safe

```python
# Current (problematic)
def update(self, id: ID, updates: Dict[str, Any]) -> T:

# Improved (typed)
def update_gene(self, gene_id: str, updates: GeneUpdate) -> Gene:
def update_variant(self, variant_id: str, updates: VariantUpdate) -> Variant:
```

**Files to Update**:
- `src/domain/repositories/gene_repository.py`
- `src/domain/repositories/variant_repository.py`
- `src/domain/repositories/phenotype_repository.py`
- `src/domain/repositories/evidence_repository.py`
- `src/domain/repositories/publication_repository.py`

**Timeline**: Week 2
**Effort**: 12 hours

### Phase 2: Domain Logic Enhancement (Weeks 3-4)

#### 2.1 Type Domain Services
**Goal**: Achieve 90%+ coverage in domain services

**Current Low-Coverage Services**:
- `GeneDomainService` (~19% coverage)
- `VariantDomainService` (~14% coverage)
- `EvidenceDomainService` (~17% coverage)

**Strategy**:
1. **Identify complex business logic functions**
2. **Add intermediate types for computations**
3. **Use generics for polymorphic operations**

```python
# Example enhancement
class GeneValidationResult(TypedDict):
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggested_fixes: List[str]

def validate_gene_relationships(
    self,
    gene: Gene,
    variants: List[Variant],
    phenotypes: List[Phenotype]
) -> GeneValidationResult:
    # Fully typed implementation
    pass
```

**Files to Update**:
- `src/domain/services/gene_domain_service.py`
- `src/domain/services/variant_domain_service.py`
- `src/domain/services/evidence_domain_service.py`

**Timeline**: Weeks 3-4
**Effort**: 20 hours

#### 2.2 Strengthen Validation Types
**Goal**: Make validation framework fully type-safe

```python
# Current (acceptable for flexibility)
ValidatorFn = Callable[[Any], ValidationOutcome]

# Enhanced (better type safety)
T = TypeVar('T')
ValidatorFn = Callable[[T], ValidationOutcome]

class ValidationRule(Protocol[T]):
    def validate(self, entity: T) -> ValidationOutcome:
        ...

class GeneValidationRule(ValidationRule[Gene]):
    def validate(self, gene: Gene) -> ValidationOutcome:
        # Type-safe validation logic
        pass
```

**Files to Update**:
- `src/domain/validation/rules/base_rules.py`
- `src/domain/validation/rules/gene_rules.py`
- `src/domain/validation/rules/variant_rules.py`

**Timeline**: Week 4
**Effort**: 16 hours

### Phase 3: Infrastructure & Integration (Weeks 5-6)

#### 3.1 Type External API Responses
**Goal**: Prevent runtime errors from malformed API data

```python
# New approach
from typing import TypedDict, Literal
from pydantic import BaseModel, ValidationError

class ClinVarResponse(BaseModel):
    variations: List[Dict[str, Any]]
    total_results: int
    api_version: str

class PubMedArticle(BaseModel):
    pmid: str
    title: str
    abstract: Optional[str]
    authors: List[str]
    publication_date: str

def fetch_pubmed_data(query: str) -> List[PubMedArticle]:
    response = httpx.get(f"https://api.ncbi.nlm.nih.gov/pubmed?query={query}")
    raw_data = response.json()

    try:
        validated = ClinVarResponse(**raw_data)
        return validated.variations
    except ValidationError as e:
        logger.error(f"Invalid API response: {e}")
        raise DataIngestionError(f"API response validation failed: {e}")
```

**Files to Create/Update**:
- `src/types/external_apis.py`
- `src/infrastructure/ingest/clinvar_ingestor.py`
- `src/infrastructure/ingest/pubmed_ingestor.py`
- `src/infrastructure/ingest/hpo_ingestor.py`
- `src/infrastructure/ingest/uniprot_ingestor.py`

**Timeline**: Weeks 5-6
**Effort**: 24 hours

#### 3.2 Type Publishing & Packaging
**Goal**: Ensure reliable data export/import

```python
from typing import TypedDict, Literal

class ROCrateMetadata(TypedDict):
    name: str
    description: str
    license: str
    author: List[Dict[str, str]]
    dateCreated: str
    conformsTo: Literal["https://w3id.org/ro/crate/1.1"]

class DataPackage(TypedDict):
    metadata: ROCrateMetadata
    genes: List[Gene]
    variants: List[Variant]
    phenotypes: List[Phenotype]
    evidence: List[Evidence]
    publications: List[Publication]
    provenance: Provenance
```

**Files to Update**:
- `src/application/packaging/rocrate/builder.py`
- `src/application/packaging/rocrate/metadata.py`
- `src/infrastructure/publishing/zenodo/client.py`

**Timeline**: Week 6
**Effort**: 16 hours

### Phase 4: Testing & Documentation (Week 7)

#### 4.1 Type Test Fixtures
**Goal**: Prevent test data inconsistencies

```python
# src/tests/types/fixtures.py
from typing import NamedTuple

class TestGene(NamedTuple):
    gene_id: str
    symbol: str
    name: Optional[str]
    chromosome: Optional[str]
    start_position: Optional[int]
    end_position: Optional[int]

class TestVariant(NamedTuple):
    variant_id: str
    gene_id: str
    hgvs_notation: str
    clinical_significance: str
    population_frequency: Dict[str, float]

# Type-safe fixture factories
def create_test_gene(**kwargs) -> TestGene:
    defaults = {
        'gene_id': 'TEST001',
        'symbol': 'TEST',
        'name': None,
        'chromosome': None,
        'start_position': None,
        'end_position': None
    }
    return TestGene(**{**defaults, **kwargs})
```

**Files to Create**:
- `src/tests/types/fixtures.py`
- `src/tests/types/mocks.py`

**Timeline**: Week 7
**Effort**: 12 hours

#### 4.2 Update Documentation
**Goal**: Document type contracts

```python
# In docstrings and README
"""
Gene Service API

Type Contracts:
- GeneUpdate: Partial gene updates (TypedDict)
- GeneFilter: Query parameters for gene search
- PaginatedGenes: Response format for gene listings

Example:
    service = GeneApplicationService(...)
    updates: GeneUpdate = {'name': 'Updated Name'}
    gene = service.update_gene('GENE001', updates)
"""
```

**Files to Update**:
- `README.md`
- All service class docstrings
- API documentation

**Timeline**: Week 7
**Effort**: 8 hours

## Success Metrics

### Type Coverage Targets

| Component | Current | Target | Timeline |
|-----------|---------|--------|----------|
| Domain Entities | 100% | 100% | Complete |
| Repository Interfaces | 95% | 100% | Week 2 |
| Domain Services | 17-19% | 90% | Week 4 |
| Application Services | 80% | 95% | Week 3 |
| Infrastructure | 70% | 90% | Week 6 |
| Tests | 85% | 95% | Week 7 |
| **Overall** | **75%** | **95%** | **Month 1** |

### Quality Gates

1. **MyPy Strict Mode**: ✅ All files pass
2. **Zero `# type: ignore`**: Target for critical paths
3. **Any Usage Reduction**: 60% reduction in `Any` occurrences
4. **Documentation**: All public APIs documented with types

### Monitoring

```bash
# Daily type checks
make type-check

# Weekly coverage reports
make test-cov
mypy src --html-report mypy-report/

# Track Any usage trends
find src -name "*.py" -exec grep -l "Any" {} \; | wc -l
```

## Risk Mitigation

### Technical Risks

1. **Over-engineering**: Use pragmatic typing - avoid over-abstracting
2. **Performance Impact**: MyPy checks should remain fast (<30 seconds)
3. **Developer Experience**: Type errors should be clear and actionable

### Mitigation Strategies

1. **Gradual Adoption**: Start with high-impact areas, expand gradually
2. **Team Training**: Ensure all developers understand typing patterns
3. **Tool Integration**: Make type checking part of daily workflow
4. **Fallback Plans**: Use `# type: ignore[reason]` for complex cases

## Implementation Timeline

```
Week 1: Foundation Setup
├── Enable stricter MyPy settings
└── Create common type definitions

Week 2: Repository Enhancement
├── Type repository update operations
└── Create domain-specific update types

Week 3-4: Domain Logic
├── Type domain services (90% coverage)
└── Strengthen validation framework

Week 5-6: Infrastructure
├── Type external API integrations
└── Type publishing/packaging layer

Week 7: Testing & Documentation
├── Type test fixtures and mocks
└── Update documentation and examples
```

## Conclusion

The MED13 Resource Library has an **excellent foundation** for type safety but can achieve **world-class type coverage** with focused effort. The plan emphasizes **pragmatic improvements** that provide immediate value while maintaining development velocity.

**Key Success Factors**:
- **Gradual adoption** prevents disruption
- **High-impact areas first** maximizes benefit
- **Developer-friendly** type errors and tooling
- **Comprehensive testing** ensures reliability

**Expected Outcome**: A codebase with **95%+ type coverage** that catches bugs at development time, improves IDE support, and serves as a model for type-safe scientific software development.
