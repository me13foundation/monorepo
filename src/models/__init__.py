# MED13 Resource Library - Pydantic Models
# Strongly typed data models with validation

from src.domain.entities.evidence import (
    Evidence as DomainEvidence,
)

# re-export domain entity
from src.domain.entities.gene import Gene as DomainGene  # re-export domain entity
from src.domain.entities.phenotype import (
    Phenotype as DomainPhenotype,
)

# re-export domain entity
from src.domain.entities.publication import (
    Publication as DomainPublication,
)

# re-export domain entity
from src.domain.entities.variant import (
    Variant as DomainVariant,
)

# re-export domain entity
from .gene import Gene, GeneCreate, GeneResponse

__all__ = [
    "DomainEvidence",
    "DomainGene",
    "DomainPhenotype",
    "DomainPublication",
    "DomainVariant",
    "Gene",
    "GeneCreate",
    "GeneResponse",
]
