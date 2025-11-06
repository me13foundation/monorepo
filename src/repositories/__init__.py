# MED13 Resource Library - Repository Layer
# Data access abstractions following repository pattern

from .base import BaseRepository
from .evidence_repository import EvidenceRepository
from .gene_repository import GeneRepository
from .phenotype_repository import PhenotypeRepository
from .publication_repository import PublicationRepository
from .variant_repository import VariantRepository

__all__ = [
    "BaseRepository",
    "EvidenceRepository",
    "GeneRepository",
    "PhenotypeRepository",
    "PublicationRepository",
    "VariantRepository",
]
