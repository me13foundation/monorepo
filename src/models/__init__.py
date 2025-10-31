# MED13 Resource Library - Pydantic Models
# Strongly typed data models with validation

from .gene import Gene, GeneCreate, GeneResponse

# TODO: Uncomment when models are implemented
# from .variant import Variant, VariantCreate, VariantResponse, VariantEvidence
# from .phenotype import Phenotype, PhenotypeCreate, PhenotypeResponse
# from .publication import Publication, PublicationCreate, PublicationResponse
# from .evidence import Evidence, EvidenceCreate, EvidenceResponse, EvidenceLevel

__all__ = [
    "Gene",
    "GeneCreate",
    "GeneResponse",
    # TODO: Uncomment when models are implemented
    # "Variant", "VariantCreate", "VariantResponse", "VariantEvidence",
    # "Phenotype", "PhenotypeCreate", "PhenotypeResponse",
    # "Publication", "PublicationCreate", "PublicationResponse",
    # "Evidence", "EvidenceCreate", "EvidenceResponse", "EvidenceLevel",
]
