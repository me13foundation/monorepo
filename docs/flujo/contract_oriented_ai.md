# 🛡️ Flujo Agent Engineering Guide

**Contract-First Architecture**

**Version:** 1.0
**Audience:** Engineers building autonomous or semi-autonomous agents with Flujo
**Philosophy:**

> Reliable agents are not created by better prompts.
> They are created by **typed contracts, explicit capabilities, and durable execution**.

---

## 0. Core Principle

**Do not start with a prompt. Start with a contract.**

In Flujo, every autonomous agent is treated as a **bounded decision system**, not a chatbot.
The contract defines:

* what the agent is allowed to output,
* how decisions are justified,
* how results are audited,
* and when humans must intervene.

Prompts are an implementation detail.
**Contracts are the architecture.**

---

## 1. Architectural Foundation: The Data Contract

### 1.1 Evidence-First Output Schemas (Auditability by Design)

Flujo agents must **not** expose internal chain-of-thought.
Free-form reasoning traces:

* increase brittleness,
* create parsing instability,
* and complicate audit and compliance.

Instead, use **Evidence-First schemas** that separate:

* the decision,
* the confidence,
* the human-readable justification,
* and the structured evidence supporting that decision.

```python
from pydantic import BaseModel, Field
from typing import Literal

class EvidenceItem(BaseModel):
    source_type: Literal["tool", "db", "paper", "web", "note"]
    locator: str  # DOI, URL, query-id, row-id, run-id, etc.
    excerpt: str
    relevance: float = Field(..., ge=0.0, le=1.0)

class AgentContract(BaseModel):
    # Executable outcome
    decision: Literal["approve", "reject", "escalate"]

    # Quantitative confidence for automated routing
    confidence_score: float = Field(..., ge=0.0, le=1.0)

    # Brief, user-safe explanation
    rationale: str = Field(
        ...,
        description="Concise justification suitable for audit logs and users."
    )

    # Structured, machine-checkable evidence
    evidence: list[EvidenceItem] = Field(default_factory=list)
```

**Design rule:**
If a decision cannot be supported by structured evidence, it must not be auto-approved.

---

### 1.2 Agent Identity via the Factory Pattern

Agents are **identities with lifecycles**, not inline function calls.

Never instantiate agents directly inside pipelines.
Always use a factory to:

* bind the output contract,
* inject system prompts,
* configure retries/timeouts,
* and centralize model configuration.

```python
from flujo.agents import make_agent_async

def create_compliance_agent():
    return make_agent_async(
        model="openai:gpt-4o",
        system_prompt=(
            "You are a compliance officer. "
            "Base decisions strictly on provided evidence."
        ),
        output_type=AgentContract,  # The contract
        max_retries=3
    )
```

**Why this matters**

* Identity consistency across pipelines
* Centralized upgrades (model, retries, prompts)
* Easier audit and reasoning about behavior

---

## 2. Capabilities as Code: Flujo Skills

Agents must never have unrestricted access to application logic.
Agents must not have broad access to your codebase.
In Flujo, **Skills** are the boundary for world interaction.

A Skill is:

* a bounded capability,
* explicitly registered,
* governed by schema and policy,
* and optionally allowed or denied at runtime.

---

### 2.0 Skill Boundaries (How to Use Skills)

Use Skills as the only agent-facing surface area:

* implement a pure callable (payload in, output out),
* register it with `SkillRegistration` and schemas,
* wire it into agents via the skill registry (YAML or pipeline config),
* gate it at runtime with the governance allowlist.

---

### 2.1 Skill Implementation (Pure Logic + Dependency Injection)

Skills must:

* be side-effect explicit,
* avoid globals,
* rely on injected resources only,
* accept a JSON payload as the first positional argument.

Custom skills always receive the payload as the first positional argument.
If the callable accepts `resources`, Flujo injects your `AppResources` by keyword.

```python
# skills/finance.py
from __future__ import annotations

from typing import Any

from flujo.domain.resources import AppResources
from flujo.type_definitions.common import JSONObject

class FinanceResources(AppResources):
    db_connection: Any

async def calculate_risk_score(
    payload: JSONObject,
    *,
    resources: FinanceResources,  # Dependency injection
) -> JSONObject:
    """Calculates risk score based on transaction history."""
    user_id = str(payload["user_id"])
    threshold = float(payload["threshold"])
    db = resources.db_connection
    score = await db.fetch_score(user_id)

    return {
        "user_id": user_id,
        "risk_score": score,
        "approved": score < threshold,
    }
```

