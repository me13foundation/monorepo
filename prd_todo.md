# MED13 Resource Library – PRD Implementation Plan

This document tracks all outstanding work required to fulfill the **Unified Storage & Advanced Literature Discovery PRD**. Each section maps directly to PRD requirements so engineering squads can execute in parallel while preserving Clean Architecture boundaries and type‑safety guarantees.

---

## 1. Storage Platform Completion

### 1.1 Domain & Application Layer
- [x] **Validator parity** – extend `StorageConfigurationValidator` with:
  - Duplicate name detection (already exists) plus conflicting default use case detection, provider quota guardrails, and `StorageValidationError`/`StorageQuotaError` errors instead of generic `ValueError`.
  - Validation helpers for allowed combinations of `supported_capabilities` vs provider advertised capabilities.
- [x] **Typed responses** – return `ApiResponse[StorageConfigurationModel]` and `PaginatedResponse[...]` DTOs from admin routes to satisfy PRD API schema.
- [x] **Delete/disable flow** – implement `delete_configuration` (soft delete + audit metadata) and expose `DELETE /api/admin/storage/configurations/{id}`.
- [x] **Aggregated stats endpoint** – add application service method that aggregates usage, health, and provider metadata for all configs; expose as `/api/admin/storage/stats`.
- [x] **Use case resolution API** – expose `get_backend_for(use_case: StorageUseCase)` that returns active configuration + plugin instance so ingest/export/discovery services can resolve file targets.
- [x] **Store operation orchestration** – add helper(s) (e.g., `StorageOperationExecutor`) that call `record_store_operation` and surface results to ingestion workflows.

### 1.2 Infrastructure Layer
- [x] **Repository updates** – ensure SQLAlchemy repositories support soft delete, stats aggregation, and paginated queries. Add `StorageStatsModel` view or compute via SQL window functions.
- [x] **Dependency wiring** – update `DependencyContainer` to provide storage services to ingestion/export/discovery modules, not only admin routes.
- [x] **Audit logging** – hook storage CRUD/test actions into `AuditTrailService`.

### 1.3 Presentation Layer (FastAPI)
- [x] Adopt shared response wrappers, enable pagination/filter parameters on list endpoint.
- [x] Add maintenance-mode guard rails to POST/PUT/DELETE routes.
- [x] Create `/admin/storage/stats` route returning usage & health aggregates.

### 1.4 Presentation Layer (Next.js)
- [x] **Storage dashboard** – extend `StorageConfigurationManager` with:
  - [x] Overview cards (enabled configs, capacity used, error rate).
  - [x] Time-series chart placeholders fed by new stats endpoint.
  - [x] Bulk actions (multi-select enable/disable/default assignment) with React Query mutations.
  - [x] Feature flag plumbing for beta rollout.
- [x] **Prefetch** – server component should hydrate new stats query.
- [x] **Delete flow** – add UI affordance + confirmation modal.

### 1.5 Testing & Monitoring
- [x] Unit tests for validator, registry, new service helpers.
- [x] Integration tests hitting LocalFS + mocked GCS (filesystem or moto-style fake) to test CRUD, stats, delete.
- [x] Playwright/E2E coverage for storage tab flows (create, test, toggle, delete).
- [x] Observability dashboards: define metrics events (test success/fail, store latency) + add stub for exporter.

---

## 2. Advanced Discovery & Presets

### 2.1 Data Model & Types
- [x] Update `DataDiscoverySessionModel` to store `pubmed_search_config` JSONB column (already migrated) plus optional future connector configs.
- [x] Extend mappers to read/write `AdvancedQueryParameters`.
- [x] Introduce `DiscoveryPreset` domain model + repository + TypedDict for API responses.
- [x] Add `QueryParameterCapabilities` fields to `SourceCatalogEntry` metadata and include them in API responses.
- [x] Update TypeScript types (`src/web/lib/types/data-discovery.ts`) to include advanced parameter shape & presets.

- [x] Build `DiscoveryConfigurationService` with responsibilities:
  - Manage presets (create, list, delete) scoped to user or research space.
  - Provide capability metadata to UI.
  - Validate parameter payloads via `PubMedQueryBuilder`.
- [x] Implement `PubMedQueryBuilder` that:
  - Converts `AdvancedQueryParameters` to E-utilities query strings.
      - Provides preview text and validation results (date ordering, allowed publication types, etc.).
