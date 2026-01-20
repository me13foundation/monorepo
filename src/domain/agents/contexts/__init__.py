"""
Typed PipelineContext extensions for AI agents.

Never use plain dict for context. Extend PipelineContext to enforce
schema validity and enable safe persistence with indexed fields.
"""

from src.domain.agents.contexts.base import BaseAgentContext
from src.domain.agents.contexts.query_context import QueryGenerationContext

__all__ = [
    "BaseAgentContext",
    "QueryGenerationContext",
]
