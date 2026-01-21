# Flujo Reasoning Techniques

Flujo provides structured reasoning primitives for complex problem-solving. There is no single `ReasoningStep` - instead, reasoning is implemented through specialized step types.

## Quick Reference

| Reasoning Type | Flujo Primitive | When to Use |
|----------------|-----------------|-------------|
| **Chain of Thought (CoT)** | `GranularStep` or `Step.granular()` | Sequential multi-turn reasoning, tool use, ReAct |
| **Tree of Thoughts (ToT)** | `TreeSearchStep` | Branching exploration, backtracking, A*/Beam search |
| **Implicit Reasoning** | Standard `Step` + reasoning model | Deep analysis with models like `openai:o1` |

---

## 1. Chain of Thought with GranularStep

For linear, multi-turn reasoning where the agent "thinks step-by-step" or uses tools iteratively. Each turn is persisted for auditability.

### Basic CoT Agent

```python
from flujo import Step
from flujo.agents import make_agent_async

# Create a CoT agent
agent = make_agent_async(
    "openai:gpt-4o",
    """You are a research assistant. Think step-by-step before answering.

When analyzing a query:
1. Identify the key concepts
2. Consider related terms and synonyms
3. Formulate the optimal search strategy
4. Explain your reasoning"""
)

# Wrap in granular step for durability
step = Step.granular(
    name="research_reasoning",
    agent=agent,
    history_max_tokens=8192,
    enforce_idempotency=True,  # Prevents duplicate tool calls on retry
)
```

### CoT with Tool Use (ReAct Pattern)

```python
from flujo import Step
from flujo.agents import make_agent_async
from flujo.domain.resources import AppResources

class ResearchResources(AppResources):
    pubmed_client: PubMedClient
    cache: dict

# Skills that the agent can use
async def search_pubmed(payload: dict, *, resources: ResearchResources) -> dict:
    """Search PubMed for articles."""
    query = payload["query"]
    results = await resources.pubmed_client.search(query)
    return {"articles": results, "count": len(results)}

async def validate_query(payload: dict) -> dict:
    """Validate a PubMed query syntax."""
    query = payload["query"]
    is_valid = "[" in query and "]" in query  # Simplified
    return {"valid": is_valid, "query": query}

# Agent with tools
agent = make_agent_async(
    "openai:gpt-4o",
    """You are a biomedical research assistant with access to tools.

Available tools:
- search_pubmed: Search PubMed database
- validate_query: Check query syntax

Think step-by-step:
1. First validate your query
2. If valid, search PubMed
3. Analyze results and refine if needed""",
    tools=[search_pubmed, validate_query],
)

step = Step.granular(
    name="react_research",
    agent=agent,
    history_max_tokens=8192,
    enforce_idempotency=True,
)
```

### When to Use GranularStep

- Multi-step data validation
- Research query refinement with feedback loops
- Evidence gathering requiring tool calls
- Any task needing audit trail of reasoning steps

---

## 2. Tree of Thoughts with TreeSearchStep

For problems requiring exploration of multiple solution paths with backtracking. Implements A*/Beam Search algorithms.

### LLM-Based Tree Search

Use LLM agents as proposer and evaluator for open-ended problems:

```python
from flujo.domain.dsl import TreeSearchStep
from flujo.agents import make_agent_async

# Proposer: Generates possible next steps
proposer = make_agent_async(
    "openai:gpt-4o",
    """You are exploring solutions to a research problem.

Given the current state, propose 3 distinct next steps.
Each step should be a different approach or direction.

Output format: List of 3 possible next actions."""
)

# Evaluator: Scores each step (0.0 to 1.0)
evaluator = make_agent_async(
    "openai:gpt-4o",
    """You are evaluating a proposed solution step.

Score this step from 0.0 to 1.0 based on:
- Likelihood of leading to the goal (0.5 weight)
- Quality of reasoning (0.3 weight)
- Feasibility (0.2 weight)

Output: A single float between 0.0 and 1.0"""
)

step = TreeSearchStep(
    name="research_exploration",
    proposer=proposer,
    evaluator=evaluator,
    branching_factor=3,       # Generate 3 options per step
    beam_width=3,             # Keep top 3 paths
    max_depth=5,              # Maximum reasoning depth
    require_goal=True,        # Fail if no solution found
    goal_score_threshold=0.85,
)
```

