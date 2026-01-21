This is the **Definitive Flujo Production Engineering Manual**. It aggregates every architectural standard, API capability, and best practice discussed, forming a single source of truth for building production-grade AI systems with Flujo.

---

# 📖 Flujo Production Engineering Manual

**Version:** 1.0 (Backend-agnostic; Postgres recommended for durability)
**Philosophy:** State-first when a persistent backend is configured. Per-turn durability requires
`GranularStep` (or `Step.granular`) plus persistence.

---

## 1. Infrastructure & Configuration
Production durability comes from configuring a persistent state backend (Postgres or SQLite).

### 1.1 State Backend
*   **URI Priority:** `FLUJO_STATE_URI` (Env) > `flujo.toml` > Default.
*   **Production Value:** `export FLUJO_STATE_URI="postgresql://user:pass@host:5432/db"`
*   **Migrations:** Required for Postgres backends.
    ```bash
    flujo migrate
    ```

### 1.2 `flujo.toml` Tuning
Configure the engine for high-concurrency environments.

```toml
# Persistent backend (top-level, not under [settings])
state_uri = "postgresql://user:pass@host:5432/db"

[settings]
# Connection Pooling (critical for FastAPI/Celery + Postgres)
postgres_pool_min = 5
postgres_pool_max = 20

[aros]
# Stage 2: Uses json-repair to fix markdown fences/trailing commas automatically
coercion_tolerant_level = 2
structured_output_default = "openai_json"

[lockfile]
# Ensure prompt/config consistency between dev and prod
enabled = true
```

**Settings precedence:** Environment variables override `flujo.toml`. Some strictness flags are
env-driven (e.g., `FLUJO_STRICT_DSL`) and enforced in CI.

### 1.3 Lockfiles
Commit `flujo.lock` to git. It ensures that the exact agent configurations and prompts tested in staging are what run in production.
*   **CI Check:** `flujo lock verify --strict`

---

## 2. Domain Modeling (Type Safety)
### 2.1 Typed Context (Mandatory)
Never use `dict`. Extend `PipelineContext` to enforce schema validity and safe persistence.

```python
from flujo.domain.models import PipelineContext
from pydantic import Field

class ResearchContext(PipelineContext):
    """Context for biomedical research."""
    # Indexed in Postgres for fast filtering
    user_id: str
    # Validated structure
    source_type: str = "unknown"
    results: list[dict] = Field(default_factory=list)
```

### 2.2 Handling Large Data (`ContextReference`)
**Guideline:** Avoid storing large blobs in Postgres `JSONB`.
Use `ContextReference` to store a pointer. Flujo hydrates/persists references via
`state_providers` you pass to the runner.

```python
from flujo.domain.models import PipelineContext, ContextReference

class DocContext(PipelineContext):
    # DB stores: { "provider_id": "s3", "key": "bucket/file.pdf" }
    raw_document: ContextReference[bytes]
```

```python
# Inject providers for ContextReference hydration/persistence
runner = Flujo(
    pipeline=my_pipeline,
    context_model=DocContext,
    state_providers={"s3": MyS3Provider()},
)
```

### 2.3 Explicit Generics
When defining runners or registries, use full type signatures to enable static analysis (`mypy`).

```python
# Flujo[InputType, OutputType, ContextType]
runner: Flujo[str, QueryOutput, ResearchContext] = Flujo(...)
```

---

## 3. The DSL: Complete Step Library
Choose the specific step type that matches your reliability requirements.

### Core Logic
*   **`Step`**: Atomic unit. Executes an agent or callable.
*   **`ConditionalStep`**: Routing logic via `condition_callable`.
*   **`LoopStep`**: Iterates a pipeline until `exit_condition_callable` returns True.
*   **`StateMachineStep`**: For complex non-linear flows (e.g., *Draft -> Critique -> Edit -> Approval*).

### Scaling & Async
*   **`MapStep`**: Iterates a pipeline over a list input. With persistence enabled, step history
    captures each iteration for audit and troubleshooting.
*   **`ParallelStep`**: Executes branches concurrently.
    *   **Recommendation:** Prefer `merge_strategy=MergeStrategy.CONTEXT_UPDATE` (and `field_mapping`)
        for explicit, safe merges.
*   **`DynamicParallelRouterStep`**: Uses a `router_agent` (callable or agent) to decide which branches run.

### Production Resilience
*   **`GranularStep`**: **The Production Standard for Agents.** Persists state *turn-by-turn* when
    a persistent backend is configured. Use `Step.granular(...)` for the loop wrapper.
    *   *Features:* CAS (Compare-And-Swap) guards, Idempotency keys.
*   **`CacheStep`**: Memoizes results via a `CacheBackend` (defaults to in-memory). Use a
    persistent cache backend if you need durability.
*   **`ImportStep`**: Composes external YAML blueprints. Essential for team modularity.
*   **`HumanInTheLoopStep`**: Raises `PausedException`; the runner returns a `Paused` result.
    Persistence depends on the configured backend; resumption is handled by the caller
    (or `TaskClient.resume_task`).

---

## 4. The Execution API
In production services (FastAPI), **sync methods are forbidden**.

### The Runner (`Flujo`)
| Method | Description | Return Type |
| :--- | :--- | :--- |
| **`run_result_async()`** | **Primary.** Runs to completion. | `Awaitable[PipelineResult]` |
| **`run_stream()`** | UI/Progress. Yields `Chunk` / `StepOutcome`. | `AsyncIterator` |
| **`resume_async()`** | Resumes a `Paused` workflow. | `Awaitable[PipelineResult]` |
| **`replay_from_trace()`** | **Debug.** Re-runs locally using cached DB responses. | `Awaitable[PipelineResult]` |
| **`aclose()`** | **Mandatory.** Drains DB pools. | `Awaitable[None]` |

