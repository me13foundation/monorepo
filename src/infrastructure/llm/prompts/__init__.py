"""
Version-controlled system prompts for AI agents.

Prompts are organized by agent type and source to enable:
- Version control and review of prompt changes
- Centralized prompt management
- Easy A/B testing of prompt variations
"""

from src.infrastructure.llm.prompts.base_prompts import (
    BIOMEDICAL_CONTEXT_TEMPLATE,
    EVIDENCE_INSTRUCTION,
)
from src.infrastructure.llm.prompts.query.pubmed import PUBMED_QUERY_SYSTEM_PROMPT

__all__ = [
    "BIOMEDICAL_CONTEXT_TEMPLATE",
    "EVIDENCE_INSTRUCTION",
    "PUBMED_QUERY_SYSTEM_PROMPT",
]