### Deterministic Tree Search (Game of 24)

The goal: use all numbers to make 24. The proposer expands numeric states, and the evaluator scores how close a state is to 24 (only returning `1.0` when a full solution is found).

```python
import asyncio
import json
from typing import Any

from flujo.application.runner import Flujo
from flujo.domain.dsl.tree_search import TreeSearchStep
from flujo.domain.models import PipelineContext
from flujo.testing.utils import gather_result


def _parse_candidate(prompt: str) -> dict[str, Any]:
    marker = "Candidate:"
    if marker not in prompt:
        return {}
    candidate_line = prompt.split(marker, 1)[1].strip().splitlines()[0]
    return json.loads(candidate_line)


def _expand_state(state: dict[str, Any]) -> list[dict[str, Any]]:
    nums = state.get("nums") or []
    entries = [item for item in nums if isinstance(item, dict)]
    results: list[dict[str, Any]] = []
    for i in range(len(entries)):
        for j in range(i + 1, len(entries)):
            a = entries[i]
            b = entries[j]
            rest = [entries[idx] for idx in range(len(entries)) if idx not in (i, j)]
            aval = int(a["value"])
            bval = int(b["value"])
            aexpr = str(a["expr"])
            bexpr = str(b["expr"])
            candidates = [
                (aval + bval, f"({aexpr}+{bexpr})"),
                (aval * bval, f"({aexpr}*{bexpr})"),
                (aval - bval, f"({aexpr}-{bexpr})"),
                (bval - aval, f"({bexpr}-{aexpr})"),
            ]
            if bval != 0 and aval % bval == 0:
                candidates.append((aval // bval, f"({aexpr}/{bexpr})"))
            if aval != 0 and bval % aval == 0:
                candidates.append((bval // aval, f"({bexpr}/{aexpr})"))
            for value, expr in candidates:
                results.append({"nums": rest + [{"value": int(value), "expr": expr}]})
    return results


async def proposer(prompt: str) -> list[dict[str, Any]]:
    return _expand_state(_parse_candidate(prompt))


async def evaluator(prompt: str) -> float:
    state = _parse_candidate(prompt)
    nums = state.get("nums") or []
    if len(nums) == 1:
        return 1.0 if int(nums[0]["value"]) == 24 else 0.0
    best = min(abs(int(item["value"]) - 24) for item in nums)
    score = max(0.0, 1.0 - min(1.0, best / 24))
    return min(score, 0.9)


async def main() -> None:
    step = TreeSearchStep(
        name="game_of_24",
        proposer=proposer,
        evaluator=evaluator,
        branching_factor=50,
        beam_width=50,
        max_depth=3,
        goal_score_threshold=1.0,
        require_goal=True,
    )
    runner = Flujo(step, context_model=PipelineContext, persist_state=False)
    start_state = {"nums": [{"value": n, "expr": str(n)} for n in [4, 4, 6, 8]]}
    result = await gather_result(
        runner,
        start_state,
        initial_context_data={"initial_prompt": "Use all numbers to make 24"},
    )
    print("Solution:", result.output)


if __name__ == "__main__":
    asyncio.run(main())
```

## Notes

- Keep candidate payloads JSON-serializable; they are persisted in `context.tree_search_state`.
- Use `candidate_validator` to prune invalid candidates cheaply.
- Set `goal_score_threshold=1.0` and `require_goal=True` when only exact matches should succeed.

## Heuristic Tuning & Distillation

After a run, you can analyze the search trace to tighten your evaluator rubric or distill the winning path into a reusable prompt. The tuning helper defaults to the `shadow_eval.judge_model` when configured.

```python
from flujo.application.tree_search_improvement import (
    build_tree_search_trace_report,
    distill_tree_search_path,
    tune_tree_search_evaluator,
)

# state is a SearchState captured from context.tree_search_state
report = build_tree_search_trace_report(state, objective="Use all numbers to make 24")
improvements = await tune_tree_search_evaluator(report)
distilled_prompt = await distill_tree_search_path(state, objective="Use all numbers to make 24")
```

### When to Use TreeSearchStep

