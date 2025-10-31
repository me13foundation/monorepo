MED13 Resource Library: Phase 0 – Developer Guide
This document describes Phase 0 of the MED13 Knowledge Base project. Phase 0 is a curated resource library: it collects, cleans and organizes all publicly available MED13-related data. The goal is not to build a final reasoning graph but to prepare high‑quality, FAIR‑compliant packages for Phase 1. These packages will feed into the TypeDB-based Knowledge Graph in later phases.
Objectives
Aggregate validated information about MED13 variants, phenotypes and supporting evidence into a single, well-documented resource library.
Normalize and clean data from multiple sources, assign stable identifiers and track provenance.
Package data following the FAIR principles (Findable, Accessible, Interoperable, Reusable) using the RO‑Crate standard.
Provide a simple internal curation interface for subject-matter experts (SMEs) to review, annotate and approve entries.
Publish regular snapshots (with DOIs) so researchers and clinicians can download and reuse the data.
Acknowledge that Phase 0 is a preparatory library; the relational store will be discarded or migrated in Phase 1 when the knowledge graph is built.
Data Sources
We compile data from trusted biomedical resources:
ClinVar / ClinGen: variant interpretations and curation status.
Human Phenotype Ontology (HPO): standard phenotype terms and hierarchies.
PubMed / LitVar: literature references linking MED13 variants to phenotypes.
OMIM / Orphanet: gene–disease associations for rare disorders.
Gene Ontology (UniProt optional): gene function annotations.
Crossref / Crossmark: article metadata and retraction status.
Other ontologies (optional): e.g. GO, DOID for additional context.
Each source is ingested via official APIs or bulk files to ensure reproducibility. Licensing metadata is recorded for every source to respect redistribution rights.
Data Model
Phase 0 stores data in simple relational tables. Each table represents an entity or relationship. Filterable attributes are top‑level columns; unstructured metadata is kept in a JSONB field.
Table
Key Columns
Description
genes
gene_id, symbol
Unique gene identifier and basic metadata.
variants
variant_id, gene_id, hgvs, clinvar_id
Sequence variants of MED13 linked to the gene.
phenotypes
hpo_id, label, definition
Phenotype terms from HPO.
publications
pub_id, doi, pmid, title
Literature references from PubMed or Crossref.
evidence
evidence_id, variant_id, hpo_id, source, evidence_level, curation_status, summary, provenance
Links variants to phenotypes with supporting references; filterable fields are columns, and raw metadata is stored in the provenance JSONB column.

Technology Stack
Layer
Tool
Rationale
ETL & validation
Python  , Pydantic models, pytest
Strong typing and testable transformations.
Metadata store
PostgreSQL with JSONB or Google Cloud Storage (CSV/JSON)
Simple and scalable for storing cleaned data.
Packaging & publishing
RO‑Crate (JSON‑LD), Zenodo DOIs
Ensures FAIR compliance and persistent identifiers.
API layer
FastAPI with OpenAPI/GraphQL schema
Exposes read‑only endpoints for public access; supports ?include_text parameter to respect licenses.
Internal curation UI
Plotly Dash (Python)
Provides interactive dashboards and tables for SMEs. Streamlit is another data‑app option but is less customizable than Dash (evidence.dev).
Public portal
Next.js (React)
Used to build a polished, SEO‑friendly website that consumes the API. This framework allows full customization and user‑experience control (tianye.org).
Model demo widgets (future)
Gradio
Optional for Phase 1 demos of AI‑powered extraction; Gradio excels at wrapping ML models but is not suitable as the main dashboard (evidence.dev).



