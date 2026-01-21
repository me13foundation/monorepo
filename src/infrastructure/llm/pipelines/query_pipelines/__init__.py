"""
Query generation pipelines for various data sources.

Each pipeline composes an agent with governance patterns
for confidence-based routing and human-in-the-loop escalation.
"""

from src.infrastructure.llm.pipelines.query_pipelines.pubmed_pipeline import (
    create_pubmed_query_pipeline,
)

__all__ = [
    "create_pubmed_query_pipeline",
]
