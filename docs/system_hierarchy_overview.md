# MED13 System Hierarchy Overview

This guide outlines the major areas of the MED13 admin platform and how they relate to one another. Use it to decide where a new workflow or feature should live.

```
┌───────────────────────────┐
│  System Settings          │
│  (/system-settings)       │
│  Global catalog controls  │
└────────────┬──────────────┘
             │
             │
┌────────────▼──────────────┐        ┌───────────────────────────┐
│      Dashboard            │        │   Data Discovery           │
│      (/dashboard)         │        │   (/data-discovery)        │
│  Metrics & navigation     │        │  Catalog exploration       │
└────────────┬──────────────┘        └────────────┬──────────────┘
             │                                     │
             │                                     │
             ▼                                     ▼
      ┌────────────────────────────┐    ┌─────────────────────────┐
      │  Research Spaces           │    │  Space-specific tabs     │
      │  (/spaces/{id}/…)          │    │  Data Sources / Members  │
      └────────────────────────────┘    └─────────────────────────┘
```

## 1. Global Admin Settings (`/system-settings`)
- **Audience**: Foundation administrators
- **Purpose**: Configure platform-wide defaults (catalog availability, template libraries, compliance switches).
- **Notes**: Changes apply to all research spaces unless overridden locally—ideal for governance or licensing controls.

## 2. Data Discovery (`/data-discovery`)
- **Audience**: Curators/researchers exploring the catalog
- **Purpose**: Filter, search, and preview data sources using gene/phenotype criteria; view availability before selecting a source.
- **Notes**: Read-focused workflow. Shows global + per-space availability but does not mutate space settings.

## 3. Research Space Management (`/spaces/{spaceId}/…`)
- **Audience**: Curators operating within a specific research space
- **Purpose**: Manage the space’s data sources, curation workflows, membership, and settings.
- **Key tabs**:
  - **Data Sources**: Configure ingestion schedules, trigger manual runs, inspect ingestion history (new scheduling UI lives here).
  - **Data Curation**: Operate the curation pipeline.
  - **Members**: Invite/remove collaborators.
- **Notes**: All per-space mutations belong here. Scheduling, quality metrics, and telemetry sit under the Data Sources tab.

## 4. System Dashboard (`/dashboard`)
- **Audience**: Admin overview
- **Purpose**: Display KPIs (source counts, ingestion status, system health) and link into the workflows above.
- **Notes**: Read-only metrics; actionable links route to Discovery or Research Space tabs.

## Placement Guidelines
- Use **System Settings** for platform-level levers or compliance requirements.
- Use **Data Discovery** for catalog exploration, comparison, and reporting.
- Use **Research Space** tabs for anything that configures, runs, or audits a specific space’s data sources.
- Keep the **Dashboard** focused on monitoring and navigation—not direct configuration.
