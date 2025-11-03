"""
Gene domain service - pure business logic for gene entities.

Encapsulates gene-specific business rules, validations, and logic
without infrastructure dependencies.
"""

from typing import Any, Dict, List, Optional

from .base import DomainService
from ..entities.gene import Gene, GeneType
from ..value_objects.identifiers import GeneIdentifier


class GeneDomainService(DomainService):
    """
    Domain service for Gene business logic.

    Contains pure business rules for gene validation, normalization,
    and derived property calculations.
    """

    def validate_business_rules(
        self, entity: Gene, operation: str, context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Validate gene business rules.

        Args:
            entity: Gene entity to validate
            operation: Operation being performed
            context: Additional validation context

        Returns:
            List of validation error messages
        """
        errors = []

        # Symbol validation
        if not self._is_valid_gene_symbol(entity.symbol):
            errors.append("Gene symbol must be uppercase alphanumeric with underscores")

        # Genomic position validation
        if entity.start_position and entity.end_position:
            if entity.end_position < entity.start_position:
                errors.append("End position must be greater than start position")

        # External ID validation
        if entity.ensembl_id and not entity.ensembl_id.startswith("ENSG"):
            errors.append("Ensembl ID must start with 'ENSG'")

        if entity.ncbi_gene_id and entity.ncbi_gene_id <= 0:
            errors.append("NCBI Gene ID must be positive")

        return errors

    def apply_business_logic(self, entity: Gene, operation: str) -> Gene:
        """
        Apply gene business logic transformations.

        Args:
            entity: Gene entity to transform
            operation: Operation being performed

        Returns:
            Transformed gene entity
        """
        # Normalize symbol to uppercase
        if operation in ("create", "update"):
            entity.update_identifier(symbol=entity.symbol.upper())

        # Set default gene type if not specified
        if not entity.gene_type or entity.gene_type == GeneType.UNKNOWN:
            entity.gene_type = self._infer_gene_type(entity)

        return entity

    def calculate_derived_properties(self, entity: Gene) -> Dict[str, Any]:
        """
        Calculate derived properties for a gene.

        Args:
            entity: Gene entity

        Returns:
            Dictionary of derived properties
        """
        derived: Dict[str, Any] = {}

        # Calculate genomic size
        if entity.start_position and entity.end_position:
            derived["genomic_size"] = entity.end_position - entity.start_position + 1
        else:
            derived["genomic_size"] = None

        # Determine if gene has genomic location
        derived["has_genomic_location"] = (
            entity.chromosome is not None
            and entity.start_position is not None
            and entity.end_position is not None
        )

        # Count external identifiers
        external_ids = [entity.ensembl_id, entity.ncbi_gene_id, entity.uniprot_id]
        derived["external_id_count"] = len(
            [id for id in external_ids if id is not None]
        )

        return derived

    def validate_gene_symbol_uniqueness(
        self, symbol: str, existing_symbols: List[str]
    ) -> bool:
        """
        Validate that a gene symbol is unique.

        Args:
            symbol: Symbol to validate
            existing_symbols: List of existing symbols

        Returns:
            True if symbol is unique
        """
        normalized_symbol = symbol.upper()
        return normalized_symbol not in [s.upper() for s in existing_symbols]

    def normalize_gene_identifiers(self, identifiers: GeneIdentifier) -> GeneIdentifier:
        """
        Normalize gene identifiers according to business rules.

        Args:
            identifiers: Raw gene identifiers

        Returns:
            Normalized identifiers
        """
        symbol = identifiers.symbol or identifiers.gene_id
        if symbol is None:
            raise ValueError("GeneIdentifier must contain at least a symbol or gene_id")

        gene_id = identifiers.gene_id or symbol

        return GeneIdentifier(
            gene_id=gene_id.upper(),
            symbol=symbol.upper(),
            ensembl_id=identifiers.ensembl_id,
            ncbi_gene_id=identifiers.ncbi_gene_id,
            uniprot_id=(
                identifiers.uniprot_id.upper() if identifiers.uniprot_id else None
            ),
        )

    def calculate_gene_similarity_score(self, gene1: Gene, gene2: Gene) -> float:
        """
        Calculate similarity score between two genes.

        Args:
            gene1: First gene
            gene2: Second gene

        Returns:
            Similarity score between 0.0 and 1.0
        """
        score = 0.0
        total_weight = 0.0

        # Symbol match (high weight)
        if gene1.symbol.upper() == gene2.symbol.upper():
            score += 1.0
            total_weight += 1.0

        # External ID matches
        external_ids1 = {gene1.ensembl_id, gene1.uniprot_id}
        external_ids2 = {gene2.ensembl_id, gene2.uniprot_id}
        if external_ids1 & external_ids2:  # Intersection
            score += 0.8
            total_weight += 0.8

        # Genomic location proximity (if both have locations)
        if (
            gene1.chromosome
            and gene2.chromosome
            and gene1.chromosome == gene2.chromosome
            and gene1.start_position
            and gene2.start_position
        ):
            distance = abs(gene1.start_position - gene2.start_position)
            if distance == 0:
                score += 0.9
                total_weight += 0.9
            elif distance < 10000:  # Within 10kb
                score += 0.5
                total_weight += 0.5

        return score / total_weight if total_weight > 0 else 0.0

    def _is_valid_gene_symbol(self, symbol: str) -> bool:
        """Validate gene symbol format."""
        if not symbol:
            return False

        # Must be uppercase alphanumeric with underscores/hyphens
        import re

        return bool(re.match(r"^[A-Z0-9_-]+$", symbol))

    def _infer_gene_type(self, gene: Gene) -> str:
        """Infer gene type based on available information."""
        # This is a simplified inference - in reality would use more complex rules
        if gene.uniprot_id:
            return GeneType.PROTEIN_CODING
        elif gene.name and any(
            term in gene.name.lower() for term in ["rna", "pseudogene"]
        ):
            return GeneType.NCRNA if "rna" in gene.name.lower() else GeneType.PSEUDOGENE

        return GeneType.UNKNOWN


__all__ = ["GeneDomainService"]
