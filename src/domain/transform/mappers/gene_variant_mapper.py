"""Typed gene-variant mapper used in unit tests."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

UPSTREAM_PADDING_BP = 2000
DOWNSTREAM_PADDING_BP = 500
SPLICE_BORDER_BP = 10


class GeneVariantRelationship(Enum):
    WITHIN_GENE = "within_gene"
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"
    SPLICE_SITE = "splice_site"
    CODING = "coding"


@dataclass
class GeneVariantLink:
    gene_id: str
    variant_id: str
    relationship_type: GeneVariantRelationship
    confidence_score: float
    evidence_sources: list[str]
    genomic_distance: int | None
    functional_impact: str | None


class GeneVariantMapper:
    def __init__(self) -> None:
        self.gene_coordinates: dict[str, tuple[str, int, int]] = {}
        self.gene_to_variants: dict[str, list[GeneVariantLink]] = {}
        self.variant_to_genes: dict[str, list[GeneVariantLink]] = {}

    def add_gene_coordinates(
        self,
        gene_id: str,
        chromosome: str,
        start_pos: int,
        end_pos: int,
    ) -> None:
        self.gene_coordinates[gene_id] = (chromosome, start_pos, end_pos)

    def map_gene_variant_relationship(
        self,
        gene: Any,
        variant: Any,
    ) -> GeneVariantLink | None:
        gene_coords = self.gene_coordinates.get(getattr(gene, "primary_id", ""))
        variant_location = getattr(variant, "genomic_location", None)

        if not gene_coords or variant_location is None:
            return None

        chromosome = getattr(variant_location, "chromosome", None)
        position = getattr(variant_location, "position", None)
        if chromosome is None or position is None:
            return None

        gene_chrom, gene_start, gene_end = gene_coords
        if chromosome != gene_chrom:
            return None

        relationship = self._determine_relationship_type(
            gene_start,
            gene_end,
            position,
            variant,
        )
        if relationship is None:
            return None

        link = GeneVariantLink(
            gene_id=getattr(gene, "primary_id", ""),
            variant_id=getattr(variant, "primary_id", ""),
            relationship_type=relationship,
            confidence_score=0.8,
            evidence_sources=[getattr(variant, "source", "unknown")],
            genomic_distance=self._calculate_distance(gene_start, gene_end, position),
            functional_impact=None,
        )

        self.gene_to_variants.setdefault(link.gene_id, []).append(link)
        self.variant_to_genes.setdefault(link.variant_id, []).append(link)
        return link

    def find_variants_for_gene(self, gene_id: str) -> list[GeneVariantLink]:
        return list(self.gene_to_variants.get(gene_id, []))

    def find_genes_for_variant(self, variant_id: str) -> list[GeneVariantLink]:
        return list(self.variant_to_genes.get(variant_id, []))

    def validate_mapping(self, link: GeneVariantLink) -> list[str]:
        errors: list[str] = []
        if not link.gene_id:
            errors.append("Missing gene ID")
        if not link.variant_id:
            errors.append("Missing variant ID")
        if not 0.0 <= link.confidence_score <= 1.0:
            errors.append("Invalid confidence score")
        if link.genomic_distance is not None and link.genomic_distance < 0:
            errors.append("Invalid genomic distance")
        return errors

    def export_mappings(self) -> dict[str, list[dict[str, Any]]]:
        return {
            gene_id: [link.__dict__ for link in links]
            for gene_id, links in self.gene_to_variants.items()
        }

    def _determine_relationship_type(
        self,
        gene_start: int,
        gene_end: int,
        variant_pos: int,
        _variant: Any | None = None,
    ) -> GeneVariantRelationship | None:
        extended_start = gene_start - UPSTREAM_PADDING_BP
        extended_end = gene_end + DOWNSTREAM_PADDING_BP

        if gene_start <= variant_pos <= gene_end:
            if (
                variant_pos - gene_start <= SPLICE_BORDER_BP
                or gene_end - variant_pos <= SPLICE_BORDER_BP
            ):
                return GeneVariantRelationship.SPLICE_SITE
            return GeneVariantRelationship.CODING
        if extended_start <= variant_pos < gene_start:
            return GeneVariantRelationship.UPSTREAM
        if gene_end < variant_pos <= extended_end:
            return GeneVariantRelationship.DOWNSTREAM
        return None

    @staticmethod
    def _calculate_distance(gene_start: int, gene_end: int, variant_pos: int) -> int:
        if gene_start <= variant_pos <= gene_end:
            return 0
        if variant_pos < gene_start:
            return gene_start - variant_pos
        return variant_pos - gene_end


__all__ = ["GeneVariantLink", "GeneVariantMapper", "GeneVariantRelationship"]
