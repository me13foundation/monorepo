"""
Data ingestion infrastructure for MED13 Resource Library.
Provides API clients, rate limiting, and data acquisition capabilities.
"""

from .base_ingestor import BaseIngestor, IngestionResult, IngestionError
from .clinvar_ingestor import ClinVarIngestor
from .pubmed_ingestor import PubMedIngestor
from .hpo_ingestor import HPOIngestor
from .uniprot_ingestor import UniProtIngestor
from .coordinator import IngestionCoordinator

__all__ = [
    "BaseIngestor",
    "IngestionResult",
    "IngestionError",
    "ClinVarIngestor",
    "PubMedIngestor",
    "HPOIngestor",
    "UniProtIngestor",
    "IngestionCoordinator",
]
