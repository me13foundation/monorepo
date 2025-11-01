"""
Cross-reference mapping coordination service.

Orchestrates cross-referencing between different biomedical entities
(genes, variants, phenotypes, publications) to create a unified
knowledge graph of relationships.
"""

from typing import Dict, List, Any, Set
from dataclasses import dataclass
from enum import Enum

from .gene_variant_mapper import GeneVariantMapper, GeneVariantLink
from .variant_phenotype_mapper import VariantPhenotypeMapper, VariantPhenotypeLink
from ..normalizers.gene_normalizer import GeneNormalizer
from ..normalizers.variant_normalizer import VariantNormalizer
from ..normalizers.phenotype_normalizer import PhenotypeNormalizer
from ..normalizers.publication_normalizer import PublicationNormalizer


class CrossReferenceType(Enum):
    """Types of cross-references."""

    GENE_VARIANT = "gene_variant"
    VARIANT_PHENOTYPE = "variant_phenotype"
    GENE_PHENOTYPE = "gene_phenotype"  # Inferred through variants
    PUBLICATION_VARIANT = "publication_variant"
    PUBLICATION_PHENOTYPE = "publication_phenotype"


@dataclass
class CrossReferenceNetwork:
    """Network of cross-references between biomedical entities."""

    genes: Set[str]
    variants: Set[str]
    phenotypes: Set[str]
    publications: Set[str]

    # Relationship mappings
    gene_variant_links: List[GeneVariantLink]
    variant_phenotype_links: List[VariantPhenotypeLink]

    # Inferred relationships
    gene_phenotype_links: List[Dict[str, Any]]


