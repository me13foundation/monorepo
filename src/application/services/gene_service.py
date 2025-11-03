"""Application-level orchestration for gene use cases."""

from typing import Any, Dict, List, Optional, Tuple

from src.domain.entities.gene import Gene
from src.domain.entities.variant import VariantSummary
from src.domain.repositories.gene_repository import GeneRepository
from src.domain.repositories.variant_repository import VariantRepository
from src.domain.services.gene_domain_service import GeneDomainService
from src.domain.value_objects.identifiers import GeneIdentifier
from src.domain.value_objects.provenance import Provenance


class GeneApplicationService:
    """
    Application service for gene management use cases.

    Orchestrates domain services and repositories to implement
    gene-related business operations with proper dependency injection.
    """

    def __init__(
        self,
        gene_repository: GeneRepository,
        gene_domain_service: GeneDomainService,
        variant_repository: VariantRepository,
    ):
        """
        Initialize the gene application service.

        Args:
            gene_repository: Domain repository for genes
            gene_domain_service: Domain service for gene business logic
            variant_repository: Domain repository for variants
        """
        self._gene_repository = gene_repository
        self._gene_domain_service = gene_domain_service
        self._variant_repository = variant_repository

    def create_gene(
        self,
        symbol: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        gene_type: str = "protein_coding",
        gene_id: Optional[str] = None,
        chromosome: Optional[str] = None,
        start_position: Optional[int] = None,
        end_position: Optional[int] = None,
        ensembl_id: Optional[str] = None,
        ncbi_gene_id: Optional[int] = None,
        uniprot_id: Optional[str] = None,
        provenance: Optional[Provenance] = None,
    ) -> Gene:
        """
        Create a new gene with validation and business rules.

        Args:
            symbol: Gene symbol
            name: Full gene name
            description: Gene description
            gene_type: Type of gene
            gene_id: Optional pre-defined gene identifier
            chromosome: Chromosome location
            start_position: Start position on chromosome
            end_position: End position on chromosome
            ensembl_id: Ensembl gene ID
            ncbi_gene_id: NCBI Gene ID
            uniprot_id: UniProt accession
            provenance: Data provenance information

        Returns:
            Created Gene entity

        Raises:
            ValueError: If validation fails
        """
        # Validate positions if both are provided
        if start_position is not None and end_position is not None:
            if end_position < start_position:
                raise ValueError("End position must be greater than start position")

        normalized_symbol = symbol.upper()
        gene_identifier = gene_id or normalized_symbol

        # Create the gene entity
        gene_entity = Gene.create(
            symbol=normalized_symbol,
            gene_id=gene_identifier,
            gene_type=gene_type,
            name=name,
            description=description,
            chromosome=chromosome,
            start_position=start_position,
            end_position=end_position,
            ensembl_id=ensembl_id,
            ncbi_gene_id=ncbi_gene_id,
            uniprot_id=uniprot_id,
            provenance=provenance,
        )

        # Apply domain business logic
        gene_entity = self._gene_domain_service.apply_business_logic(
            gene_entity, "create"
        )

        # Validate business rules
        errors = self._gene_domain_service.validate_business_rules(
            gene_entity, "create"
        )
        if errors:
            raise ValueError(f"Business rule violations: {', '.join(errors)}")

        # Persist the entity
        return self._gene_repository.create(gene_entity)

    def list_genes(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        search: Optional[str] = None,
    ) -> Tuple[List[Gene], int]:
        """Retrieve paginated genes with optional search."""
        return self._gene_repository.paginate_genes(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
        )

    def get_gene_by_id(self, gene_id: str) -> Optional[Gene]:
        """Retrieve a gene by its public gene identifier."""
        return self._gene_repository.find_by_gene_id(gene_id)

    def get_gene_by_symbol(self, symbol: str) -> Optional[Gene]:
        """Retrieve a gene by its symbol."""
        return self._gene_repository.find_by_symbol(symbol.upper())

    def find_gene_by_identifier(self, identifier: GeneIdentifier) -> Optional[Gene]:
        """
        Find a gene by its identifier (supports multiple ID types).

        Args:
            identifier: GeneIdentifier value object

        Returns:
            Gene entity or None if not found
        """
        # Try different ID types in order of preference
        gene = self._gene_repository.find_by_gene_id(identifier.gene_id)
        if gene:
            return gene

        gene = self._gene_repository.find_by_symbol(identifier.symbol)
        if gene:
            return gene

        if identifier.ensembl_id:
            gene = self._gene_repository.find_by_external_id(identifier.ensembl_id)
        if not gene and identifier.ncbi_gene_id:
            gene = self._gene_repository.find_by_external_id(
                str(identifier.ncbi_gene_id)
            )
        if not gene and identifier.uniprot_id:
            gene = self._gene_repository.find_by_external_id(identifier.uniprot_id)

        return gene

    def get_gene_with_variants(self, gene_id: int) -> Optional[Gene]:
        """
        Get a gene with its associated variants loaded.

        Args:
            gene_id: Gene ID to retrieve

        Returns:
            Gene entity with variants relationship loaded
        """
        gene = self._gene_repository.get_by_id(gene_id)
        if gene:
            variant_models = self._variant_repository.find_by_gene(gene_id)
            # Convert to summaries (this would need proper mapping)
            gene.variants = [
                VariantSummary(
                    variant_id=getattr(variant, "variant_id", ""),
                    clinvar_id=getattr(variant, "clinvar_id", None),
                    chromosome=getattr(variant, "chromosome", ""),
                    position=getattr(variant, "position", 0),
                    clinical_significance=getattr(
                        variant, "clinical_significance", None
                    ),
                )
                for variant in variant_models
            ]
        return gene

    def search_genes(self, query: str, limit: int = 10) -> List[Gene]:
        """
        Search genes by symbol or name.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching Gene entities
        """
        return self._gene_repository.search_by_name_or_symbol(query, limit)

    def update_gene(self, gene_id: str, updates: Dict[str, Any]) -> Gene:
        """Update mutable gene fields by gene identifier."""
        gene = self._gene_repository.find_by_gene_id_or_fail(gene_id)

        allowed_fields = {
            "name",
            "description",
            "gene_type",
            "chromosome",
            "start_position",
            "end_position",
            "ensembl_id",
            "ncbi_gene_id",
            "uniprot_id",
        }

        sanitized_updates = {
            key: value for key, value in updates.items() if key in allowed_fields
        }

        if not sanitized_updates:
            raise ValueError("No valid fields provided for update")

        gene_db_id = self._require_gene_db_id(gene)
        updated_gene = self._gene_repository.update(gene_db_id, sanitized_updates)

        # Apply domain business logic to updated entity
        updated_gene = self._gene_domain_service.apply_business_logic(
            updated_gene, "update"
        )

        return updated_gene

    def update_gene_locations(
        self,
        gene_id: int,
        chromosome: Optional[str] = None,
        start_position: Optional[int] = None,
        end_position: Optional[int] = None,
    ) -> Gene:
        """
        Update gene genomic location information.

        Args:
            gene_id: Gene ID to update
            chromosome: New chromosome
            start_position: New start position
            end_position: New end position

        Returns:
            Updated Gene entity

        Raises:
            ValueError: If positions are invalid
        """
        # Validate positions
        if start_position is not None and end_position is not None:
            if end_position < start_position:
                raise ValueError("End position must be greater than start position")

        updates: Dict[str, Any] = {}
        if chromosome is not None:
            updates["chromosome"] = chromosome
        if start_position is not None:
            updates["start_position"] = start_position
        if end_position is not None:
            updates["end_position"] = end_position

        if not updates:
            raise ValueError("No location updates provided")

        return self._gene_repository.update(gene_id, updates)

    def delete_gene(self, gene_id: str) -> None:
        """Delete a gene by its gene identifier."""
        gene = self._gene_repository.find_by_gene_id_or_fail(gene_id)
        gene_db_id = self._require_gene_db_id(gene)
        self._gene_repository.delete(gene_db_id)

    def get_gene_variants(self, gene_id: str) -> List[VariantSummary]:
        """Return serialized variants associated with a gene."""
        gene = self._gene_repository.find_by_gene_id(gene_id)
        if gene is None:
            return []

        gene_db_id = self._require_gene_db_id(gene)
        variant_models = self._variant_repository.find_by_gene(gene_db_id)
        return [
            VariantSummary(
                variant_id=getattr(variant, "variant_id", ""),
                clinvar_id=getattr(variant, "clinvar_id", None),
                chromosome=getattr(variant, "chromosome", ""),
                position=getattr(variant, "position", 0),
                clinical_significance=getattr(variant, "clinical_significance", None),
            )
            for variant in variant_models
        ]

    def get_gene_phenotypes(self, gene_id: str) -> List[Dict[str, str]]:
        """Return related phenotypes for a gene (placeholder implementation)."""
        # Phenotype relationships are not yet modeled; return empty list for now.
        return []

    def gene_has_variants(self, gene_id: str) -> bool:
        """Check whether a gene has associated variants."""
        gene = self._gene_repository.find_by_gene_id(gene_id)
        if gene is None:
            return False
        gene_db_id = self._require_gene_db_id(gene)
        variants = self._variant_repository.find_by_gene(gene_db_id, limit=1)
        return bool(variants)

    def get_gene_statistics(
        self, gene_id: Optional[str] = None
    ) -> Dict[str, int | float | bool | str | None]:
        """
        Get comprehensive statistics about genes.

        Returns:
            Dictionary with gene statistics
        """
        if gene_id:
            gene = self._gene_repository.find_by_gene_id_or_fail(gene_id)
            gene_db_id = self._require_gene_db_id(gene)
            variants = self._variant_repository.find_by_gene(gene_db_id)
            return {
                "gene_id": gene.gene_id,
                "symbol": gene.symbol,
                "variant_count": len(variants),
                "has_location": gene.chromosome is not None,
            }

        stats_raw: Dict[str, Any] = self._gene_repository.get_gene_statistics()
        stats: Dict[str, int | float | bool | str | None] = {}
        for key, value in stats_raw.items():
            if isinstance(value, (int, float, bool, str)) or value is None:
                stats[key] = value

        total_genes = self._coerce_int(stats_raw.get("total_genes"))
        stats["total_genes"] = total_genes

        # Add additional computed statistics
        if total_genes and total_genes > 0:
            # Calculate additional metrics (simplified)
            stats["genes_with_location"] = stats_raw.get("genes_with_location", 0)
            stats["location_coverage"] = stats_raw.get("location_coverage", 0.0)

        return stats

    def validate_gene_exists(self, gene_id: int) -> bool:
        """
        Validate that a gene exists.

        Args:
            gene_id: Gene ID to validate

        Returns:
            True if gene exists, False otherwise
        """
        return self._gene_repository.exists(gene_id)

    def get_gene_summary(
        self, gene_id: int
    ) -> Optional[Dict[str, int | float | bool | str | None]]:
        """
        Get a summary of gene information including variant counts.

        Args:
            gene_id: Gene ID to summarize

        Returns:
            Dictionary with gene summary or None if not found
        """
        gene = self._gene_repository.get_by_id(gene_id)
        if not gene:
            return None

        variant_count = len(self._variant_repository.find_by_gene(gene_id))

        return {
            "id": gene.id,
            "gene_id": gene.gene_id,
            "symbol": gene.symbol,
            "name": gene.name,
            "gene_type": gene.gene_type,
            "chromosome": gene.chromosome,
            "start_position": gene.start_position,
            "end_position": gene.end_position,
            "variant_count": variant_count,
            "created_at": gene.created_at.isoformat() if gene.created_at else None,
            "updated_at": gene.updated_at.isoformat() if gene.updated_at else None,
        }

    def _require_gene_db_id(self, gene: Gene) -> int:
        if gene.id is None:
            raise ValueError("Gene is not persisted and lacks a database id")
        return gene.id

    @staticmethod
    def _coerce_int(value: Any, default: int = 0) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        return default


__all__ = ["GeneApplicationService"]
