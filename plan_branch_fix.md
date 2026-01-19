# Plan

I will shift space discovery to server-orchestrated data and Server Actions, remove client-derived business logic, align TS types with generated DTOs, move auth mutations to Server Actions, and eliminate `cast(...)` in tests by using typed stubs. This addresses the architecture compliance issues while minimizing behavioral change.

## Scope
- In: Space discovery UI refactor, new Server Actions for discovery/auth, generated-type alignment, test stub typing, test updates/validation.
- Out: Broad refactors of unrelated React Query flows or backend API redesigns beyond what is needed for orchestration.

## Action items
[x] Refactor space discovery UI to accept server-orchestrated state and remove React Query hooks (`src/web/components/data-discovery/DataDiscoveryContent.tsx`, `src/web/components/data-discovery/SourceCatalog.tsx`, `src/web/components/data-sources/DiscoverSourcesDialog.tsx`, `src/web/app/(dashboard)/spaces/[spaceId]/data-sources/page.tsx`).
[x] Add Server Actions for space discovery orchestration (ensure/create session, fetch orchestrated state + catalog, update selection, add-to-space) and wire them into the UI.
[x] Align `src/web/lib/types/data-discovery.ts` with generated DTOs (type aliases/re-exports) and adjust imports where needed.
[x] Replace auth page `fetch` calls with Server Actions (`src/web/app/auth/register/page.tsx`, `src/web/app/auth/forgot-password/page.tsx`).
[x] Remove client-side PubMed defaults when adding discovery sources; rely on backend config generation.
[x] Remove `cast(...)` usage in ingestion scheduling tests by implementing stub repositories/services that conform to domain interfaces (`tests/unit/application/test_ingestion_scheduling_service.py`).
[x] Update affected frontend tests (DataDiscoveryContent/DiscoverSourcesDialog).
[x] Run targeted checks (architectural validator + unit tests).

## Open questions
- Use the existing `/data-discovery/sessions/{id}/state` orchestrator for space discovery.
- Keep auth pages as client components for forms; mutations move to Server Actions.
