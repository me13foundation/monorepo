"""
Gene-variant relationship mapping service.

Establishes and manages relationships between genes and genetic variants
from different data sources, enabling comprehensive genotype-phenotype
correlation analysis.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..normalizers.gene_normalizer import NormalizedGene, GeneNormalizer
from ..normalizers.variant_normalizer import NormalizedVariant, VariantNormalizer


class GeneVariantRelationship(Enum):
    """Types of relationships between genes and variants."""

    WITHIN_GENE = "within_gene"  # Variant located within gene boundaries
    REGULATORY = "regulatory"  # Variant affects gene regulation
    SPLICE_SITE = "splice_site"  # Variant affects splicing
    CODING = "coding"  # Variant in coding region
    UTR = "utr"  # Variant in untranslated region
    INTRONIC = "intronic"  # Variant in intron
    UPSTREAM = "upstream"  # Variant upstream of gene
    DOWNSTREAM = "downstream"  # Variant downstream of gene


@dataclass
class GeneVariantLink:
    """Link between a gene and a variant."""

    gene_id: str
    variant_id: str
    relationship_type: GeneVariantRelationship
    confidence_score: float
    evidence_sources: List[str]
    genomic_distance: Optional[int]  # Distance in base pairs if applicable
    functional_impact: Optional[str]  # e.g., "missense", "frameshift"


class GeneVariantMapper:
    """
    Maps relationships between genes and variants.

    Analyzes genomic coordinates and functional annotations to establish
    relationships between genes and genetic variants from multiple sources.
    """

    def __init__(
        self,
        gene_normalizer: Optional[GeneNormalizer] = None,
        variant_normalizer: Optional[VariantNormalizer] = None,
    ):
        self.gene_normalizer = gene_normalizer or GeneNormalizer()
        self.variant_normalizer = variant_normalizer or VariantNormalizer()

        # Mapping cache: gene_id -> list of variant links
        self.gene_to_variants: Dict[str, List[GeneVariantLink]] = {}

        # Reverse mapping: variant_id -> list of gene links
        self.variant_to_genes: Dict[str, List[GeneVariantLink]] = {}

        # Genomic coordinate mappings for overlap detection
        self.gene_coordinates: Dict[
            str, Tuple[str, int, int]
        ] = {}  # gene_id -> (chrom, start, end)

    def add_gene_coordinates(
        self, gene_id: str, chromosome: str, start_pos: int, end_pos: int
    ):
        """
        Add genomic coordinates for a gene.

        Args:
            gene_id: Gene identifier
            chromosome: Chromosome name
            start_pos: Start position
            end_pos: End position
        """
        self.gene_coordinates[gene_id] = (chromosome, start_pos, end_pos)

    def map_gene_variant_relationship(
        self, gene: NormalizedGene, variant: NormalizedVariant
    ) -> Optional[GeneVariantLink]:
        """
        Determine the relationship between a gene and variant.

        Args:
            gene: Normalized gene object
            variant: Normalized variant object

        Returns:
            GeneVariantLink if relationship found, None otherwise
        """
        # Get genomic coordinates
        gene_coords = self.gene_coordinates.get(gene.primary_id)
        variant_location = variant.genomic_location

        if not gene_coords or not variant_location:
            return None

        gene_chrom, gene_start, gene_end = gene_coords
        variant_chrom = variant_location.chromosome
        variant_pos = variant_location.position

        # Must be on same chromosome
        if gene_chrom != variant_chrom:
            return None

        if variant_pos is None:
            return None

        # Determine relationship type
        relationship = self._determine_relationship_type(
            gene_start, gene_end, variant_pos, variant_location
        )

        if relationship:
            link = GeneVariantLink(
                gene_id=gene.primary_id,
                variant_id=variant.primary_id,
                relationship_type=relationship,
                confidence_score=self._calculate_confidence(variant),
                evidence_sources=[variant.source],
                genomic_distance=self._calculate_distance(
                    gene_start, gene_end, variant_pos
                ),
                functional_impact=self._infer_functional_impact(variant),
            )

            # Cache the mapping
            if gene.primary_id not in self.gene_to_variants:
                self.gene_to_variants[gene.primary_id] = []
            self.gene_to_variants[gene.primary_id].append(link)

            if variant.primary_id not in self.variant_to_genes:
                self.variant_to_genes[variant.primary_id] = []
            self.variant_to_genes[variant.primary_id].append(link)

            return link

        return None

    def _determine_relationship_type(
        self, gene_start: int, gene_end: int, variant_pos: int, variant_location
    ) -> Optional[GeneVariantRelationship]:
        """Determine the type of relationship between gene and variant."""
        # Define extended gene region (include regulatory regions)
        extended_start = gene_start - 2000  # 2kb upstream
        extended_end = gene_end + 500  # 500bp downstream

        if gene_start <= variant_pos <= gene_end:
            # Within gene boundaries
            if variant_location.reference_allele and variant_location.alternate_allele:
                # Check for splice site variants (within 10bp of exon boundaries)
                # This is simplified - in practice would need exon coordinates
                distance_to_start = abs(variant_pos - gene_start)
                distance_to_end = abs(variant_pos - gene_end)

                if distance_to_start <= 10 or distance_to_end <= 10:
                    return GeneVariantRelationship.SPLICE_SITE
                else:
                    return GeneVariantRelationship.CODING  # Assume coding by default
            else:
                return GeneVariantRelationship.WITHIN_GENE

        elif extended_start <= variant_pos < gene_start:
            return GeneVariantRelationship.UPSTREAM

        elif gene_end < variant_pos <= extended_end:
            return GeneVariantRelationship.DOWNSTREAM

        return None

    def _calculate_confidence(self, variant: NormalizedVariant) -> float:
        """Calculate confidence score for gene-variant relationship."""
        confidence = 0.5  # Base confidence

        # Higher confidence for variants with genomic coordinates
        if variant.genomic_location and variant.genomic_location.position:
            confidence += 0.2

        # Higher confidence for ClinVar variants
        if variant.source == "clinvar":
            confidence += 0.2

        # Higher confidence for variants with functional annotations
        if variant.hgvs_notations:
            confidence += 0.1

        return min(1.0, confidence)

    def _calculate_distance(
        self, gene_start: int, gene_end: int, variant_pos: int
    ) -> int:
        """Calculate genomic distance between gene and variant."""
        if gene_start <= variant_pos <= gene_end:
            return 0  # Within gene
        elif variant_pos < gene_start:
            return gene_start - variant_pos
        else:
            return variant_pos - gene_end

    def _infer_functional_impact(self, variant: NormalizedVariant) -> Optional[str]:
        """Infer functional impact from variant annotations."""
        # Check HGVS notations for functional clues
        for notation_type, notation in variant.hgvs_notations.items():
            if notation_type == "p":  # Protein notation
                if "fs" in notation:  # Frameshift
                    return "frameshift"
                elif "del" in notation:  # Deletion
                    return "deletion"
                elif "*" in notation:  # Nonsense
                    return "nonsense"
                else:
                    return "missense"  # Assume missense by default

        # Check variant type
        if variant.id_type.name == "SINGLE_NUCLEOTIDE_VARIANT":
            return "substitution"

        return None

    def find_variants_for_gene(self, gene_id: str) -> List[GeneVariantLink]:
        """
        Find all variants associated with a gene.

        Args:
            gene_id: Gene identifier

        Returns:
            List of gene-variant links
        """
        return self.gene_to_variants.get(gene_id, [])

    def find_genes_for_variant(self, variant_id: str) -> List[GeneVariantLink]:
        """
        Find all genes associated with a variant.

        Args:
            variant_id: Variant identifier

        Returns:
            List of gene-variant links
        """
        return self.variant_to_genes.get(variant_id, [])

    def get_relationship_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about gene-variant relationships.

        Returns:
            Dictionary with relationship statistics
        """
        stats = {
            "total_relationships": 0,
            "genes_with_variants": len(self.gene_to_variants),
            "variants_with_genes": len(self.variant_to_genes),
            "relationship_types": {},
        }

        for links in self.gene_to_variants.values():
            stats["total_relationships"] += len(links)
            for link in links:
                rel_type = link.relationship_type.value
                if rel_type not in stats["relationship_types"]:
                    stats["relationship_types"][rel_type] = 0
                stats["relationship_types"][rel_type] += 1

        return stats

    def validate_mapping(self, link: GeneVariantLink) -> List[str]:
        """
        Validate a gene-variant mapping.

        Args:
            link: GeneVariantLink to validate

        Returns:
            List of validation error messages
        """
        errors = []

        if not link.gene_id:
            errors.append("Missing gene ID")

        if not link.variant_id:
            errors.append("Missing variant ID")

        if link.confidence_score < 0 or link.confidence_score > 1:
            errors.append("Invalid confidence score")

        if link.genomic_distance is not None and link.genomic_distance < 0:
            errors.append("Invalid genomic distance")

        return errors

    def merge_duplicate_links(self):
        """Merge duplicate gene-variant links."""
        # This would remove duplicates and merge evidence
        # Simplified implementation
        pass

    def export_mappings(self, format: str = "json") -> str:
        """
        Export gene-variant mappings in specified format.

        Args:
            format: Export format ("json", "csv", etc.)

        Returns:
            Formatted string representation of mappings
        """
        if format == "json":
            import json

            mappings = {
                "gene_to_variants": {
                    gene_id: [
                        {
                            "variant_id": link.variant_id,
                            "relationship": link.relationship_type.value,
                            "confidence": link.confidence_score,
                            "distance": link.genomic_distance,
                            "impact": link.functional_impact,
                        }
                        for link in links
                    ]
                    for gene_id, links in self.gene_to_variants.items()
                }
            }
            return json.dumps(mappings, indent=2)

        return "Unsupported format"
