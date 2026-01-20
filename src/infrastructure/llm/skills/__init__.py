"""
Flujo Skills registry for AI agents.

Skills are bounded capabilities that agents can invoke.
Every skill must be explicitly registered with:
- Unique namespaced ID
- Input/output schemas
- Side effects declaration
- Governance metadata
"""

from src.infrastructure.llm.skills.registry import (
    SkillRegistry,
    register_all_skills,
)

__all__ = [
    "register_all_skills",
    "SkillRegistry",
]
