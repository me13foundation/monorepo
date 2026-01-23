Here is the detailed **Engineering Implementation Plan** to evolve the MED13 Resource Library into a **Translational AI Platform**.

This plan follows **Clean Architecture principles** and assumes a **Postgres-backed graph model with NetworkX traversal** for Phases 1-4. The storage choice is intentionally swappable; a TypeDB migration remains a **future option** if graph semantics or scale demand it.

## Goals alignment (explicit)

- Mechanistic reasoning (Variant -> ProteinDomain -> Mechanism -> Phenotype) is the primary graph path.
- Hypotheses are human-verifiable and never auto-promoted to truth.
- The graph is the system of record with provenance and curation status on every edge.
- Agent assistance is bounded, auditable, and cannot write to validated data directly.
- Clinical and scientific credibility is enforced via audit logging, evidence transparency, and review workflows.

## Graph service strategy

- Initial implementation lives inside the existing FastAPI backend as an application service.
- Expose a stable graph API contract (`/api/graph/export`, `/api/graph/neighborhood`, `/api/hypotheses`) so clients are insulated from storage changes.
- Postgres remains the system of record; NetworkX is used for traversal and export.
- Extraction to an independent service is optional and only justified by scale, latency, or external consumer needs.
- Any future TypeDB migration must preserve the API contract.

## Implementation status (as of January 23, 2026)

**Legend:** DONE | PARTIAL | PLANNED

### Phase 1: Ontology
- **Drug entity** DONE (`src/domain/entities/drug.py`)
- **Pathway entity** DONE (`src/domain/entities/pathway.py`)
- **ProteinDomain value object** DONE (`src/domain/value_objects/protein_structure.py`)
- **Mechanism entity** PLANNED (not yet implemented)
- **Variant schema enhancements** DONE (structural annotation + in-silico scores in `src/domain/entities/variant.py`)
- **Phenotype longitudinal observations** DONE (`src/domain/entities/phenotype.py`)

### Phase 2: Atlas ingestion
- **UniProt domain extraction** PLANNED (parser exists, but domains are not mapped into `ProteinDomain` or persisted)
- **PubMed research corpus + extraction** PARTIAL (ingestion queues publications and a placeholder runner marks items skipped; real extraction logic is pending)
- **Drug/Pathway seeding** PLANNED (no seed files or seeding service yet)
- **Repository/DB JSON fields** PLANNED (DB models/migrations do not yet store structural annotation or longitudinal observations)

### Phase 3: Knowledge graph core
- **GraphService + Postgres node/edge storage** PLANNED (not implemented)
- **Graph API endpoints** PLANNED (no `/api/graph/*` routes yet)

### Phase 4: AI engine + UI
- **Hypothesis scoring / inference services** PLANNED (not implemented)
- **Knowledge graph UI** PARTIAL (route exists but is a placeholder page)

---

# MED13 Translational AI Platform: Engineering Implementation Plan

## **Phase 1: The Ontology (Domain Layer Expansion)**
**Goal:** Formally define the biological entities required for mechanism modeling and therapeutic discovery. We move beyond "Variant Registry" to "System Biology Model."

### **1.1 New Domain Entities**
We must introduce three new core entities to the `src/domain/entities/` module.

*   **`Drug` (Therapeutic Agent)**
    *   **Purpose:** Represents small molecules, ASOs, or gene therapies.
    *   **Attributes:** `id` (DrugBank/PubChem), `name`, `mechanism_of_action` (e.g., "CDK8 inhibitor"), `brain_penetrance` (Boolean), `approval_status` (FDA/EMA).
    *   **File:** `src/domain/entities/drug.py`

*   **`Pathway` (Biological Context)**
    *   **Purpose:** Represents the functional networks MED13 regulates (e.g., "Wnt signaling", "Mitochondrial metabolism").
    *   **Attributes:** `id` (Reactome/GO), `name`, `gene_set` (List of Gene IDs).
    *   **File:** `src/domain/entities/pathway.py`

