# MED13 Resource Library – Unified Storage & Advanced Literature Discovery PRD

## 1. Context & Goals
- Strengthen the Clean Architecture implementation documented in `docs/EngineeringArchitecture.md` by clearly placing new storage and discovery capabilities into the domain → application → infrastructure stack.
- Extend the existing PubMed-specific proposal to **all data discovery sources** (ClinVar, OMIM, UniProt, custom APIs, etc.) so that storage, metadata, and advanced search settings follow the same typed contracts and UI workflows.
- Preserve the strict type-safety rules from `docs/type_examples.md` and ensure every new contract has a Pydantic + TypedDict definition that can flow to generated TypeScript types for the Next.js admin (`docs/frontend/EngenieeringArchitectureNext.md`).

### Success Metrics
| Metric | Target |
| --- | --- |
| Config-related support tickets | ↓95% (baseline per release) |
| Search precision (validated user studies) | +50% |
| Storage provider coverage | ≥3 providers (Local, GCS, Future cloud) |
| Discovery-to-storage automation | ≥99.9% stored PDFs / exports |
| Setup time for new provider | ≤5 minutes from UI |
| Type-checking compliance | 100% MyPy + generated TS parity |

## 2. Scope
1. **Storage Plugin Platform** usable by any ingestion, export, or retrieval workflow.
2. **Advanced Discovery Parameter System** that generalizes PubMed enhancements to all query-capable data sources.
3. **UI/UX enhancements** in the Next.js admin for configuring storage, watching health, and managing discovery presets while keeping the server-prefetch + React Query hydration pattern.
4. **Audit, observability, and rollout** guardrails for healthcare compliance.

### Out of Scope
- Moving persistence away from PostgreSQL (only schema additions are planned).
- Replacing the existing ingestion scheduler (will integrate with its service interfaces).

## 3. Stakeholders
- Research Admins: configure storage + discovery defaults.
- Researchers: run advanced searches, download PDFs/exports with guaranteed storage paths.
- Platform Engineers: implement plugins, monitor jobs, add new providers.

## 4. Clean Architecture Placement
| Component | Layer | Notes |
| --- | --- | --- |
| `StorageProviderPlugin` protocol, `DiscoveryPreset` entity | Domain | Pure contracts + Pydantic models; no I/O.
| `StorageConfigurationService`, `DiscoveryConfigurationService`, `PDFDownloadOrchestrator` | Application | Use cases coordinating repositories + plugins; wired via dependency-injection containers per subsystem.
| SQLAlchemy repositories, GCS client adapters, PubMed E-utilities client | Infrastructure | Adapter-specific logic; injected via dependency inversion.
| FastAPI routes under `src/routes/admin/storage` & `src/routes/data_discovery/pubmed` (plus Next.js UI) | Presentation | Only call application services via DI; uses typed schemas for request/response.

## 5. Domain & Type Contracts
All new models must live under `src/domain/entities/` or `src/type_definitions/` and export TS equivalents through the existing generator.

```python
# src/type_definitions/storage.py
class StorageProviderCapability(StrEnum):
    PDF = "pdf"
    EXPORT = "export"
    RAW_SOURCE = "raw_source"

class StorageUseCase(StrEnum):
    PDF = "pdf"
    EXPORT = "export"
    RAW_SOURCE = "raw_source"
    BACKUP = "backup"

class StorageConfigurationModel(BaseModel):
    id: UUID
    name: str
    provider: StorageProviderName
    config: StorageProviderConfig
    enabled: bool
    supported_capabilities: set[StorageProviderCapability]
    default_use_cases: set[StorageUseCase]
    metadata: JSONObject
    created_at: datetime
    updated_at: datetime
```

```python
# src/type_definitions/pubmed.py
class AdvancedQueryParameters(QueryParameters):
    date_from: date | None
    date_to: date | None
    publication_types: list[PublicationType]
    languages: list[str]
    sort_by: PubMedSortOption
    max_results: conint(ge=1, le=1000) = 100
    additional_terms: str | None
```

- Capabilities metadata determine which advanced fields appear per data source:

```python
class QueryParameterCapabilities(BaseModel):
    supports_date_range: bool = False
    supports_publication_types: bool = False
    supports_language_filter: bool = False
    supports_sort_options: bool = False
    supports_additional_terms: bool = False
    max_results_limit: conint(ge=1, le=1000) = 1000
```

- **Typed JSON columns** (`config_data`, `pubmed_search_config`) must serialize one of these models; no loose dicts.
- `StorageOperationRecord`, `DiscoveryPreset` TypedDicts back the API responses via `ApiResponse[T]` / `PaginatedResponse[T]`.