### Resource Injection (`AppResources`)
Do not use global variables for database connections or API clients. Inject them via `resources`.

```python
class ServiceResources(AppResources):
    db_conn: Any
    search_client: Any

# Usage in Step
async def my_step(data, context, resources: ServiceResources):
    await resources.db_conn.execute(...)

# Injection
runner = Flujo(..., resources=ServiceResources(db_conn=pool))
```

---

## 5. Native Background Execution
Flujo acts as its own task queue. You do not need Celery for long-running agents.

1.  **Define:** Set `execution_mode="background"` in `StepConfig`.
2.  **Launch:** The step returns immediately with a `BackgroundLaunched` status.
3.  **Manage:**
    *   `runner.get_failed_background_tasks()`: Audit crashes.
    *   `runner.resume_background_task(task_id)`: Retry specific failures.

---

## 6. Management & Monitoring API
### `TaskClient`
The interface for external systems (Admin Dashboards, Webhooks) to interact with the configured
state backend (SQLite or Postgres).

*   **`list_tasks(status="paused", metadata_filter={...})`**: Find tasks.
*   **`get_task(run_id)`**: Retrieve full history/context.
*   **`resume_task(run_id, input)`**: Resume a specific suspended workflow.

### Governance Engine
Configure via environment variables:
*   **PII Scrubbing:** `FLUJO_GOVERNANCE_PII_SCRUB=1` (optional `FLUJO_GOVERNANCE_PII_STRONG=1`).
*   **Tool Gating:** `FLUJO_GOVERNANCE_TOOL_ALLOWLIST=tool_a,tool_b`.
*   **Limits:** Use `UsageLimits(...)` in code or `[budgets]` in `flujo.toml`.

### Shadow Evaluation (LLM-as-Judge)
Run quality checks on live traffic asynchronously.
*   **Config (env):** `FLUJO_SHADOW_EVAL_ENABLED=1`, `FLUJO_SHADOW_EVAL_SINK=database`.
*   **Outcome:** Scores are written to the `evaluations` table on the configured backend
    (SQLite or Postgres).

---

## 7. Integration Patterns (FastAPI)

### Lifecycle Management
You must wire the runner into the application lifespan to prevent connection leaks.

```python
class FlujoAdapter:
    def __init__(self):
        self.runner = Flujo(...)

    async def shutdown(self):
        await self.runner.aclose() # Drains Postgres pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    await adapter.shutdown()
```

### The "Fatal Anti-Pattern" (Exception Handling)
**Never** write a bare `except Exception`. It breaks the Pause/Resume orchestration.

**❌ BAD:**
```python
try:
    await runner.run_result_async(...)
except Exception: # Swallows PausedException!
    return "Error"
```

**✅ GOOD:**
```python
from flujo.exceptions import PausedException, PipelineAbortSignal, FlujoError

try:
    await runner.run_result_async(...)
except (PausedException, PipelineAbortSignal):
    raise # Allow signal to bubble up
except FlujoError as e:
    logger.error(f"Execution Error: {e}")
```

---

## 8. Deployment Profiles & Checklists

### Profile A: The "Autonomous Researcher" (Long-Running)
*   **Architecture:** `Step.granular(...)` + `LoopStep` + `Native Background`.
*   **Checklist:**
    - [ ] `persist_state = True`.
    - [ ] `enforce_idempotency=True` for granular tools (prevents double-posting).
    - [ ] `TaskClient` set up for status polling.

### Profile B: The "High-Speed Utility" (RAG / Data Processing)
*   **Architecture:** `MapStep` + `CacheStep`.
*   **Checklist:**
    - [ ] `persist_state = False` (Optional) to save IOPS if audit is not required.
    - [ ] `timeout_s` set strictly in `StepConfig`.
    - [ ] `postgres_pool_max` set high (20+) if using Postgres.

### Profile C: The "Interactive Assistant" (Chat / HITL)
*   **Architecture:** `HumanInTheLoopStep` + `StateMachineStep`.
*   **Checklist:**
    - [ ] `FLUJO_GOVERNANCE_PII_SCRUB=1` enabled.
    - [ ] UI integrates with `TaskClient.resume_task`.
    - [ ] `aclose()` wired to server shutdown.

---

## 9. Reference Implementation (Best Practices)

```python
class FlujoProductionAdapter:
    def __init__(self, persist: bool = True):
        self._runner = Flujo(
            pipeline=my_pipeline,
            context_model=MyTypedContext,
            usage_limits=UsageLimits(total_cost_usd_limit=1.0),
            persist_state=persist
        )

    async def process_request(self, input_data: str, user_id: str) -> str:
        # Seed context for auditability
        initial_ctx = {"user_id": user_id, "source": "api"}

        try:
            result = await self._runner.run_result_async(
                initial_input=input_data,
                initial_context_data=initial_ctx
            )

            if result.success:
                return result.output
            return "Processing Failed"

        except (PausedException, PipelineAbortSignal):
            # Propagate pause signal to upper layers
            raise
        except Exception as e:
            # Log actual errors
            logger.error(f"Critical failure: {e}")
            raise

    async def close(self):
        await self._runner.aclose()
```

---

## Related Documentation

- **[Agent Architecture](./agent_architecture.md)**: MED13-specific implementation guide
- **[Reasoning Techniques](./reasoning.md)**: GranularStep, TreeSearchStep patterns
- **[Contract-Oriented AI](./contract_oriented_ai.md)**: Evidence-first contract design
- **[Engineering Architecture](../EngineeringArchitecture.md)**: Overall system architecture
