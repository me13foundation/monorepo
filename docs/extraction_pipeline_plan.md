# Extraction Pipeline Plan (PubMed Immediate Post-Ingestion)

**Status date:** January 23, 2026
**Owner:** Platform Engineering (overall)
**Scope:** Queue + immediate post-ingestion wiring + MVP extraction outputs.

---

## Objective

Deliver an immediate post-ingestion extraction pipeline that safely queues
publications for extraction, supports concurrent ingestion runs, and prevents
duplicate processing. MVP extraction logic is rule-based and designed to be
extended to full-text extraction later.

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
| T7 | Extraction runner and processor port | Data/AI Eng | DONE | Placeholder processor + runner |
| T8 | MVP extraction rules (variants, phenotypes) | Data/AI Eng | DONE | Rule-based PubMed processor |
| T9 | Extraction outputs persistence + API | Backend Eng | DONE | `publication_extractions` table + API |
| T10 | Admin visibility / metrics endpoints | Backend Eng | NOT STARTED | Future phase |
| T11 | Integration tests (queue + extraction) | QA | NOT STARTED | Future phase |

---

## Milestones

- **M1 (Complete):** Queue schema and immediate ingestion hook in place (Postgres verified).
- **M2 (Complete):** Extraction runner processes queued items.
- **M3 (Complete):** MVP extraction outputs persisted and traceable.

---

## Progress Tracking Notes

- Queue records are created immediately after ingestion completes and include
  ingestion job metadata for traceability.
- Postgres smoke test completed (Jan 23, 2026) with queued extraction rows.
- Runner now processes queued items using a rule-based processor and stores
  extraction outputs for reuse and extension to full-text extraction.
