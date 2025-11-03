# MED13 Resource Library - Realistic Architecture Roadmap

## Current State Assessment (Accurate as of Analysis)

### ✅ Existing Strengths
- **Type Safety**: 100% MyPy compliance with strict settings
- **Layered Architecture**: Clean separation of concerns (Presentation → Application → Domain → Infrastructure)
- **Security Foundation**: API key auth, rate limiting, CORS protection
- **Advanced Features**: Conflict detection, webhook notifications, async processing
- **Testing**: Unit, integration, and E2E test suites (68% coverage)

### ❌ Current Gaps (Verified)
- **Repository Duplication**: 3 repository layers exist instead of clean domain/infrastructure split
- **Incomplete API**: Only `/genes` endpoint; missing `/variants`, `/phenotypes`, `/evidence`
- **Security Issues**: 7 Bandit MEDIUM vulnerabilities (XML parsing, interface binding)
- **CI/CD Gaps**: No linting, type checking, or security scanning in CI pipeline
- **Test Coverage**: 68% coverage leaves business logic unverified
- **Production Readiness**: SQLite defaults, missing deployment configurations

## Realistic Implementation Roadmap

### Phase 1: Critical Foundation Fixes (1-2 weeks)
**Focus**: Fix architectural inconsistencies and security issues

#### Step 1.1: Repository Consolidation
```bash
# Current state: 3 repository layers
src/repositories/              # Remove this layer
src/domain/repositories/       # Keep as interfaces
src/infrastructure/repositories/ # Keep as implementations

# Target state: Clean separation
src/domain/repositories/       # Interfaces only
src/infrastructure/repositories/sql/ # SQL implementations
```

**Concrete Steps**:
1. **Audit current usage**: `grep -r "from src.repositories" src/`
2. **Migrate imports**: Update all imports to use domain/infrastructure layers
3. **Remove duplicate files**: Delete `src/repositories/` after migration
4. **Update dependency injection**: Verify `container.py` uses correct layers
5. **Run tests**: Ensure no functionality broken

**Verification**: `find src -name "*repository.py" | grep -v domain | grep -v infrastructure` should return empty

#### Step 1.2: Security Issue Resolution
**Address 7 Bandit MEDIUM issues**:

**Issue #1: Interface Binding**
- **File**: `src/dash_app.py:1097`
- **Problem**: `host="0.0.0.0"` binds to all interfaces
- **Fix**: Change to `host="127.0.0.1"` for development, use environment variable for production

**Issue #2-7: XML Parsing & Input Validation**
- **Files**: Data ingestion modules
- **Fix**: Add input sanitization, use secure XML parsers, validate all inputs

**Concrete Steps**:
1. **Run Bandit**: `bandit -r src -f json -o bandit-results.json`
2. **Fix each issue**: Address root causes, not just suppress warnings
3. **Add input validation**: Implement comprehensive validation in all data ingestion points
4. **Re-run Bandit**: Verify all MEDIUM issues resolved

**Verification**: `bandit -r src | grep -c "MEDIUM"` should return 0

#### Step 1.3: CI/CD Pipeline Enhancement
**Current**: Only basic install/test
**Target**: Full quality gates

**Concrete Steps**:
1. **Update `.github/workflows/deploy.yml`**:
   ```yaml
   - name: Run linting
     run: make lint
   - name: Run type checking
     run: make type-check
   - name: Run security audit
     run: make security-audit
   ```
2. **Fix security audit failures**: Address any issues found
3. **Add coverage reporting**: Upload coverage reports to CI

**Verification**: CI pipeline runs all quality checks and passes

### Phase 2: API Completeness (2-3 weeks)
**Focus**: Complete the API surface for all entities

#### Step 2.1: Variants API Implementation
**Current**: No `src/routes/variants.py`
**Target**: Full CRUD API matching genes pattern

**Concrete Steps**:
1. **Create `src/routes/variants.py`**: Copy genes.py structure, adapt for variants
2. **Add to `src/routes/__init__.py`**: Export `variants_router`
3. **Update `src/main.py`**: Include variants router
4. **Add variant models**: Extend `src/models/api/` with variant schemas
5. **Implement service wiring**: Update dependency injection

**Verification**: `GET /variants/` returns variant list, all CRUD operations work

#### Step 2.2: Phenotypes API Implementation
**Current**: No `src/routes/phenotypes.py`
**Target**: Full CRUD with HPO integration

**Concrete Steps**:
1. **Create `src/routes/phenotypes.py`**: Implement phenotype endpoints
2. **Add HPO integration**: Connect to phenotype hierarchy service
3. **Add to routing**: Include in `__init__.py` and `main.py`
4. **Add validation**: HPO ID format validation

**Verification**: `GET /phenotypes/?hpo_id=HP:0001234` works

#### Step 2.3: Evidence API Implementation
**Current**: No `src/routes/evidence.py`
**Target**: Full CRUD with conflict detection integration

**Concrete Steps**:
1. **Create `src/routes/evidence.py`**: Evidence endpoints with confidence scoring
2. **Integrate conflict detection**: Use existing `evidence_service.detect_evidence_conflicts()`
3. **Add filtering**: By variant_id, confidence thresholds, evidence levels
4. **Add to routing**: Complete API surface

**Verification**: `GET /evidence/?variant_id=123` returns evidence with conflict flags

### Phase 3: Advanced Features & Production Readiness (3-4 weeks)

#### Step 3.1: Search System Implementation
**Current**: Basic gene search only
**Target**: Full-text search across all entities

