"""
Data transformation pipeline for MED13 Resource Library.

This module provides the core transformation components that convert raw
biomedical data from various sources into standardized, validated formats
ready for curation and packaging.

Key Components:
- Parsers: Extract structured data from raw source formats (XML, JSON, etc.)
- Normalizers: Standardize identifiers and data formats across sources
- Mappers: Create cross-references between related entities
- Transformers: Orchestrate the complete transformation pipeline

Architecture follows clean architecture principles with separation of concerns
and comprehensive error handling.
"""

from .parsers import ClinVarParser, PubMedParser, HPOParser, UniProtParser
from .normalizers import (
    GeneNormalizer,
    VariantNormalizer,
    PhenotypeNormalizer,
    PublicationNormalizer,
)
from .mappers import GeneVariantMapper, VariantPhenotypeMapper, CrossReferenceMapper
from .transformers import ETLTransformer, TransformationPipeline

__all__ = [
    # Parsers
    "ClinVarParser",
    "PubMedParser",
    "HPOParser",
    "UniProtParser",
    # Normalizers
    "GeneNormalizer",
    "VariantNormalizer",
    "PhenotypeNormalizer",
    "PublicationNormalizer",
    # Mappers
    "GeneVariantMapper",
    "VariantPhenotypeMapper",
    "CrossReferenceMapper",
    # Transformers
    "ETLTransformer",
    "TransformationPipeline",
]
