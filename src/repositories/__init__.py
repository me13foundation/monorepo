# MED13 Resource Library - Repository Layer
# Data access abstractions following repository pattern

from .base import BaseRepository
from .gene_repository import GeneRepository
from .variant_repository import VariantRepository
from .phenotype_repository import PhenotypeRepository
from .evidence_repository import EvidenceRepository
from .publication_repository import PublicationRepository

__all__ = [
    "BaseRepository",
    "GeneRepository",
    "VariantRepository",
    "PhenotypeRepository",
    "EvidenceRepository",
    "PublicationRepository",
]
