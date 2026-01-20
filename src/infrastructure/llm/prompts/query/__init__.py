"""
Query generation prompts for various data sources.

Each data source has its own prompt module optimized for
that source's query syntax and capabilities.
"""

from src.infrastructure.llm.prompts.query.pubmed import PUBMED_QUERY_SYSTEM_PROMPT

__all__ = [
    "PUBMED_QUERY_SYSTEM_PROMPT",
]