class CrossReferenceMapper:
    """
    Coordinates cross-referencing between biomedical entities.

    Integrates gene-variant and variant-phenotype mappings to create
    comprehensive genotype-phenotype relationship networks.
    """

    def __init__(self):
        self.gene_variant_mapper = GeneVariantMapper()
        self.variant_phenotype_mapper = VariantPhenotypeMapper()

        # Normalizers for ID resolution
        self.gene_normalizer = GeneNormalizer()
        self.variant_normalizer = VariantNormalizer()
        self.phenotype_normalizer = PhenotypeNormalizer()
        self.publication_normalizer = PublicationNormalizer()

        # Cross-reference networks by disease/gene
        self.networks: Dict[str, CrossReferenceNetwork] = {}

    def build_cross_reference_network(
        self, gene_symbol: str, include_publications: bool = False
    ) -> CrossReferenceNetwork:
        """
        Build a comprehensive cross-reference network for a gene.

        Args:
            gene_symbol: Gene symbol to build network around
            include_publications: Whether to include publication references

        Returns:
            CrossReferenceNetwork with all relationships
        """
        network_key = gene_symbol.lower()

        if network_key in self.networks:
            return self.networks[network_key]

        # Initialize network
        network = CrossReferenceNetwork(
            genes=set(),
            variants=set(),
            phenotypes=set(),
            publications=set(),
            gene_variant_links=[],
            variant_phenotype_links=[],
            gene_phenotype_links=[],
        )

        # Find the normalized gene
        gene = self.gene_normalizer.find_gene_by_symbol(gene_symbol)
        if not gene:
            return network

        network.genes.add(gene.primary_id)

        # Get variants for this gene
        variant_links = self.gene_variant_mapper.find_variants_for_gene(gene.primary_id)
        network.gene_variant_links.extend(variant_links)

        # Collect variant IDs
        for link in variant_links:
            network.variants.add(link.variant_id)

            # Get phenotypes for each variant
            phenotype_links = self.variant_phenotype_mapper.find_phenotypes_for_variant(
                link.variant_id
            )
            network.variant_phenotype_links.extend(phenotype_links)

            # Collect phenotype IDs
            for pheno_link in phenotype_links:
                network.phenotypes.add(pheno_link.phenotype_id)

        # Infer gene-phenotype relationships
        network.gene_phenotype_links = self._infer_gene_phenotype_relationships(
            network.gene_variant_links, network.variant_phenotype_links
        )

        # Optionally include publications
        if include_publications:
            self._add_publication_references(network)

        self.networks[network_key] = network
        return network

    def _infer_gene_phenotype_relationships(
        self,
        gene_variant_links: List[GeneVariantLink],
        variant_phenotype_links: List[VariantPhenotypeLink],
    ) -> List[Dict[str, Any]]:
        """
        Infer gene-phenotype relationships from gene-variant and variant-phenotype links.

        Args:
            gene_variant_links: Direct gene-variant relationships
            variant_phenotype_links: Direct variant-phenotype relationships

        Returns:
            List of inferred gene-phenotype relationships
        """
        gene_phenotype_map = {}

        # Group variants by gene
        variants_by_gene = {}
        for gv_link in gene_variant_links:
            if gv_link.gene_id not in variants_by_gene:
                variants_by_gene[gv_link.gene_id] = []
            variants_by_gene[gv_link.gene_id].append(gv_link.variant_id)

        # Group phenotypes by variant
        phenotypes_by_variant = {}
        for vp_link in variant_phenotype_links:
            if vp_link.variant_id not in phenotypes_by_variant:
                phenotypes_by_variant[vp_link.variant_id] = []
            phenotypes_by_variant[vp_link.variant_id].append(vp_link)

        # Infer gene-phenotype relationships
        for gene_id, variant_ids in variants_by_gene.items():
            gene_phenotypes = {}

            for variant_id in variant_ids:
                if variant_id in phenotypes_by_variant:
                    for vp_link in phenotypes_by_variant[variant_id]:
                        phenotype_id = vp_link.phenotype_id
                        if phenotype_id not in gene_phenotypes:
                            gene_phenotypes[phenotype_id] = {
                                "gene_id": gene_id,
                                "phenotype_id": phenotype_id,
                                "supporting_variants": [],
                                "relationship_types": set(),
                                "confidence_scores": [],
                                "evidence_sources": set(),
                            }

                        gene_phenotypes[phenotype_id]["supporting_variants"].append(
                            variant_id
                        )
                        gene_phenotypes[phenotype_id]["relationship_types"].add(
                            vp_link.relationship_type.value
                        )
                        gene_phenotypes[phenotype_id]["confidence_scores"].append(
                            vp_link.confidence_score
                        )
                        gene_phenotypes[phenotype_id]["evidence_sources"].update(
                            vp_link.evidence_sources
                        )

            # Convert to final format
            for phenotype_data in gene_phenotypes.values():
                phenotype_data["relationship_types"] = list(
                    phenotype_data["relationship_types"]
                )
                phenotype_data["evidence_sources"] = list(
                    phenotype_data["evidence_sources"]
                )
                phenotype_data["average_confidence"] = sum(
                    phenotype_data["confidence_scores"]
                ) / len(phenotype_data["confidence_scores"])

        return list(gene_phenotype_map.values())

    def _add_publication_references(self, network: CrossReferenceNetwork):
        """Add publication references to the network."""
        # This would link publications to variants/phenotypes
        # Simplified implementation
        pass

    def find_related_entities(
        self, entity_id: str, entity_type: str, max_depth: int = 2
    ) -> Dict[str, List[str]]:
        """
        Find related entities through the cross-reference network.

        Args:
            entity_id: Starting entity identifier
            entity_type: Type of starting entity ('gene', 'variant', 'phenotype')
            max_depth: Maximum traversal depth

        Returns:
            Dictionary mapping entity types to lists of related IDs
        """
        related = {"genes": [], "variants": [], "phenotypes": [], "publications": []}

        visited = set()
        queue = [(entity_id, entity_type, 0)]

        while queue:
            current_id, current_type, depth = queue.pop(0)

            if depth >= max_depth or (current_id, current_type) in visited:
                continue

            visited.add((current_id, current_type))

            if current_type == "gene":
                # Find related variants
                variant_links = self.gene_variant_mapper.find_variants_for_gene(
                    current_id
                )
                for link in variant_links:
                    if link.variant_id not in related["variants"]:
                        related["variants"].append(link.variant_id)
                        queue.append((link.variant_id, "variant", depth + 1))

            elif current_type == "variant":
                # Find related genes
                gene_links = self.gene_variant_mapper.find_genes_for_variant(current_id)
                for link in gene_links:
                    if link.gene_id not in related["genes"]:
                        related["genes"].append(link.gene_id)
                        queue.append((link.gene_id, "gene", depth + 1))

                # Find related phenotypes
                phenotype_links = (
                    self.variant_phenotype_mapper.find_phenotypes_for_variant(
                        current_id
                    )
                )
                for link in phenotype_links:
                    if link.phenotype_id not in related["phenotypes"]:
                        related["phenotypes"].append(link.phenotype_id)
                        queue.append((link.phenotype_id, "phenotype", depth + 1))

            elif current_type == "phenotype":
                # Find related variants
                variant_links = (
                    self.variant_phenotype_mapper.find_variants_for_phenotype(
                        current_id
                    )
                )
                for link in variant_links:
                    if link.variant_id not in related["variants"]:
                        related["variants"].append(link.variant_id)
                        queue.append((link.variant_id, "variant", depth + 1))

        return related

    def get_network_statistics(self, network: CrossReferenceNetwork) -> Dict[str, Any]:
        """
        Get statistics about a cross-reference network.

        Args:
            network: CrossReferenceNetwork to analyze

        Returns:
            Dictionary with network statistics
        """
        stats = {
            "nodes": {
                "genes": len(network.genes),
                "variants": len(network.variants),
                "phenotypes": len(network.phenotypes),
                "publications": len(network.publications),
                "total": len(network.genes)
                + len(network.variants)
                + len(network.phenotypes)
                + len(network.publications),
            },
            "edges": {
                "gene_variant": len(network.gene_variant_links),
                "variant_phenotype": len(network.variant_phenotype_links),
                "gene_phenotype": len(network.gene_phenotype_links),
                "total": len(network.gene_variant_links)
                + len(network.variant_phenotype_links)
                + len(network.gene_phenotype_links),
            },
            "connectivity": self._calculate_connectivity(network),
            "pathogenic_variants": self._count_pathogenic_variants(network),
        }

        return stats

    def _calculate_connectivity(self, network: CrossReferenceNetwork) -> float:
        """Calculate network connectivity score."""
        if not network.nodes["variants"]:
            return 0.0

        # Simple connectivity: average phenotypes per variant
        total_phenotypes = len(network.phenotypes)
        total_variants = len(network.variants)

        return total_phenotypes / total_variants if total_variants > 0 else 0.0

    def _count_pathogenic_variants(self, network: CrossReferenceNetwork) -> int:
        """Count pathogenic variants in the network."""
        pathogenic_count = 0

        for link in network.variant_phenotype_links:
            if link.relationship_type.value in ["causative", "associated"]:
                pathogenic_count += 1

        return pathogenic_count

    def validate_network(self, network: CrossReferenceNetwork) -> List[str]:
        """
        Validate a cross-reference network.

        Args:
            network: CrossReferenceNetwork to validate

        Returns:
            List of validation error messages
        """
        errors = []

        # Check for orphaned nodes
        for link in network.gene_variant_links:
            if link.gene_id not in network.genes:
                errors.append(
                    f"Gene {link.gene_id} referenced in link but not in network"
                )
            if link.variant_id not in network.variants:
                errors.append(
                    f"Variant {link.variant_id} referenced in link but not in network"
                )

        for link in network.variant_phenotype_links:
            if link.variant_id not in network.variants:
                errors.append(
                    f"Variant {link.variant_id} referenced in link but not in network"
                )
            if link.phenotype_id not in network.phenotypes:
                errors.append(
                    f"Phenotype {link.phenotype_id} referenced in link but not in network"
                )

        return errors

    def export_network(
        self, network: CrossReferenceNetwork, format: str = "json"
    ) -> str:
        """
        Export a cross-reference network in specified format.

        Args:
            network: CrossReferenceNetwork to export
            format: Export format ("json", "graphml", etc.)

        Returns:
            Formatted string representation of the network
        """
        if format == "json":
            import json

            network_dict = {
                "nodes": {
                    "genes": list(network.genes),
                    "variants": list(network.variants),
                    "phenotypes": list(network.phenotypes),
                    "publications": list(network.publications),
                },
                "edges": {
                    "gene_variant": [
                        {
                            "gene": link.gene_id,
                            "variant": link.variant_id,
                            "relationship": link.relationship_type.value,
                            "confidence": link.confidence_score,
                        }
                        for link in network.gene_variant_links
                    ],
                    "variant_phenotype": [
                        {
                            "variant": link.variant_id,
                            "phenotype": link.phenotype_id,
                            "relationship": link.relationship_type.value,
                            "confidence": link.confidence_score,
                        }
                        for link in network.variant_phenotype_links
                    ],
                    "gene_phenotype": network.gene_phenotype_links,
                },
            }
            return json.dumps(network_dict, indent=2)

        return "Unsupported format"
