# MED13 AI Agent Architecture

## Overview

The MED13 Resource Library implements a **contract-first, evidence-based AI agent system** using the [Flujo](https://github.com/flujo-ai/flujo) framework. This architecture enables intelligent query generation, data processing, and research assistance while maintaining strict type safety and Clean Architecture principles.

## Architectural Principles

### 1. Contract-First Design

All AI agents communicate through **strongly-typed Pydantic contracts** that define:
- **Input expectations**: What the agent receives
- **Output guarantees**: What the agent returns
- **Evidence requirements**: Supporting data for decisions

```python
# Every agent output includes evidence-first fields
class BaseAgentContract(BaseModel):
    confidence_score: float  # 0.0-1.0 for governance routing
    rationale: str           # Human-readable explanation
    evidence: list[EvidenceItem]  # Machine-checkable supporting data
```

### 2. Clean Architecture Alignment

AI agents follow the same layered architecture as the rest of the system:

```
┌─────────────────────────────────────────────────────────────┐
│              Domain Layer (src/domain/agents/)              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  • Contracts: QueryGenerationContract, BaseAgentContract │
│  │  • Contexts: QueryGenerationContext, BaseAgentContext    │
│  │  • Ports: QueryAgentPort (interface definition)          │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────┐
│          Application Layer (src/application/agents/)        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  • QueryAgentService: Orchestrates agent use cases       │
│  │  • Handles research space context resolution             │
│  │  • Multi-source query coordination                       │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────┐
│        Infrastructure Layer (src/infrastructure/llm/)       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  • Adapters: FlujoQueryAgentAdapter (implements port)    │
│  │  • Factories: QueryAgentFactory, create_pubmed_query_agent│
│  │  • Pipelines: PubMed, ClinVar, etc. with governance     │
│  │  • State: Backend manager, lifecycle, state repository   │
│  │  • Skills: Bounded capabilities registry                 │
│  │  • Prompts: Version-controlled system prompts           │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 3. Evidence-First Outputs

Every agent decision includes structured evidence:

```python
class EvidenceItem(BaseModel):
    source: EvidenceSourceType  # llm_reasoning, retrieved_document, etc.
    content: str
    confidence: float
    metadata: dict[str, str | int | float | bool]
```

This enables:
- **Auditability**: Track why decisions were made
- **Governance**: Route low-confidence decisions for human review
- **Debugging**: Understand agent reasoning
- **Compliance**: Healthcare audit trail requirements

## File Organization

```
src/
├── domain/agents/                    # Domain layer
│   ├── contracts/
│   │   ├── base.py                  # BaseAgentContract, EvidenceItem
│   │   └── query_generation.py      # QueryGenerationContract
│   ├── contexts/
│   │   ├── base.py                  # BaseAgentContext
│   │   └── query_context.py         # QueryGenerationContext
│   └── ports/
│       └── query_agent_port.py      # QueryAgentPort interface
│
├── application/agents/               # Application layer
│   └── services/
│       └── query_agent_service.py   # Use case orchestration
│
└── infrastructure/llm/               # Infrastructure layer
    ├── adapters/
    │   └── query_agent_adapter.py   # FlujoQueryAgentAdapter
    ├── config/
    │   ├── flujo_config.py          # State URI resolution
    │   ├── governance.py            # GovernanceConfig
    │   └── model_registry.py        # LLM model configurations
    ├── factories/
    │   ├── base_factory.py          # BaseAgentFactory
    │   └── query_agent_factory.py   # QueryAgentFactory
    ├── pipelines/
    │   ├── base_pipeline.py         # Governance patterns
    │   └── query_pipelines/
    │       └── pubmed_pipeline.py   # PubMed-specific pipeline
    ├── prompts/
    │   └── query/
    │       └── pubmed.py            # PubMed system prompts
    ├── skills/
    │   └── registry.py              # Skill registration
    └── state/
        ├── backend_manager.py       # State backend singleton
        ├── flujo_state_repository.py # State inspection
        └── lifecycle.py             # FastAPI lifecycle management
```

## Current Agents

### Query Generation Agent (PubMed)

Generates optimized PubMed Boolean queries from research context.

**Contract:**
```python
class QueryGenerationContract(BaseAgentContract):
    decision: Literal["generated", "fallback", "escalate"]
    query: str                    # The generated query
    source_type: str              # "pubmed"
    query_complexity: str         # "simple", "moderate", "complex"
```

**Usage:**
```python
from src.infrastructure.llm import FlujoQueryAgentAdapter

# Create adapter
agent = FlujoQueryAgentAdapter()

# Generate query
contract = await agent.generate_query(
    research_space_description="MED13 genetic variants in cardiac development",
    user_instructions="Focus on recent publications",
    source_type="pubmed",
)

# Access results
print(contract.query)            # PubMed Boolean query
print(contract.confidence_score) # 0.0-1.0
print(contract.rationale)        # Explanation
print(contract.decision)         # "generated", "fallback", "escalate"
```

## Reasoning Techniques

Flujo provides structured reasoning primitives for complex problem-solving. Rather than a single "reasoning step," reasoning is implemented through specialized step types.

### Reasoning Strategy Selection

| Reasoning Type | Step Type | Use Case |
|----------------|-----------|----------|
| **Chain of Thought (CoT)** | `GranularStep` | Sequential, multi-turn reasoning with tool use |
| **Tree of Thoughts (ToT)** | `TreeSearchStep` | Branching exploration with backtracking |
| **Implicit Reasoning** | Standard `Step` | Reasoning models (e.g., `openai:o1`) |

### Chain of Thought with GranularStep

For linear, multi-turn reasoning where the agent needs to "think step-by-step" or use tools iteratively. Each thought and tool call is persisted for auditability.

```python
from flujo.domain.dsl import GranularStep
from flujo.agents import make_agent_async

# CoT / ReAct agent with tool use
agent = make_agent_async(
    "openai:gpt-4o",
    "Think step-by-step before answering. Use tools to verify assumptions."
)

step = GranularStep(
    name="step_by_step_reasoning",
    agent=agent,
    history_max_tokens=8192,
    enforce_idempotency=True,  # Track for retry safety
)
```

**Use Cases:**
- Research query refinement
- Evidence gathering with tool calls
- Multi-step data validation

### Tree of Thoughts with TreeSearchStep

For complex problems requiring exploration of multiple solution paths with backtracking. Implements A*/Beam Search algorithms.

```python
from flujo.domain.dsl import TreeSearchStep
from flujo.agents import make_agent_async

# 1. Proposer: Generates N possible next steps
proposer = make_agent_async(
    "openai:gpt-4o",
    "Propose 3 possible next steps for solving this problem..."
)

# 2. Evaluator: Scores each step (0.0 to 1.0)
evaluator = make_agent_async(
    "openai:gpt-4o",
    "Rate this approach from 0.0 to 1.0 based on likelihood of success..."
)

# 3. Tree Search Step
step = TreeSearchStep(
    name="deep_reasoning",
    proposer=proposer,
    evaluator=evaluator,
    branching_factor=3,       # Generate 3 thoughts per step
    beam_width=3,             # Keep top 3 thoughts
    max_depth=5,              # Look 5 steps ahead
    require_goal=True,        # Fail if no solution found
    goal_score_threshold=0.9, # Solution threshold
)
```

**Use Cases:**
- Complex query optimization
- Multi-step research planning
- Variant classification with multiple hypotheses

### Implicit Reasoning with Reasoning Models

For problems where the model's native reasoning capabilities suffice, use a standard `Step` with a reasoning-optimized model.

```python
from flujo.domain.dsl import Step
from flujo.agents import make_agent_async

# Use a reasoning model (e.g., o1)
agent = make_agent_async(
    "openai:o1",  # Reasoning model
    "Analyze this genetic variant and provide classification rationale..."
)

step = Step(name="variant_analysis", agent=agent)
```

### When to Use Each Approach

| Scenario | Recommended Approach |
|----------|---------------------|
| Simple query generation | Standard `Step` |
| Multi-step evidence gathering | `GranularStep` (CoT) |
| Complex research planning with alternatives | `TreeSearchStep` (ToT) |
| Deep analysis requiring native reasoning | Reasoning model (`o1`) |
| Hybrid: exploration + tool use | `TreeSearchStep` + `GranularStep` in pipeline |

**See Also:** `docs/flujo/reasoning.md` for detailed TreeSearchStep examples

## Governance Patterns

### Confidence-Based Routing

Agents route low-confidence decisions for human review:

```python
# In pipeline configuration
governance_gate = ConditionalStep(
    name="confidence_gate",
    condition_callable=check_confidence,  # Returns "approve" or "review"
    routing={
        "approve": continue_step,
        "review": HumanInTheLoopStep(message="Review required"),
    },
)
```

### Governance Configuration

```python
# Environment variables
FLUJO_GOVERNANCE_ENABLED=true
FLUJO_GOVERNANCE_HITL_THRESHOLD=0.85
FLUJO_GOVERNANCE_TOOL_ALLOWLIST=pubmed.search,query.validate
```

### Step Granularity

Enable per-turn state persistence for auditability:

```python
# In pipeline creation
Step.granular(
    name="generate_query",
    agent=agent,
    enforce_idempotency=True,  # Track costs/retry safety
)
```

## Adding New Agents

### Step 1: Define Domain Contract

```python
# src/domain/agents/contracts/my_agent.py
from src.domain.agents.contracts.base import BaseAgentContract

class MyAgentContract(BaseAgentContract):
    """Output contract for my new agent."""

    result: str
    metadata: dict[str, str]
```

### Step 2: Define Context

```python
# src/domain/agents/contexts/my_context.py
from src.domain.agents.contexts.base import BaseAgentContext

class MyAgentContext(BaseAgentContext):
    """Pipeline context for my agent."""

    custom_field: str | None = None
```

### Step 3: Define Port (Interface)

```python
# src/domain/agents/ports/my_agent_port.py
from abc import ABC, abstractmethod
from src.domain.agents.contracts.my_agent import MyAgentContract

class MyAgentPort(ABC):
    """Port interface for my agent operations."""

    @abstractmethod
    async def process(
        self,
        input_data: str,
        *,
        user_id: str | None = None,
    ) -> MyAgentContract:
        """Process input and return contract."""

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources."""
```

### Step 4: Create System Prompt

```python
# src/infrastructure/llm/prompts/my_agent/prompt.py
MY_AGENT_SYSTEM_PROMPT = """
You are an expert assistant for...

## Output Schema

Provide:
- result: The main output
- confidence_score: 0.0-1.0
- rationale: Brief explanation
- evidence: Supporting information
"""
```

### Step 5: Create Factory

```python
# src/infrastructure/llm/factories/my_agent_factory.py
from flujo.agents import make_agent_async
from src.domain.agents.contracts.my_agent import MyAgentContract
from src.infrastructure.llm.prompts.my_agent.prompt import MY_AGENT_SYSTEM_PROMPT

def create_my_agent(model: str | None = None) -> FlujoAgent:
    return make_agent_async(
        model=model or "openai:gpt-4o-mini",
        system_prompt=MY_AGENT_SYSTEM_PROMPT,
        output_type=MyAgentContract,
    )
```

### Step 6: Create Pipeline

```python
# src/infrastructure/llm/pipelines/my_agent_pipeline.py
from flujo import Flujo, Step
from src.domain.agents.contexts.my_context import MyAgentContext
from src.infrastructure.llm.factories.my_agent_factory import create_my_agent

def create_my_agent_pipeline(
    state_backend: StateBackend,
    use_governance: bool = True,
) -> Flujo[str, MyAgentContract, MyAgentContext]:
    agent = create_my_agent()

    steps = [
        Step.granular(name="process", agent=agent),
    ]

    if use_governance:
        # Add governance gate
        steps.append(create_governance_gate(...))

    return Flujo(*steps, state_backend=state_backend)
```

### Step 7: Create Adapter

```python
# src/infrastructure/llm/adapters/my_agent_adapter.py
from src.domain.agents.ports.my_agent_port import MyAgentPort
from src.domain.agents.contracts.my_agent import MyAgentContract

class MyAgentAdapter(MyAgentPort):
    """Flujo-based implementation of MyAgentPort."""

    async def process(self, input_data: str, ...) -> MyAgentContract:
        # Execute pipeline and return contract
        ...

    async def close(self) -> None:
        # Clean up pipelines
        ...
```

### Step 8: Create Application Service

```python
# src/application/agents/services/my_agent_service.py
class MyAgentService:
    """Application service for my agent use cases."""

    def __init__(self, agent: MyAgentPort) -> None:
        self._agent = agent

    async def execute(self, input_data: str, user_id: str) -> MyAgentContract:
        return await self._agent.process(input_data, user_id=user_id)
```

## Future Agent Roadmap

### Planned Agents

| Agent | Purpose | Reasoning Type | Status |
|-------|---------|----------------|--------|
| **Query Generation (PubMed)** | Generate PubMed Boolean queries | Standard Step | ✅ Complete |
| **Query Generation (ClinVar)** | Generate ClinVar queries | Standard Step | 🔜 Planned |
| **Evidence Extraction** | Extract evidence from publications | GranularStep (CoT) | 🔜 Planned |
| **Variant Classification** | AI-assisted variant classification | TreeSearchStep (ToT) | 🔜 Planned |
| **Literature Summarization** | Summarize research papers | Standard Step | 🔜 Planned |
| **Phenotype Mapping** | Map phenotypes to HPO terms | GranularStep (CoT) | 🔜 Planned |
| **Research Synthesis** | Multi-source research analysis | TreeSearchStep (ToT) | 🔜 Planned |

### Scaling Patterns

As we add more agents:

1. **Shared Infrastructure**: All agents use the same state backend, lifecycle management, and governance patterns
2. **Domain Boundaries**: Each agent type has its own contract, context, and port in the domain layer
3. **Factory Pattern**: Centralized agent creation with consistent configuration
4. **Skill Composition**: Agents can invoke registered skills for bounded capabilities

## Configuration Reference

### Environment Variables

```bash
# State Backend
FLUJO_STATE_URI=postgresql://...     # Override state backend URI
DATABASE_URL=postgresql://...         # Fallback for state backend

# Model Configuration
MED13_AI_AGENT_MODEL=openai:gpt-4o-mini  # Default model

# Governance
FLUJO_GOVERNANCE_ENABLED=true
FLUJO_GOVERNANCE_HITL_THRESHOLD=0.85
FLUJO_GOVERNANCE_REQUIRE_EVIDENCE=true
FLUJO_GOVERNANCE_TOOL_ALLOWLIST=pubmed.search,query.validate
```

### flujo.toml Configuration

```toml
[flujo]
state_uri = "postgresql://user:pass@host:5432/db?options=-c%20search_path%3Dflujo,public"
default_model = "openai:gpt-4o-mini"

[aros]
session_ttl = "24h"
max_retries = 3
pooled_connections = 10

[governance]
enabled = true
hitl_threshold = 0.85
require_evidence = true

[lockfile]
enabled = true
path = ".flujo.lock"
```

## Type Safety Notes

The Flujo library uses `Any` types in some internal generic parameters. This is a **documented exception** to the project's strict "Never Any" policy, confined to the infrastructure layer.

**Affected files** (listed in `scripts/validate_architecture.py`):
- `src/infrastructure/llm/pipelines/base_pipeline.py`
- `src/infrastructure/llm/pipelines/query_pipelines/pubmed_pipeline.py`
- `src/infrastructure/llm/state/lifecycle.py`
- `src/infrastructure/llm/adapters/query_agent_adapter.py`

**Key points:**
- All domain contracts are fully typed (no `Any`)
- All port interfaces are fully typed
- `Any` is only used for Flujo's internal `Step`/`Pipeline` generic parameters
- This is documented and added to the architectural validator's allowlist

## Testing Agents

### Unit Testing Contracts

```python
def test_query_generation_contract():
    contract = QueryGenerationContract(
        decision="generated",
        confidence_score=0.9,
        rationale="Query generated successfully",
        evidence=[],
        query="MED13[Title/Abstract]",
        source_type="pubmed",
        query_complexity="simple",
    )
    assert contract.decision == "generated"
    assert contract.confidence_score >= 0.0
```

### Testing with Stub Agents

```python
class StubQueryAgent(QueryAgentPort):
    def __init__(self, query: str, confidence: float = 0.9):
        self._query = query
        self._confidence = confidence

    async def generate_query(self, ...) -> QueryGenerationContract:
        return QueryGenerationContract(
            decision="generated",
            confidence_score=self._confidence,
            rationale="Stub agent",
            evidence=[],
            query=self._query,
            source_type="pubmed",
            query_complexity="simple",
        )

    async def close(self) -> None:
        pass

# Use in tests
agent = StubQueryAgent("MED13[Title/Abstract]")
contract = await agent.generate_query(...)
```

### Integration Testing

```python
@pytest.mark.integration
async def test_flujo_postgres_backend(postgres_engine):
    """Verify Flujo state persistence."""
    backend = PostgresBackend(resolve_flujo_state_uri())
    await backend.set_system_state("healthcheck", {"ok": True})
    # Verify tables exist in flujo schema
```

## Lifecycle Management

### FastAPI Integration

```python
from src.infrastructure.llm import flujo_lifespan

app = FastAPI(lifespan=flujo_lifespan)
```

### Manual Lifecycle

```python
from src.infrastructure.llm import get_lifecycle_manager

manager = get_lifecycle_manager()

# Register runners
manager.register_runner(pipeline)

# Shutdown (call during app shutdown)
await manager.shutdown()
```

## Related Documentation

- **[Reasoning Techniques](./reasoning.md)**: TreeSearchStep examples and A* search patterns
- **[Contract-Oriented AI](./contract_oriented_ai.md)**: Deep dive into contract-first patterns
- **[Production Guide](./prod_guide.md)**: Deployment and production configuration
- **[Engineering Architecture](../EngineeringArchitecture.md)**: Overall system architecture
- **[AGENTS.md](../../AGENTS.md)**: AI agent coding guidelines
