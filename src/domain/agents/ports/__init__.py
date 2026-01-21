"""
Port interfaces for AI agent operations.

Defines how the application layer interacts with AI agents
following the Ports & Adapters (Hexagonal) architecture pattern.
"""

from src.domain.agents.ports.model_registry_port import ModelRegistryPort
from src.domain.agents.ports.query_agent_port import QueryAgentPort

__all__ = [
    "ModelRegistryPort",
    "QueryAgentPort",
]