---

### 2.2 Skill Registration (The Capability Contract)

Every Skill must be **registered** with explicit metadata.

Key rules:

* Skills are namespaced for governance.
* Factories **must accept `**kwargs`** for YAML / CLI parameter pass-through.
* Side effects are declared, not inferred.

```python
# skills/__init__.py
from flujo.infra.skill_registry import get_skill_registry
from flujo.infra.skill_models import SkillRegistration

from .finance import calculate_risk_score

def register_skills():
    registry = get_skill_registry()

    registry.register(
        **SkillRegistration(
            id="finance.calculate_risk",
            factory=lambda **_params: calculate_risk_score,
            description="Calculates user risk score. Read-only.",
            side_effects=False,
            input_schema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "threshold": {"type": "number"}
                },
                "required": ["user_id", "threshold"]
            }
        ).__dict__
    )
```

**Important:**
`factory` returns the callable. Flujo supplies runtime arguments separately using the declared schema.

---

### 2.3 Security & Governance

Agents introduce a new attack surface.
Flujo enforces **least privilege** at multiple layers.

#### Runtime Tool Gating

Use `governance_tool_allowlist` to restrict which Skills may be invoked.

```bash
export FLUJO_GOVERNANCE_TOOL_ALLOWLIST="finance.calculate_risk,search.query"
```

`flujo.toml` can set `governance_tool_allowlist` as a list; env overrides it.

* Every skill invocation is wrapped at runtime.
* Disallowed tools raise a `ConfigurationError`.

#### Blueprint Safety (Creation-Time)

When using `flujo create`:

* Skills marked `side_effects=True` are blocked in non-interactive mode.
* Use `--allow-side-effects` to explicitly override.

This prevents accidental deployment of write-capable agents.

---

## 3. Execution Loop: Durability & Control

Governance must exist **inside** the execution loop, not after it.

---

### 3.1 Execution Primitives: Durability by Default

For multi-turn or complex reasoning, prefer `Step.granular(...)`.
It wraps a `GranularStep` in a `LoopStep` and persists each turn.

It:

* persists state per turn,
* records inputs, outputs, and tool calls,
* and supports idempotent execution.

```python
from flujo import Step

granular_pipeline = Step.granular(
    name="secure_reasoning",
    agent=create_compliance_agent(),
    history_max_tokens=4096,
    enforce_idempotency=True,
)
```

**Outcome:**
A durable, inspectable execution trail suitable for audits and post-hoc analysis.

---

### 3.2 Reasoning Patterns: CoT vs ToT

Flujo does not have a specific primitive named `ReasoningStep`. Instead, reasoning is implemented through structural patterns that provide the desired level of depth and auditability.

#### 1. `GranularStep` (For Chain of Thought / ReAct)
Use `GranularStep` for linear, multi-turn reasoning where the agent needs to "think out loud" or use tools iteratively. This pattern persists every individual "thought" or tool call to the database.

```python
from flujo.domain.dsl import GranularStep
from flujo.agents import make_agent_async

# Standard CoT / ReAct agent
agent = make_agent_async(
    "openai:gpt-4o",
    "Think step-by-step before answering. Use tools to verify assumptions."
)

step = GranularStep(
    name="step_by_step_reasoning",
    agent=agent,
    history_max_tokens=8192,
    enforce_idempotency=True
)
```

#### 2. `TreeSearchStep` (For Deep Search / Tree of Thoughts)
This is the heavy-lifting reasoning primitive. It implements algorithms like **Beam Search** or **Best-First Search** to explore multiple reasoning paths, evaluate them, and select the best one.

Use this when the problem requires exploring multiple possibilities (e.g., code generation, complex planning).

```python
from flujo.domain.dsl import TreeSearchStep
from flujo.agents import make_agent_async

# 1. Proposer: Generates N possible next steps
proposer = make_agent_async("openai:gpt-4o", "Propose 3 possible next steps...")

# 2. Evaluator: Scores each step (0.0 to 1.0)
evaluator = make_agent_async("openai:gpt-4o", "Rate this step from 0.0 to 1.0...")

# 3. The Reasoning Step
step = TreeSearchStep(
    name="deep_reasoning",
    proposer=proposer,
    evaluator=evaluator,
    branching_factor=3,  # Generate 3 thoughts per step
    beam_width=3,        # Keep the top 3 thoughts
    max_depth=5,         # Look 5 steps ahead
    require_goal=True,   # Fail if no solution found
    goal_score_threshold=0.9
)
```