- [x] Create `PDFDownloadService`/`PDFDownloadOrchestrator`:
  - Fetch PDFs/PMC exports for PubMed results.
  - Use `StorageConfigurationService.get_backend_for(StorageUseCase.PDF)` to persist files (and `RAW_SOURCE` for other connectors).
  - Emit `StorageOperationRecord`s and audit events.
- [x] Extend `SpaceDataDiscoveryService` to surface presets and default advanced parameters per space.

### 2.3 FastAPI Routes
- [x] `/api/data-discovery/pubmed/presets` – CRUD for presets using new service.
- [x] `/api/data-discovery/pubmed/search` & `/search/{id}` – start advanced searches + poll results (with storage automation hooks).
- [x] `/api/data-discovery/pubmed/download` – trigger PDF download and return storage metadata.
- [x] Update existing `/data-discovery/sessions` endpoints to accept/return `AdvancedQueryParameters` where applicable.
- [x] Apply capability data to catalog responses so UI can dynamically enable filters.

- [x] Implement SQLAlchemy models/tables for discovery presets (columns: id, owner_id, scope, provider, parameters JSON, metadata, timestamps).
- [x] Add repositories for presets and for asynchronous search runs (jobs table tracking search status, storage key, etc.).
- [x] Integrate storage adapters with ingestion scheduler so PDF downloads can be retried/resumed.

### 2.5 Next.js UI
- [x] **Advanced parameter bar** – add sections (Basics, Filters, Output) covering:
  - Date range pickers, publication type multi-select, language chips, sort selectors, result limits, additional terms.
  - Real-time validation + query preview using server endpoint.
- [x] **Preset modal** – save/load/delete presets, with sharing scope selector (user vs space) behind feature flag as per PRD.
- [x] **Discovery modal enhancements** – show storage target summary, capability-driven field toggles.
- [x] **PDF automation UX** – button/state in Results view to download articles; display toast + link to stored asset.
- [x] Update React Query hooks to consume new endpoints and hydrate capability metadata.

### 2.6 Testing
- [x] Unit tests for `PubMedQueryBuilder`, preset service, capability enforcement.
- [x] Integration tests for new routes (pytest) using fixtures for advanced params & presets.
- [x] Frontend tests (React Testing Library + Playwright) for parameter forms, preset workflows, PDF download flows.

---

## 3. Cross-Source Adoption (ClinVar, UniProt, Custom APIs)

- [x] Extend `SourceCatalogEntry` metadata to declare connector-specific advanced parameters and compatible storage use cases.
- [x] Implement capability-driven forms in UI for these connectors (reusing advanced parameter components).
- [x] Add new API endpoints or extend existing ones to trigger ClinVar/UniProt searches using shared preset service.
- [x] Ensure ingestion pipelines call `StorageConfigurationService` for RAW_SOURCE and EXPORT use cases.
- [x] Document provider onboarding steps (new plugin + typed config) in `docs/` per PRD.

---

## 4. Monitoring, Security, and Audit

- [x] Expand audit events to cover:
  - Storage CRUD/test/delete, preset changes, advanced search executions, PDF downloads, automated store operations.
- [x] Enforce typed `ApiErrorResponse` for rate-limit violations, storage errors, PDF failures.
- [x] Add observability hooks (metrics/logs) for provider latency, discovery search success rate, automation coverage (≥99.9% stored PDFs).
- [x] Update `docs/security.md` with new threat considerations (storage credentials, preset sharing permissions).

---

## 5. Testing & Quality Gates

- [x] Increase unit + integration coverage for all new services to maintain ≥85% target.
- [x] Update `make all` to include new test suites (preset, discovery, PDF downloads).
- [x] Create synthetic performance tests for storage upload/download (100 MB <10s) and concurrent plugin ops (≥10 parallel).
- [x] Add contract tests for storage APIs to ensure TS/py parity.
- [x] Set up Playwright scenarios covering storage dashboard, advanced discovery parameter UX, preset flows, and PDF automation.

---

## 6. Rollout & Documentation

- [ ] Align implementation phases (1–6) with PRD timeline:
  - Track progress per phase in this TODO and link to Jira/GitHub issues.
- [x] Update `docs/EngineeringArchitecture.md`, `docs/frontend/EngineeringArchitectureNext.md`, and `docs/type_examples.md` with new patterns.
- [x] Provide runbooks for storage plugin onboarding, preset management, and PDF automation troubleshooting.
- [x] Ensure release notes capture feature flags, migration steps, and rollback plans.

---

**Status Legend:**
Use GitHub issues or project board to track each checkbox. Mark completed items, and annotate with PR links as we implement the remaining PRD scope.