*   **`ProteinDomain` (Structural Context)**
    *   **Purpose:** Defines the physical regions of the MED13 protein.
    *   **Attributes:** `name` (e.g., "Cyclin C binding interface"), `start_residue`, `end_residue`, `3d_coordinates` (AlphaFold JSON), `function`.
    *   **Usage:** Value Object embedded within `Gene` or linked to `Variant`.

*   **`Mechanism` (Causal Link)**
    *   **Purpose:** Represents a biological mechanism that bridges variants/domains to phenotypes.
    *   **Attributes:** `id`, `name`, `description`, `evidence_tier`, `confidence_score`.
    *   **Usage:** Node type in the graph, backed by evidence with provenance.

### **1.2 Expanded Mechanism & Outcome Entities (Sprint 3)**
To fully capture the disease mechanism, we will add these entities in the next phase:

*   **`ProteinInteraction` (PPI)**
    *   **Purpose:** Explicitly models binding events (e.g., MED13-Cyclin C).
    *   **Attributes:** `protein_a`, `protein_b`, `binding_affinity` (Kd), `evidence_type` (Co-IP, Yeast 2-Hybrid).

*   **`TranscriptionalTarget`**
    *   **Purpose:** Genes whose expression is regulated by MED13.
    *   **Attributes:** `target_gene`, `regulation_direction` (Up/Down), `fold_change`, `context` (Cell Type).

*   **`CellularContext`**
    *   **Purpose:** Defines the biological environment where a phenotype occurs.
    *   **Attributes:** `cell_type` (e.g., GABAergic Neuron), `developmental_stage` (e.g., E14.5), `tissue`.

### **1.3 Hypothesis and Curation Entities (Sprint 3)**
To enable human-verifiable hypotheses, we will add explicit structures for review and provenance:

*   **`Hypothesis`**
    *   **Purpose:** Stores proposed mechanistic paths with evidence and contradictions.
    *   **Attributes:** `id`, `summary`, `support_score`, `contradiction_score`, `net_score`, `status`.

*   **`ReviewDecision`**
    *   **Purpose:** Captures human validation events.
    *   **Attributes:** `reviewer_id`, `decision`, `notes`, `reviewed_at`.

### **1.4 Enhance Existing Entities**
*   **Refactor `Variant` (`src/domain/entities/variant.py`)**
    *   **Add `StructuralAnnotation`:** Links a variant to specific `ProteinDomains` (e.g., "Variant R123X is in the IDR region").
    *   **Add `InSilicoScores`:** Fields for `cadd_phred`, `revel`, `alpha_missense` (critical for AI classification).
    *   **Add `FunctionalPrediction`:** Field for `predicted_consequence` (e.g., "Haploinsufficiency" vs "Dominant Negative").

*   **Refactor `Phenotype` (`src/domain/entities/phenotype.py`)**
    *   **Add `LongitudinalData`:** Support for time-series observations (Age of onset, severity progression) to enable Natural History modeling.

---

## **Phase 2: The "Atlas" (Ingestion & Enrichment) - Sprint 2**
**Goal:** Build the "Smart Scout" infrastructure to ingest, analyze, and persist high-fidelity scientific data (Structural, Clinical, Therapeutic).

### **2.1 Structural Biology Ingestion (UniProt)**
*   **Task:** Upgrade `UniProtIngestor` to extract `ProteinDomain` data.
*   **Implementation:**
    *   Parse `features` list in UniProt XML/JSON.
    *   Extract types: `domain`, `region`, `binding site`, `active site`.
    *   Map to `ProteinDomain` Value Object with coordinates.
*   **Success Criteria:** `Gene` entities in the DB have populated `structural_annotation` fields.

