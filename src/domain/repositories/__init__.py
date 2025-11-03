"""
Domain repository interfaces - abstract contracts for data access.

These interfaces define the contracts that domain services depend on,
enabling dependency inversion and testability.
"""

from .base import Repository, QuerySpecification
from .gene_repository import GeneRepository
from .variant_repository import VariantRepository
from .phenotype_repository import PhenotypeRepository
from .evidence_repository import EvidenceRepository
from .publication_repository import PublicationRepository

__all__ = [
    "Repository",
    "QuerySpecification",
    "GeneRepository",
    "VariantRepository",
    "PhenotypeRepository",
    "EvidenceRepository",
    "PublicationRepository",
]
