# MED13 AI Agent Architecture

## Overview

The MED13 Resource Library implements a **contract-first, evidence-based AI agent system** using the [Flujo](https://github.com/aandresalvarez/flujo) framework. This architecture enables intelligent query generation, data processing, and research assistance while maintaining strict type safety and Clean Architecture principles.

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
from src.domain.agents.models import ModelCapability
from src.infrastructure.llm.config.model_registry import get_model_registry
from src.infrastructure.llm.prompts.my_agent.prompt import MY_AGENT_SYSTEM_PROMPT

def create_my_agent(model: str | None = None) -> FlujoAgent:
    # Get model from registry (respects env var overrides)
    registry = get_model_registry()

    if model:
        model_spec = registry.get_model(model)
    else:
        model_spec = registry.get_default_model(ModelCapability.QUERY_GENERATION)

    # Handle reasoning models with special settings
    reasoning_settings = model_spec.get_reasoning_settings()

    if reasoning_settings:
        return make_agent_async(
            model=model_spec.model_id,
            system_prompt=MY_AGENT_SYSTEM_PROMPT,
            output_type=MyAgentContract,
            max_retries=model_spec.max_retries,
            timeout=int(model_spec.timeout_seconds),
            model_settings=reasoning_settings,
        )

    return make_agent_async(
        model=model_spec.model_id,
        system_prompt=MY_AGENT_SYSTEM_PROMPT,
        output_type=MyAgentContract,
        max_retries=model_spec.max_retries,
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

## Model Management

### Centralized Model Registry

All AI models are configured in `flujo.toml` and accessed through a centralized registry. This eliminates hardcoded model strings and enables:

- **Per-capability defaults**: Different models for different tasks
- **Environment overrides**: Override via `MED13_AI_{CAPABILITY}_MODEL`
- **Reasoning model support**: Automatic handling of `model_settings` for reasoning models
- **Future: User selection**: Users can choose from available models

### Model Configuration (flujo.toml)

```toml
[models]
# System-wide defaults by capability
default_query_generation = "openai:gpt-4o-mini"
default_evidence_extraction = "openai:gpt-5"
default_curation = "openai:gpt-5"
default_judge = "openai:gpt-4o-mini"

# Model specifications
[models.registry."openai:gpt-4o-mini"]
display_name = "GPT-4o Mini"
provider = "openai"
capabilities = ["query_generation", "judge"]
cost_tier = "low"
is_reasoning_model = false
max_retries = 3
timeout_seconds = 30.0
is_enabled = true

[models.registry."openai:gpt-5"]
display_name = "GPT-5"
provider = "openai"
capabilities = ["query_generation", "evidence_extraction", "curation", "judge"]
cost_tier = "high"
is_reasoning_model = true
max_retries = 1
timeout_seconds = 180.0
is_enabled = true

[models.registry."openai:gpt-5".default_reasoning_settings]
effort = "high"
summary = "detailed"
```

### Using the Registry

```python
from src.domain.agents.models import ModelCapability
from src.infrastructure.llm.config.model_registry import get_model_registry

# Get registry (singleton)
registry = get_model_registry()

# Get default model for a capability
model = registry.get_default_model(ModelCapability.QUERY_GENERATION)
print(model.model_id)        # "openai:gpt-4o-mini"
print(model.display_name)    # "GPT-4o Mini"

# Get models supporting a capability
models = registry.get_models_for_capability(ModelCapability.EVIDENCE_EXTRACTION)

# Check if model supports capability
is_valid = registry.validate_model_for_capability(
    "openai:gpt-5",
    ModelCapability.CURATION
)

# Get all available models (for UI selection)
available = registry.get_available_models()
```

### Reasoning Model Handling

Reasoning models (like GPT-5) require special `model_settings` for Flujo:

```python
# The factory handles this automatically
from src.infrastructure.llm.factories.base_factory import BaseAgentFactory

class MyAgentFactory(BaseAgentFactory[MyContract]):
    def create(self, model: str | None = None) -> FlujoAgent:
        # If model is a reasoning model, factory adds model_settings automatically
        return super().create(model)

# Or manually get settings
model_spec = registry.get_model("openai:gpt-5")
if model_spec.is_reasoning_model:
    settings = model_spec.get_reasoning_settings(effort="high")
    # Returns: {"reasoning": {"effort": "high"}, "text": {"verbosity": "detailed"}}
```

### Model Resolution Priority

The registry resolves models in this order:

1. **Environment variable**: `MED13_AI_{CAPABILITY}_MODEL=openai:gpt-5`
2. **flujo.toml defaults**: `[models] default_query_generation = "..."`
3. **Fallback**: First enabled model with the capability

## Configuration Reference

### Environment Variables

```bash
# State Backend
FLUJO_STATE_URI=postgresql://...     # Override state backend URI
DATABASE_URL=postgresql://...         # Fallback for state backend

# Model Configuration (override flujo.toml defaults)
MED13_AI_QUERY_GENERATION_MODEL=openai:gpt-5-nano
MED13_AI_EVIDENCE_EXTRACTION_MODEL=openai:gpt-5
MED13_AI_CURATION_MODEL=openai:gpt-5
MED13_AI_JUDGE_MODEL=openai:gpt-4o-mini

# Governance
FLUJO_GOVERNANCE_ENABLED=true
FLUJO_GOVERNANCE_HITL_THRESHOLD=0.85
FLUJO_GOVERNANCE_REQUIRE_EVIDENCE=true
FLUJO_GOVERNANCE_TOOL_ALLOWLIST=pubmed.search,query.validate

# Shadow Evaluation
FLUJO_SHADOW_EVAL_ENABLED=0
FLUJO_SHADOW_EVAL_JUDGE_MODEL=openai:gpt-4o-mini
```

### flujo.toml Configuration

```toml
[flujo]
state_uri = "postgresql://user:pass@host:5432/db?options=-c%20search_path%3Dflujo,public"

[models]
default_query_generation = "openai:gpt-4o-mini"
default_evidence_extraction = "openai:gpt-5"
default_curation = "openai:gpt-5"
default_judge = "openai:gpt-4o-mini"

[aros]
session_ttl = "24h"
max_retries = 3
pooled_connections = 10

[governance]
enabled = true
hitl_threshold = 0.85
require_evidence = true

[shadow_eval]
enabled = false
judge_model = "openai:gpt-4o-mini"

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