#### Summary
*   **Sequential Reasoning (CoT):** Use `GranularStep`.
*   **Branching Reasoning (ToT):** Use `TreeSearchStep`.
*   **Implicit Reasoning:** Use a standard `Step` with a reasoning model like `openai:o1`.

---

### 3.3 Confidence-Based Escalation (Human-in-the-Loop)

Confidence is a **routing signal**, not proof of correctness.

Use it to determine whether a decision:

* proceeds automatically,
* or requires human review.

```python
from typing import Literal

from pydantic import BaseModel, Field

from flujo import Pipeline, Step
from flujo.domain.dsl import ConditionalStep, HumanInTheLoopStep

class AgentContract(BaseModel):
    decision: Literal["approve", "reject", "escalate"]
    confidence_score: float = Field(..., ge=0.0, le=1.0)


async def decide(payload: str) -> AgentContract:
    return AgentContract(decision="approve", confidence_score=0.9)


async def finalize(contract: AgentContract) -> str:
    return contract.decision


def check_confidence(output: AgentContract, _ctx) -> str:
    return "escalate" if output.confidence_score < 0.85 else "proceed"


agent_step = Step.from_callable(decide, name="decision")

pipeline = Pipeline(
    steps=[
        agent_step,
        ConditionalStep(
            name="governance_gate",
            condition_callable=check_confidence,
            branches={
                "escalate": Pipeline(
                    steps=[
                        HumanInTheLoopStep(
                            name="human_review",
                            message_for_user="Low confidence decision. Review required.",
                            sink_to="manual_override",
                        )
                    ]
                ),
                "proceed": Pipeline(
                    steps=[
                        Step.from_callable(finalize, name="finalize"),
                    ]
                ),
            },
        ),
    ]
)
```

**Note on strictness:**
Flujo runs with `strict_dsl=True` by default.
Avoid `Any` / `object` unless using an explicit adapter step.
Environment variables override `flujo.toml` via `ConfigManager`.

---

## 4. Observability: Hierarchical Tracing

Traditional APM cannot explain agent behavior.

Flujo provides **hierarchical span-level tracing**:

1. **Pipeline Run** – end-to-end execution
2. **Step Execution** – logical stages
3. **Agent Turn** – LLM calls (tokens, cost, prompt, output)
4. **Skill Invocation** – arguments, results, timing

Inspect traces via CLI:

```bash
flujo lens trace <run_id>
```

This enables:

* forensic debugging,
* cost attribution,
* and reasoning transparency.

---

## 5. Engineering Checklist

### Architecture

* [ ] Output contract separates decision, rationale, and evidence
* [ ] Agents created via factories (`make_agent_async`)
* [ ] `Step.granular` used for multi-turn reasoning (CoT)
* [ ] `TreeSearchStep` used for complex, branching exploration (ToT)

### Skills

* [ ] Every capability registered via `SkillRegistration`
* [ ] Skill factories accept `**kwargs`
* [ ] No global state; only `AppResources`

### Governance

* [ ] `governance_tool_allowlist` configured (env or `flujo.toml`)
* [ ] Confidence-based escalation present
* [ ] Durable backend (e.g., Postgres) enabled for audit logs

---

## Final Note

Flujo is not a “smart agent framework.”
It is a **decision infrastructure**.

If an agent cannot:

* explain itself,
* justify its evidence,
* be paused,
* or be audited,

then it does not belong in production.

**Contracts first. Capabilities second. Prompts last.**

---

## Related Documentation

- **[Agent Architecture](./agent_architecture.md)**: MED13-specific implementation guide
- **[Reasoning Techniques](./reasoning.md)**: GranularStep, TreeSearchStep patterns
- **[Production Guide](./prod_guide.md)**: Deployment and infrastructure configuration
- **[Engineering Architecture](../EngineeringArchitecture.md)**: Overall system architecture
- **[AGENTS.md](../../AGENTS.md)**: AI coding agent guidelines
