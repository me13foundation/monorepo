"""
Gene-Variant Relationship Domain Service.

Encapsulates business logic for gene-variant relationships.
"""

from dataclasses import dataclass

from src.domain.entities.gene import Gene
from src.domain.entities.variant import Variant
from src.domain.value_objects.confidence import Confidence


@dataclass
class RelationshipAssessment:
    """Assessment of gene-variant relationship strength."""

    is_valid_association: bool
    confidence_score: Confidence
    relationship_type: str
    validation_errors: list[str]
    evidence_strength: str


class GeneVariantRelationshipService:
    """
    Domain service for gene-variant relationship business logic.

    This service encapsulates the logic for determining valid gene-variant associations.
    """

    @staticmethod
    def assess_relationship(gene: Gene, variant: Variant) -> RelationshipAssessment:
        """
        Assess the relationship between a gene and variant.

        Args:
            gene: The gene entity
            variant: The variant entity

        Returns:
            Assessment of the relationship validity and strength
        """
        validation_errors = []
        relationship_type = "unknown"
        evidence_strength = "weak"

        # Basic validation
        is_valid = GeneVariantRelationshipService._is_basic_association_valid(
            gene, variant
        )

        if not is_valid:
            validation_errors.append("Gene and variant are not on the same chromosome")

        # Determine relationship type
        if is_valid:
            relationship_type = "coding_variant"
            evidence_strength = "moderate"

        # Calculate confidence score
        confidence_value = 0.8 if is_valid else 0.1
        confidence_score = Confidence.from_score(confidence_value)

        return RelationshipAssessment(
            is_valid_association=is_valid,
            confidence_score=confidence_score,
            relationship_type=relationship_type,
            validation_errors=validation_errors,
            evidence_strength=evidence_strength,
        )

    @staticmethod
    def can_gene_have_variant(gene: Gene, variant: Variant) -> bool:
        """
        Determine if a gene can logically be associated with a variant.

        Args:
            gene: The gene entity
            variant: The variant entity

        Returns:
            True if the association is biologically plausible
        """
        return GeneVariantRelationshipService._is_basic_association_valid(gene, variant)

    @staticmethod
    def _is_basic_association_valid(gene: Gene, variant: Variant) -> bool:
        """Check if the basic association between gene and variant is valid."""
        # Gene must have genomic location
        if not gene.chromosome or not gene.start_position or not gene.end_position:
            return False

        # Variant must have genomic location
        if not hasattr(variant, "chromosome") or not hasattr(variant, "position"):
            return False

        variant_chromosome = getattr(variant, "chromosome", None)
        variant_position = getattr(variant, "position", None)

        if not variant_chromosome or variant_position is None:
            return False

        # Must be on same chromosome
        if gene.chromosome != variant_chromosome:
            return False

        # Variant position should be within gene boundaries (with some tolerance)
        # We know these are not None due to the checks above
        assert gene.start_position is not None
        assert gene.end_position is not None

        gene_start = gene.start_position
        gene_end = gene.end_position

        # Allow variants within gene boundaries or in regulatory regions (extend by 5kb)
        regulatory_padding = 5000
        extended_start = gene_start - regulatory_padding
        extended_end = gene_end + regulatory_padding

        return extended_start <= variant_position <= extended_end  # type: ignore
