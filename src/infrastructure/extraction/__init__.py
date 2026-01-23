"""Extraction processor adapters."""

from src.infrastructure.extraction.placeholder_extraction_processor import (
    PlaceholderExtractionProcessor,
)
from src.infrastructure.extraction.rule_based_pubmed_extraction_processor import (
    RuleBasedPubMedExtractionProcessor,
)

__all__ = [
    "PlaceholderExtractionProcessor",
    "RuleBasedPubMedExtractionProcessor",
]
