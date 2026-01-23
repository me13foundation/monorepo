# Extraction Pipeline Plan (PubMed Immediate Post-Ingestion)

**Status date:** January 23, 2026
**Owner:** Platform Engineering (overall)
**Scope:** Queue + immediate post-ingestion wiring, no extraction logic yet.

---

## Objective

Deliver an immediate post-ingestion extraction pipeline that safely queues
publications for extraction, supports concurrent ingestion runs, and prevents
duplicate processing. Extraction logic itself will be added in a later phase.

---

## Work Breakdown (Tasks, Owners, Status)

**Legend:** DONE | IN PROGRESS | NOT STARTED

| Task ID | Task | Owner | Status | Notes |
| --- | --- | --- | --- | --- |
| T1 | Requirements doc for extraction pipeline | Platform Eng | DONE | `docs/extraction_pipeline_requirements.md` |
| T2 | Extraction queue schema + Alembic migration | Backend Eng | DONE | New `extraction_queue` table |
| T3 | Domain entity + repository interface | Backend Eng | DONE | `ExtractionQueueItem` + repository |
| T4 | SQLAlchemy model + repository implementation | Backend Eng | DONE | Mapper + repository |
| T5 | Application service for queueing | Backend Eng | DONE | `ExtractionQueueService` |
| T6 | Wire immediate post-ingestion hook | Backend Eng | DONE | Ingestion scheduling now enqueues |
| T7 | Extraction runner and processor port | Data/AI Eng | NOT STARTED | Future phase |
| T8 | MVP extraction rules (variants, phenotypes) | Data/AI Eng | NOT STARTED | Future phase |
| T9 | Admin visibility / metrics endpoints | Backend Eng | NOT STARTED | Future phase |
| T10 | Integration tests (queue + ingestion hook) | QA | NOT STARTED | Future phase |

---

## Milestones

- **M1 (Complete):** Queue schema and immediate ingestion hook in place (Postgres verified).
- **M2 (Next):** Extraction runner processes queued items.
- **M3 (Next):** MVP extraction outputs persisted and traceable.

---

## Progress Tracking Notes

- Queue records are created immediately after ingestion completes and include
  ingestion job metadata for traceability.
- Postgres smoke test completed (Jan 23, 2026) with queued extraction rows.
- No extraction logic runs yet; queue items remain pending until T7 is implemented.
