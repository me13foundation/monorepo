# Release Notes Draft - Unified Storage & Advanced Literature Discovery

## 🚀 Feature Release: Storage Platform & Advanced Discovery

This release introduces the Unified Storage Platform for managing data persistence across multiple backends (LocalFS, GCS, S3) and the Advanced Discovery Module for reproducible PubMed literature searches.

---

## 🌟 New Features

### Unified Storage Platform
*   **Storage Configuration Management**: Admin UI to create, test, and manage storage backends.
*   **Multi-Provider Support**: First-class support for Local Filesystem and Google Cloud Storage.
*   **Health Monitoring**: Real-time connection testing and usage statistics.
*   **Maintenance Mode**: Ability to disable specific storage configurations to prevent writes during maintenance.
*   **Audit Logging**: All storage operations (upload/download/delete) are auditable.

### Advanced Literature Discovery
*   **PubMed Integration**: Search PubMed using advanced filters (date range, article type, etc.).
*   **Discovery Presets**: Save complex search queries as presets (User-scoped or Space-scoped).
*   **PDF Automation**: One-click retrieval of full-text PDFs for search results.
*   **Space-Scoped Discovery**: Research spaces now have dedicated discovery sessions and catalog settings.

---

## 🛠 Technical Changes

### Feature Flags
*   `ENABLE_ADVANCED_DISCOVERY`: Enables the new discovery UI and API endpoints. (Default: `true`)
*   `ENABLE_STORAGE_DASHBOARD`: Enables the storage configuration admin panel. (Default: `true`)
*   `ENABLE_PDF_AUTOMATION`: Enables the background worker for PDF fetching. (Default: `true`)

### Migrations
*   **Alembic Revisions**:
    *   `add_storage_configurations_table`: Creates `storage_configurations` table.
    *   `add_discovery_presets_table`: Creates `discovery_presets` table.
    *   `add_storage_operation_records`: Creates audit table for storage ops.

### API Changes
*   **New Endpoints**:
    *   `/api/admin/storage/*`: Storage management.
    *   `/api/data-discovery/pubmed/presets`: Preset CRUD.
    *   `/api/data-discovery/pubmed/download`: PDF automation.
*   **Updated Endpoints**:
    *   `/api/data-discovery/sessions`: Now supports `AdvancedQueryParameters`.

---

## 🔄 Rollback Plan

### Database
If a rollback is required, revert the Alembic migrations:

```bash
alembic downgrade -3  # Revert storage, presets, and operation records
```

### Feature Flags
To disable features without code rollback, set the following environment variables:

```bash
export ENABLE_ADVANCED_DISCOVERY=false
export ENABLE_STORAGE_DASHBOARD=false
export ENABLE_PDF_AUTOMATION=false
```

### Data Persistence
*   **Storage Configurations**: Soft-deleted configurations can be restored directly in the DB if needed (`deleted_at = NULL`).
*   **Files**: Files written to storage backends are **NOT** deleted during a code rollback. They remain in the configured buckets/directories.