### **2.2 AI-Driven Literature Extraction (PubMed "Scout")**
*   **Task:** Transform PubMed ingestion into a "Research Corpus" builder.
*   **Implementation:**
    *   **Raw Storage:** Upgrade `PubMedIngestor` to save full JSON/XML content to `storage/raw/pubmed/`.
    *   **Analysis Queue:** Create a mechanism (e.g., `analysis_status` flag or DB table) to mark papers as "Ready for Extraction."
    *   **Entity Extraction (MVP):** Implement basic regex/rule-based extraction for:
        *   **Variants:** `c.\d+[A-Z]>[A-Z]`, `p.[A-Z][a-z]{2}\d+[A-Z][a-z]{2}`
        *   **Phenotypes:** Match against HPO term list.
        *   **Drugs:** Match against a seed list of known compounds.
*   **Success Criteria:** System can identify "Paper X contains Variant Y and Drug Z."

### **2.3 Therapeutic Atlas Seeding**
*   **Task:** Populate the `Drug` and `Pathway` tables.
*   **Implementation:**
    *   Create `DrugSeedingService` to load a curated JSON list (`data/seeds/drugs.json`).
    *   **Seed Scope:**
        *   CDK8 Inhibitors (e.g., Cortistatin A, Senexin B).
        *   Broad-spectrum Neuro-drugs (e.g., Valproic Acid, Levetiracetam).
        *   Gene Therapy Vectors (AAV serotypes relevant to CNS).
*   **Success Criteria:** `DrugRepository` contains >20 validated therapeutic candidates.

### **2.4 Repository Layer Upgrades**
*   **Task:** Update SQLAlchemy models to support complex JSON fields.
*   **Implementation:**
    *   Update `VariantModel` to store `structural_annotation` and `in_silico_scores` as JSONB.
    *   Update `PhenotypeModel` to store `longitudinal_observations` as JSONB.
    *   Ensure full round-trip type safety (Pydantic <-> SQLAlchemy).

---

## **Phase 3: The Knowledge Graph (Application & Infrastructure)**
**Goal:** Connect the isolated entities into a traversable network to enable hypothesis generation.

### **3.1 Graph Service (`src/application/services/graph_service.py`)**
This is the core engine. It orchestrates the retrieval of data from Repositories and constructs the Graph.

*   **Responsibility:**
    1.  Fetch all `Variants`, `Phenotypes`, `Domains`, `Mechanisms`, `Drugs`.
    2.  Construct Nodes for each.
    3.  Construct Edges based on business rules with provenance and curation status:
        *   `Variant` --(*causes*)--> `Phenotype`
        *   `Variant` --(*located_in*)--> `ProteinDomain`
        *   `ProteinDomain` --(*impacts*)--> `Mechanism`
        *   `Mechanism` --(*explains*)--> `Phenotype`
        *   `Drug` --(*targets*)--> `Pathway`/`Gene`
        *   `Gene` --(*interacts_with*)--> `Gene` (PPI)

### **3.2 Graph Implementation (Infrastructure)**
*   **MVP (Postgres + NetworkX):**
    *   Store nodes and edges in Postgres tables as the system of record.
    *   Include provenance, evidence references, and curation status on edges.
    *   Build the graph in-memory using Python's `networkx` library for traversal and export.
    *   Fast, easy to debug, perfect for exporting to JSON for the frontend/public.
    *   **Output:** `med13_knowledge_graph.json` (Node-Link format).

*   **Future option (TypeDB/Neo4j):**
    *   Optional migration if Postgres + NetworkX hits scale or semantic constraints.
    *   See `docs/world_model/TypeDb_plan.md` for a future migration concept (not current execution).

### **3.3 Public API (`src/routes/graph.py`)**
*   **Endpoint:** `GET /api/graph/export`
    *   Returns the full JSON graph. This enables "Open Science" - researchers can download our model and run their own algorithms.

---

## **Phase 4: The AI Engine (Inference Layer)**
**Goal:** Use the Graph to answer questions.