- Complex query optimization with multiple valid approaches
- Research planning requiring exploration of alternatives
- Variant classification with competing hypotheses
- Any problem benefiting from backtracking

---

## 3. Implicit Reasoning with Reasoning Models

For problems where the model's native reasoning capabilities suffice:

```python
from flujo import Step
from flujo.agents import make_agent_async

# Use a reasoning-optimized model
agent = make_agent_async(
    "openai:o1",  # Native reasoning model
    """Analyze this genetic variant and provide:
1. Classification (pathogenic/benign/VUS)
2. Supporting evidence
3. Confidence level"""
)

step = Step(name="variant_analysis", agent=agent)
```

**When to Use:**
- Deep analysis tasks
- Complex logical reasoning
- When explicit CoT/ToT overhead isn't needed

---

## 4. Hybrid Patterns

Combine reasoning techniques for complex workflows:

### CoT + ToT Pipeline

```python
from flujo import Flujo, Pipeline, Step
from flujo.domain.dsl import TreeSearchStep

# Stage 1: CoT for initial analysis
analysis_step = Step.granular(
    name="initial_analysis",
    agent=analysis_agent,
    history_max_tokens=4096,
)

# Stage 2: ToT for solution exploration
exploration_step = TreeSearchStep(
    name="solution_exploration",
    proposer=proposer,
    evaluator=evaluator,
    branching_factor=3,
    beam_width=2,
    max_depth=3,
)

# Stage 3: CoT for final synthesis
synthesis_step = Step.granular(
    name="synthesis",
    agent=synthesis_agent,
    history_max_tokens=4096,
)

pipeline = Pipeline(steps=[analysis_step, exploration_step, synthesis_step])
```

---

## 5. MED13-Specific Patterns

### Query Generation with Confidence Routing

```python
from flujo import Pipeline, Step
from flujo.domain.dsl import ConditionalStep, HumanInTheLoopStep

# Generate query with reasoning
query_step = Step.granular(
    name="query_generation",
    agent=query_agent,
    enforce_idempotency=True,
)

# Route based on confidence
def check_confidence(output, ctx) -> str:
    return "review" if output.confidence_score < 0.85 else "proceed"

governance_gate = ConditionalStep(
    name="confidence_gate",
    condition_callable=check_confidence,
    branches={
        "review": Pipeline(steps=[
            HumanInTheLoopStep(
                name="human_review",
                message_for_user="Low confidence query. Please review.",
            )
        ]),
        "proceed": Pipeline(steps=[
            Step.from_callable(lambda x, _: x, name="passthrough")
        ]),
    },
)

pipeline = Pipeline(steps=[query_step, governance_gate])
```

### Evidence Extraction with Tool Use

```python
# Agent that extracts evidence from multiple sources
evidence_agent = make_agent_async(
    "openai:gpt-4o",
    """You are extracting evidence for a genetic variant.

For each claim, you must:
1. Search relevant databases (ClinVar, PubMed)
2. Extract supporting quotes
3. Assign confidence scores

Always cite your sources with DOIs or accession numbers.""",
    tools=[search_clinvar, search_pubmed, fetch_abstract],
)

step = Step.granular(
    name="evidence_extraction",
    agent=evidence_agent,
    history_max_tokens=16384,  # Larger context for multiple tool calls
    enforce_idempotency=True,
)
```

---

## Summary

| Pattern | Primitive | Durability | Use Case |
|---------|-----------|------------|----------|
| Simple task | `Step` | Per-step | Direct generation |
| Sequential reasoning | `Step.granular()` / `GranularStep` | Per-turn | CoT, ReAct, tool use |
| Branching exploration | `TreeSearchStep` | Per-candidate | ToT, A* search |
| Native reasoning | `Step` + `o1` model | Per-step | Deep analysis |
| Hybrid | Pipeline composition | Mixed | Complex workflows |

**Key Principle:** Choose the simplest pattern that meets your auditability and exploration needs. Over-engineering reasoning adds latency and cost without proportional benefit.

---

## Related Documentation

- **[Agent Architecture](./agent_architecture.md)**: Complete implementation guide
- **[Contract-Oriented AI](./contract_oriented_ai.md)**: Evidence-first contracts
- **[Production Guide](./prod_guide.md)**: Deployment configuration