**Concrete Steps**:
1. **Create search service**: `src/application/search/search_service.py`
2. **Add search endpoint**: `src/routes/search.py` with POST /search/
3. **Implement basic filtering**: Database-level filtering for MVP
4. **Add relevance scoring**: Sort by confidence scores, recency

**Verification**: Complex queries like `POST /search/` with filters work

#### Step 3.2: Bulk Export API
**Current**: No bulk operations
**Target**: JSON/CSV/TSV export capabilities

**Concrete Steps**:
1. **Create export service**: Handle large dataset serialization
2. **Add export endpoint**: `GET /export/{entity_type}?format=json`
3. **Implement streaming**: For large datasets to avoid memory issues
4. **Add compression**: Gzip support for large exports

**Verification**: `GET /export/variants?format=csv` downloads complete dataset

#### Step 3.3: Database & Configuration Production-Ready
**Current**: SQLite defaults
**Target**: PostgreSQL with proper configuration

**Concrete Steps**:
1. **Update connection config**: Environment-based database selection
2. **Add production settings**: Connection pooling, read replicas config
3. **Implement migrations**: Proper Alembic setup for schema changes
4. **Add health checks**: Database connectivity monitoring

**Verification**: App runs with PostgreSQL in production environment

#### Step 3.4: Test Coverage Improvement
**Current**: 68% coverage
**Target**: >85% coverage

**Concrete Steps**:
1. **Identify gaps**: Run `make test-cov` and review uncovered lines
2. **Add missing unit tests**: Focus on business logic in domain layer
3. **Add integration tests**: API endpoint testing
4. **Add error case testing**: Edge cases and failure scenarios

**Verification**: `make test-cov` shows >85% coverage

### Phase 4: Production Deployment & Monitoring (2-3 weeks)

#### Step 4.1: Containerization & Deployment
**Current**: Basic Cloud Run deployment
**Target**: Production-ready container with proper configuration

**Concrete Steps**:
1. **Update Dockerfile**: Multi-stage build, security hardening
2. **Add health checks**: Proper `/health/` endpoint with dependencies
3. **Environment configuration**: Production secrets, database URLs
4. **Deployment automation**: Blue-green deployment setup

**Verification**: Successful production deployment with zero-downtime updates

#### Step 4.2: Monitoring & Observability
**Current**: Basic logging
**Target**: Comprehensive monitoring stack

**Concrete Steps**:
1. **Add structured logging**: JSON format with correlation IDs
2. **Implement metrics**: Response times, error rates, database performance
3. **Add health endpoints**: Detailed health checks for all dependencies
4. **Set up alerting**: Automated alerts for critical issues

**Verification**: Real-time monitoring dashboard shows system health

## Success Verification Framework

### Automated Checks (CI/CD)
```bash
# Quality gates that must pass
make lint                    # Code style & formatting
make type-check             # Type safety verification
make security-audit         # Security vulnerability scan
make test                   # Unit & integration tests
make test-cov               # Coverage >85%

# API completeness verification
curl -f http://localhost:8080/variants/ || exit 1
curl -f http://localhost:8080/phenotypes/ || exit 1
curl -f http://localhost:8080/evidence/ || exit 1
```

### Manual Verification Checklist
- [ ] All repository layers consolidated (no duplicates)
- [ ] All Bandit MEDIUM issues resolved
- [ ] All core entity APIs implemented and functional
- [ ] Search works across all entities
- [ ] Bulk export works for large datasets
- [ ] Application starts with PostgreSQL
- [ ] Production deployment successful
- [ ] Monitoring alerts configured

## Risk Mitigation Strategy

### Rollback Plans
- **Repository refactoring**: Keep old layer as backup, gradual migration
- **API changes**: Versioned endpoints, backward compatibility
- **Database changes**: Proper migrations with rollback scripts
- **Deployment**: Blue-green deployment with instant rollback capability

### Testing Strategy
- **Unit tests**: All business logic changes
- **Integration tests**: API workflows and service interactions
- **E2E tests**: Critical user journeys
- **Performance tests**: Load testing before production

### Monitoring & Alerting
- **Error tracking**: Sentry integration for error monitoring
- **Performance monitoring**: Response time and throughput tracking
- **Business metrics**: API usage, search query success rates
- **Infrastructure**: Database connections, cache hit rates

## Resource Allocation

### Team Requirements
- **Lead Engineer**: 1 FTE (architecture, complex features)
- **Backend Engineer**: 1 FTE (API implementation, testing)
- **DevOps Engineer**: 0.5 FTE (CI/CD, deployment, monitoring)

### Time Estimates (Realistic)
- **Phase 1**: 2 weeks (critical foundation)
- **Phase 2**: 3 weeks (API completeness)
- **Phase 3**: 4 weeks (advanced features)
- **Phase 4**: 3 weeks (production deployment)

**Total**: 12 weeks for complete transformation

## Conclusion

This roadmap provides a **realistic, achievable path** to the ideal architectural state. Unlike the previous aspirational plan, this focuses on:

1. **Current State Accuracy**: Based on verified codebase analysis
2. **Concrete Deliverables**: Specific files, commands, and verification steps
3. **Incremental Progress**: Each phase delivers working, testable improvements
4. **Risk Management**: Rollback plans and thorough testing at each step
5. **Measurable Success**: Clear verification criteria for each phase

The result will be a **production-ready biomedical data platform** that maintains the strong architectural foundation while delivering complete functionality and enterprise-grade quality.