## 6. Storage Plugin Platform
### Requirements
1. `StorageProviderPlugin` protocol extends `Protocol` with async methods: `validate_config`, `ensure_storage_exists`, `store_file`, `get_file_url`, `list_files`, `delete_file`, `get_storage_info`.
2. `StoragePluginRegistry` (domain service) keeps provider metadata and capabilities. Registration occurs at startup via an `initialize_storage_plugins()` helper inside infrastructure wiring (no dynamic runtime imports). The helper registers Local FS + GCS and exposes a documented hook for future providers.
3. `StorageConfigurationService` responsibilities:
   - CRUD operations backed by `StorageConfigurationRepository` (SQLAlchemy + Alembic migration for `storage_configurations`).
   - Provider-specific validation by delegating to registry before persistence.
   - Mapping configs to use cases (PDFs, exports, raw source uploads) with fallback logic.
4. `StorageConfigurationValidator` enforces cross-cutting business rules (duplicate names, conflicting defaults, quota guardrails) before commit; violations surface as typed errors consumable by UI.
4. Providers in initial release:
   - **LocalFilesystemProvider**: validates absolute paths, ensures permissions, produces `file://` URLs (or signed local proxies when exposed via backend).
   - **GoogleCloudStorageProvider**: uses credential references stored in Secret Manager; runtime clients live in infrastructure.
5. Extension hooks: CLI + documentation instruct new provider implementers to add plugin + typed config model, register in registry, and optionally add UI card.
6. Dependency-injection container (e.g., `StorageContainer`) wires registry, repositories, and services for FastAPI startup so presentation layers never instantiate providers directly.
7. Storage error taxonomy standardized through domain exceptions:

```python
class StorageOperationError(Exception): ...
class StorageConnectionError(StorageOperationError): ...
class StorageQuotaError(StorageOperationError): ...
class StorageValidationError(StorageOperationError): ...
```

### Other Data Sources Integration
- The plugin API must expose `StorageUseCase.RAW_SOURCE` so ingestion jobs (e.g., ClinVar, OMIM) can store raw payloads, parsed CSV/JSON exports, and attached PDFs uniformly.
- Data Source templates will declare storage needs via typed fields, allowing Source Management flows to resolve the correct backend at runtime.

## 7. Advanced Discovery Configuration
### Unified Parameter System
- Extend the existing `QueryParameters` entity with `AdvancedQueryParameters` mixin so PubMed, ClinVar, UniProt, or future connectors can opt into additional filters.
- Each data source declares supported `QueryParameterCapabilities` (gene, phenotype, publication filters, boolean queries, etc.) in metadata consumed by the UI to enable or disable fields.

### PubMed Enhancements
- Add advanced filters (date range, publication type, language, sort, max results, additional terms) to `AdvancedQueryParameters`.
- Provide query preview + validation service `PubMedQueryBuilder` inside the application layer.
- Store presets in `data_discovery_sessions.pubmed_search_config` using the typed model.

### Other Sources
- Example: ClinVar advanced search uses severity, review status, clinical significance filters from `src/type_definitions/external_apis.py`; unify via the same preset workflow.

## 8. Presentation Layer (Next.js) Requirements
- **Server Components**: Settings and Discovery pages fetch typed data through server loaders and dehydrate React Query caches, matching the architecture in `docs/frontend/EngenieeringArchitectureNext.md`.
- **Client Components**: Provider cards, configuration forms, connection tests, and preset modals consume hydrated queries; optimistic updates use React Query mutations.
- **Storage Tab UI**:
  1. Providers overview (status badges, capabilities, default use cases).
  2. Configuration drawer per provider with typed form schema mirrored from backend models, including preset templates for common deployments.
  3. "Test connection" button calls `/api/admin/storage/configurations/{id}/test`; loading states & toast feedback.
  4. Usage dashboard with SSR prefetched stats + charts, capacity forecasting, and configuration bulk actions (enable/disable multiple defaults).
- **Discovery Modal UI**:
  - Parameter groups (Basics, Filters, Output) with contextual help texts pulled from domain metadata.
  - Preview generated PubMed query + storage target.
  - Preset management (save, load, delete) with server validation.
  - Optional sharing scope selector (per-user vs. research-space) behind a feature flag pending policy decision.

## 9. API & Persistence Changes
### Alembic Migrations
- `storage_configurations` (UUID PK, provider enum, config JSONB, capabilities array, default use cases array, created/updated timestamps, audit columns).
- `storage_operations` (log table with operation type, storage key, file size, status, error message, metadata JSONB).
- `data_discovery_sessions.pubmed_search_config` (JSONB storing `AdvancedQueryParameters`).
- Migration scripts include rollback plans and data backfills:

```sql
UPDATE data_discovery_sessions
SET pubmed_search_config = jsonb_build_object('max_results', 100, 'sort_by', 'relevance')
WHERE pubmed_search_config IS NULL;
```

Each migration doc outlines downgrade steps and validation queries to ensure config parity.

### FastAPI Routes
| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/admin/storage/configurations` | Create config, returns `ApiResponse[StorageConfigurationModel]` |
| GET | `/api/admin/storage/configurations` | Paginated list |
| PUT | `/api/admin/storage/configurations/{id}` | Update |
| DELETE | `/api/admin/storage/configurations/{id}` | Soft delete/disable |
| POST | `/api/admin/storage/configurations/{id}/test` | Execute provider test |
| GET | `/api/admin/storage/stats` | Storage usage + health |
| POST | `/api/data-discovery/pubmed/search` | Advanced search |
| GET | `/api/data-discovery/pubmed/search/{id}` | Polling |
| POST | `/api/data-discovery/pubmed/presets` | Save preset |
| GET | `/api/data-discovery/pubmed/presets` | List presets |
| POST | `/api/data-discovery/pubmed/download` | Trigger PDF download with storage destination |
- Similar preset + storage endpoints become available for other connectors through `DiscoveryConfigurationService` and will reuse the same typed responses.

## 10. PDF & Export Automation
- `PDFDownloadService` orchestrates PubMed/PMC downloads, storing metadata (`StorageOperationRecord`) and linking files to `data_discovery_sessions`.
- File paths follow `/discovery/{source}/{yyyy}/{mm}/{dd}/{identifier}.pdf` with metadata stored in JSON.
- Retry policy w/ exponential backoff; failure events log to audit table + emit monitoring alerts.
- For other sources, ingestion pipelines call `StorageConfigurationService.get_backend_for(StorageUseCase.RAW_SOURCE)` to persist raw payloads or exports.
- Rate-limited API clients (PubMed, ClinVar, UniProt) wrap existing services to enforce per-provider quotas and expose telemetry hooks.

## 11. Monitoring, Security, and Audit
- Audit logging appended whenever configs change, tests run, or files stored (`storage_operations` linking to user IDs from auth middleware).
- Storage provider credentials come from secure settings (Secrets Manager or encrypted env vars); UI never exposes secrets beyond masked display.
- PubMed + other API calls respect rate limits; errors bubble through typed `ApiErrorResponse` objects.
- Observability dashboards track success/failure per provider, throughput, and latency.

## 12. Testing Strategy
| Layer | Tests |
| --- | --- |
| Domain | Unit tests for plugin protocol conformance, typed validators (including property-based tests for configs). |
| Application | Service tests covering config CRUD, fallback logic, advanced query builders, PDF download orchestration. |
| Infrastructure | Integration tests hitting local FS, emulator-based GCS, PubMed sandbox/mock server, plus contract tests for other data sources. |
| Presentation | Playwright + React Testing Library for storage tab + discovery modal flows, ensuring hydration pattern compliance. |
| Performance | Upload/download benchmarks (100 MB files <10s), search stress tests, concurrent plugin operations (≥10). |

## 13. Rollout Plan
1. **Phase 1 – Storage Platform (Weeks 1-2)**
   - Domain contracts, registry, LocalFilesystem provider, migrations, admin APIs, backend tests.
2. **Phase 2 – Cloud Providers (Week 3)**
   - Google Cloud Storage plugin, credential wiring, integration tests.
3. **Phase 3 – Next.js Settings UI (Week 4)**
   - Storage tab, forms, stats, configuration preset templates, bulk actions, feature flag for beta.
4. **Phase 4 – Advanced Discovery (Weeks 5-6)**
   - PubMed parameter extensions, presets, PDF automation to storage, capability-driven UI toggles.
5. **Phase 5 – Cross-Source Adoption (Weeks 7-8)**
   - ClinVar/UniProt/Custom sources adopt storage + presets, add UI sections where applicable, optional preset sharing by research space.
6. **Phase 6 – Hardening (Weeks 9-10)**
   - End-to-end testing, monitoring dashboards, documentation + training.

## 14. Open Questions
1. Which additional provider should follow GCS (e.g., AWS S3 vs. Azure Blob) based on partner demand?
2. Do we require multi-region replication for storage assets at launch, or can it follow in a later milestone?
3. Should preset sharing span research spaces (requiring new permission models), or remain per-user in Phase 1?

---
**Deliverable:** All teams follow this PRD for implementation and testing so storage, discovery, and PDF automation stay tightly aligned with MED13 Clean Architecture and strict type-safety standards.