Deployment Model – Two Services
To make the architecture explicit, Phase 0 is delivered as two separate services:
Python back‑end / API service (api.med13foundation.org): Implements ETL jobs, validation, packaging, and provides REST/GraphQL endpoints. Deployed on Cloud Run or a similar platform. All authentication and RBAC live here.
Next.js front‑end service (med13foundation.org): Serves the public and curation web pages. Fetches data from the API using HTTPS. Handles site branding, SEO, multi‑language support and navigation. A dedicated subpath or subdomain can host the knowledge‑base pages (e.g., med13foundation.org/knowledge-base).
This separation improves security and scalability: the front‑end never touches the database directly and can be redeployed independently of the ETL and API layer.
ETL Pipeline
The extraction–transformation–loading process comprises several stages:
Ingest: Download or query data from each source (ClinVar, HPO, PubMed, OMIM, etc.) and save raw files with timestamps.
Transform: Normalize identifiers, parse records into Pydantic models and map variant‑phenotype‑publication relations.
Validate: Run syntactic checks (ID patterns), completeness checks (row counts), referential integrity (foreign keys), transformation correctness (e.g. map ClinVar significance to evidence levels) and semantic checks (flag nonsensical phenotype links).
Curate: Present new records in the internal dashboard for SME review; curators can approve or reject evidence and add comments.
Package: Generate RO‑Crate packages that include cleaned tables, provenance metadata, licensing information and a licenses.yaml manifest.
Publish: Upload each release to Zenodo or a similar repository, mint a DOI and update the public portal.
Validation & Governance
Governance board: A small panel of clinical geneticists, bioinformaticians and ethicists oversees curation policies and resolves disputes.
Role‑based access: Public users can read data; only authenticated curators can edit or validate records.
Audit trail: Every curation action (approve/reject) logs the user ID, timestamp and change in an audit table.
Licensing compliance: Each data source has a license entry specifying redistribution rules. Text or annotations from proprietary sources (OMIM, SNOMED) are never redistributed; only IDs and links are shared.
Security measures: All services run behind HTTPS with OAuth2 authentication. Data at rest uses encryption (e.g. Cloud SQL encryption). Backups and recovery procedures are documented.
User‑centered design: Interviews with clinicians and researchers inform the dashboard workflow; usability is measured via standard surveys.
Packaging & Attribution
RO‑Crate metadata: The ETL pipeline creates a ro-crate-metadata.json file describing the dataset, authors, creation date and context. It conforms to the RO‑Crate 1.1 specification.
Licenses file: A licenses.yaml file lists each source with fields: license_name, license_url, attribution_text, redistribution_ok, commercial_ok, share_alike and notes. This ensures transparency and helps downstream users respect licensing.
API controls: The public API implements an ?include_text flag. When false (default), any proprietary text is replaced with a notice; when true, the API returns full text only for sources that allow redistribution.
Phase 0 → Phase 1 Interface
Phase 0’s output is not a direct database migration; it is a data export used as input for the Phase 1 knowledge graph.
Each validated record is exported as structured JSON or CSV aligned with a draft TypeDB schema.
A type_map.yaml defines how Phase 0 fields map to TypeDB entities, attributes and relations.
The Phase 1 ETL reads RO‑Crates, applies the mapping and loads data into TypeDB. There is no expectation of reusing Phase 0 SQL queries or repository classes.
This decoupling eliminates the conceptual mismatch between relational and graph models.
Strategic Options
To guide stakeholders, we acknowledge two paths:
Graph‑Native (Recommended): Use TypeDB from the start for both Phase 0 and Phase 1. This eliminates migration overhead and ensures that the schema evolves organically. However, it requires the team to learn TypeDB early.
Relational Prototype (High‑Risk): Use PostgreSQL for Phase 0 because of team familiarity. Accept that the Phase 0 data tier will be discarded after the resource library is created. Plan and budget a full rewrite for Phase 1.
Phase 0 has been reframed as a resource library that prepares the data for either path.
Summary
The MED13 Resource Library (Phase 0) consolidates high‑quality information about MED13 into a FAIR package. It provides curated data to clinicians and researchers, records provenance and licensing, and prepares exports for the future graph‑based discovery system. This foundation ensures that subsequent phases can focus on causal reasoning and AI‑driven insights rather than basic data collection and cleaning.
