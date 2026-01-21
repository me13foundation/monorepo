"""
Domain layer for AI agents.

This module defines the contracts, contexts, model specifications, and port
interfaces for AI agents. Contracts are the architecture - they define what
agents can output, how decisions are justified, and when humans must intervene.
"""

from src.domain.agents.contexts.base import BaseAgentContext
from src.domain.agents.contexts.query_context import QueryGenerationContext
from src.domain.agents.contracts.base import (
    AgentDecision,
    BaseAgentContract,
    EvidenceItem,
)
from src.domain.agents.contracts.query_generation import QueryGenerationContract
from src.domain.agents.models import (
    ModelCapability,
    ModelCostTier,
    ModelReasoningSettings,
    ModelSpec,
)

__all__ = [
    # Contracts
    "AgentDecision",
    "BaseAgentContract",
    "EvidenceItem",
    "QueryGenerationContract",
    # Contexts
    "BaseAgentContext",
    "QueryGenerationContext",
    # Models
    "ModelCapability",
    "ModelCostTier",
    "ModelReasoningSettings",
    "ModelSpec",
]
