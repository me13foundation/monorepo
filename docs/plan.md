Here is the detailed **Engineering Implementation Plan** to evolve the MED13 Resource Library into a **Translational AI Platform**.

This plan follows **Clean Architecture principles**, ensuring that our Domain Layer (Business Logic) remains independent of specific tools (like TypeDB vs. NetworkX), allowing us to start fast with Python/JSON and scale to a graph database later.

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

### **1.3 Enhance Existing Entities**
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
    1.  Fetch all `Variants`, `Phenotypes`, `Domains`, `Drugs`.
    2.  Construct Nodes for each.
    3.  Construct Edges based on business rules:
        *   `Variant` --(*causes*)--> `Phenotype`
        *   `Variant` --(*located_in*)--> `ProteinDomain`
        *   `Drug` --(*targets*)--> `Pathway`/`Gene`
        *   `Gene` --(*interacts_with*)--> `Gene` (PPI)

### **3.2 Graph Implementation (Infrastructure)**
*   **MVP (NetworkX):**
    *   Build the graph in-memory using Python's `networkx` library.
    *   Fast, easy to debug, perfect for exporting to JSON for the frontend/public.
    *   **Output:** `med13_knowledge_graph.json` (Node-Link format).

*   **Target (TypeDB/Neo4j):**
    *   As per your `TypeDb_plan.md`, we will eventually persist this to a graph DB for complex querying (e.g., "Find all drugs targeting pathways affected by variants in the Cyclin C binding domain").

### **3.3 Public API (`src/routes/graph.py`)**
*   **Endpoint:** `GET /api/graph/export`
    *   Returns the full JSON graph. This enables "Open Science" – researchers can download our model and run their own algorithms.

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
    *   **Future Scaling:** The architecture allows swapping the `GraphService` implementation from NetworkX to a dedicated graph database (TypeDB/Neo4j) without changing the API contract.
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
| **Sprint 1** | **Ontology** | `Drug`, `Pathway`, `ProteinDomain` entities created. `Variant` schema updated. |
| **Sprint 2** | **Atlas Data** | `UniProtIngestor` upgraded to fetch Domains. `Variant` repository updated to store new fields. |
| **Sprint 3** | **Graph Core** | `GraphService` implemented with `networkx`. `GET /graph/export` endpoint live. |
| **Sprint 4** | **UI & Public** | "Network Explorer" in Next.js UI (using `react-force-graph`). Public release of the dataset. |

## **Recommendation for "Right Now"**
Start with **Sprint 1 (Ontology)**. Without the rigorous Pydantic models for `Drug`, `Pathway`, and `Structure`, the AI has no data structure to operate on.

Shall I generate the code for **Sprint 1 (The New Entities)** now?