### **4.1 Variant Classifier (`VariantClassificationService`)**
*   **Input:** A `Variant` with its `StructuralAnnotation` and `InSilicoScores`.
*   **Logic:**
    *   *Level 1 (Rules):* If `impact` is "High" and `clinvar` is "Pathogenic", label as "Loss of Function".
    *   *Level 2 (ML):* Train a classifier (Random Forest/Gradient Boost) on the Graph features to predict pathogenicity for VUS (Variants of Uncertain Significance).

### **4.2 Therapeutic Hypothesis Generator (`DrugRepurposingService`)**
*   **Logic:** Graph Traversal.
    *   Identify `Pathways` disrupted by pathogenic variants.
    *   Find `Drugs` that target these pathways (or inverse-target them).
    *   Rank candidates based on `safety` and `brain_penetrance`.

### **4.3 Hypothesis Evaluation (`HypothesisScoringService`)**
*   **Logic:** Evidence aggregation with explicit contradictions.
    *   Compute support, contradiction, and net scores.
    *   Emit human-readable mechanism reports with citations.
    *   Require human review before promotion to validated knowledge.

---

## **Risk Assessment & Mitigation**

### **Risk 1: Circular Dependencies in Domain Model**
*   **Description:** Tightly coupling `Variant`, `Gene`, and `ProteinDomain` can lead to Python circular import errors, especially when defining relationships (e.g., Variant -> Domain -> Variant).
*   **Mitigation:**
    *   Use `src/domain/value_objects/` for shared structures like `ProteinDomain` that don't require their own identity.
    *   Utilize `TYPE_CHECKING` blocks and string forward references (`"Variant"`) in Pydantic models.
    *   Strictly enforce unidirectional dependencies in the core domain where possible.

### **Risk 2: Graph Service Scalability**
*   **Description:** Loading the entire knowledge graph into memory (NetworkX) could become a bottleneck if the dataset grows significantly (e.g., including all genome-wide interactions).
*   **Mitigation:**
    *   **MVP Scope:** Limit the initial graph to MED13-specific interactions (~100k nodes), which easily fits in memory.
    *   **Future Scaling:** The architecture allows an optional migration of `GraphService` from NetworkX to a dedicated graph database (TypeDB/Neo4j) without changing the API contract.
    *   **Pagination:** Implement subgraph querying (e.g., `get_neighborhood(node_id, depth=1)`) instead of full-graph dumps for UI endpoints.

### **Risk 3: Data Quality Propagation**
*   **Description:** "Garbage in, garbage out." Integrating noisy data from automated extraction (NLP) or uncurated public sources could pollute the graph.
*   **Mitigation:**
    *   **Confidence Scoring:** Every edge in the graph must have a `confidence_score` (0.0-1.0) and `provenance` trace.
    *   **Source Tiering:** Prioritize "Gold Standard" sources (Curated ClinVar, Manually Verified Papers) over "Silver/Bronze" sources (Automated Mining) in the inference engine.

---

## **Execution Roadmap (Sprints)**

| Sprint | Focus | Key Deliverables |
| :--- | :--- | :--- |
| **Sprint 1** | **Ontology** | `Drug`, `Pathway`, `ProteinDomain`, `Mechanism` entities created. `Variant` schema updated. |
| **Sprint 2** | **Atlas Data** | `UniProtIngestor` upgraded to fetch Domains. `Variant` repository updated to store new fields. |
| **Sprint 3** | **Graph Core** | `GraphService` implemented with `networkx`. `GET /graph/export` endpoint live. Hypothesis and review scaffolding added. |
| **Sprint 4** | **UI & Public** | "Network Explorer" in Next.js UI (using `react-force-graph`). Public release of the dataset. |

## **Recommendation for "Right Now"**
Start with **Sprint 1 (Ontology)**. Without the rigorous Pydantic models for `Drug`, `Pathway`, and `Structure`, the AI has no data structure to operate on.

Shall I generate the code for **Sprint 1 (The New Entities)** now?
