# MED13 Resource Library - Pydantic Models
# Strongly typed data models with validation

from .gene import Gene, GeneCreate, GeneResponse
from src.domain.entities.gene import Gene as DomainGene  # re-export domain entity
from src.domain.entities.variant import (
    Variant as DomainVariant,
)  # re-export domain entity
from src.domain.entities.phenotype import (
    Phenotype as DomainPhenotype,
)  # re-export domain entity
from src.domain.entities.publication import (
    Publication as DomainPublication,
)  # re-export domain entity
from src.domain.entities.evidence import (
    Evidence as DomainEvidence,
)  # re-export domain entity

# TODO: Uncomment when models are implemented
# from .variant import Variant, VariantCreate, VariantResponse, VariantEvidence
# from .phenotype import Phenotype, PhenotypeCreate, PhenotypeResponse
# from .publication import Publication, PublicationCreate, PublicationResponse
# from .evidence import Evidence, EvidenceCreate, EvidenceResponse, EvidenceLevel

__all__ = [
    "Gene",
    "GeneCreate",
    "GeneResponse",
    # Domain re-exports for migration
    "DomainGene",
    "DomainVariant",
    "DomainPhenotype",
    "DomainPublication",
    "DomainEvidence",
    # TODO: Uncomment when models are implemented
    # "Variant", "VariantCreate", "VariantResponse", "VariantEvidence",
    # "Phenotype", "PhenotypeCreate", "PhenotypeResponse",
    # "Publication", "PublicationCreate", "PublicationResponse",
    # "Evidence", "EvidenceCreate", "EvidenceResponse", "EvidenceLevel",
]
