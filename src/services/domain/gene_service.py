"""
Gene service for MED13 Resource Library.
Business logic for gene entity operations and validations.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from src.repositories import GeneRepository, VariantRepository
from src.models.database import GeneModel
from src.models.value_objects import GeneIdentifier, Provenance
from src.services.domain.base_service import BaseService


class GeneService(BaseService[GeneModel]):
    """
    Service for gene business logic and operations.

    Provides high-level operations for gene management including
    validation, creation, and relationship management.
    """

    def __init__(self, session: Optional[Session] = None):
        super().__init__(session)
        self.gene_repo = GeneRepository(session)
        self.variant_repo = VariantRepository(session)

    @property
    def repository(self) -> GeneRepository:
        return self.gene_repo

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
    ) -> GeneModel:
        """
        Create a new gene with validation.

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
            Created GeneModel instance

        Raises:
            ValueError: If validation fails
            DuplicateError: If gene already exists
        """
        # Validate positions if both are provided
        if start_position is not None and end_position is not None:
            if end_position < start_position:
                raise ValueError("End position must be greater than start position")

        normalized_symbol = symbol.upper()
        gene_identifier = gene_id or normalized_symbol

        # Create the gene
        gene = GeneModel(
            gene_id=gene_identifier,
            symbol=normalized_symbol,
            name=name,
            description=description,
            gene_type=gene_type,
            chromosome=chromosome,
            start_position=start_position,
            end_position=end_position,
            ensembl_id=ensembl_id,
            ncbi_gene_id=ncbi_gene_id,
            uniprot_id=uniprot_id,
        )

        # Add provenance metadata if provided
        if provenance:
            # Could add provenance tracking here
            pass

        return self.repository.create(gene)

    def list_genes(
        self,
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        search: Optional[str] = None,
    ) -> Tuple[List[GeneModel], int]:
        """Retrieve paginated genes with optional search."""
        return self.gene_repo.paginate_genes(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
        )

    def get_gene_by_id(self, gene_id: str) -> Optional[GeneModel]:
        """Retrieve a gene by its public gene identifier."""
        return self.gene_repo.find_by_gene_id(gene_id)

    def get_gene_by_symbol(self, symbol: str) -> Optional[GeneModel]:
        """Retrieve a gene by its symbol."""
        return self.gene_repo.find_by_symbol(symbol.upper())

    def find_gene_by_identifier(
        self, identifier: GeneIdentifier
    ) -> Optional[GeneModel]:
        """
        Find a gene by its identifier (supports multiple ID types).

        Args:
            identifier: GeneIdentifier value object

        Returns:
            GeneModel instance or None if not found
        """
        # Try different ID types in order of preference
        gene = self.gene_repo.find_by_gene_id(identifier.gene_id)
        if gene:
            return gene

        gene = self.gene_repo.find_by_symbol(identifier.symbol)
        if gene:
            return gene

        if identifier.ensembl_id:
            gene = self.gene_repo.find_by_external_id(identifier.ensembl_id)
        if not gene and identifier.ncbi_gene_id:
            gene = self.gene_repo.find_by_external_id(str(identifier.ncbi_gene_id))
        if not gene and identifier.uniprot_id:
            gene = self.gene_repo.find_by_external_id(identifier.uniprot_id)

        return gene

    def get_gene_with_variants(self, gene_id: int) -> Optional[GeneModel]:
        """
        Get a gene with its associated variants loaded.

        Args:
            gene_id: Gene ID to retrieve

        Returns:
            GeneModel with variants relationship loaded
        """
        gene = self.gene_repo.get_by_id(gene_id)
        if gene:
            # Load variants (in a real implementation, this would use joined loading)
            gene.variants = self.variant_repo.find_by_gene(gene_id)
        return gene

    def search_genes(self, query: str, limit: int = 10) -> List[GeneModel]:
        """
        Search genes by symbol or name.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching GeneModel instances
        """
        return self.gene_repo.search_by_name_or_symbol(query, limit)

    def update_gene(self, gene_id: str, updates: Dict[str, Any]) -> GeneModel:
        """Update mutable gene fields by gene identifier."""
        gene = self.gene_repo.find_by_gene_id_or_fail(gene_id)

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

        return self.repository.update(gene.id, sanitized_updates)

    def update_gene_locations(
        self,
        gene_id: int,
        chromosome: Optional[str] = None,
        start_position: Optional[int] = None,
        end_position: Optional[int] = None,
    ) -> GeneModel:
        """
        Update gene genomic location information.

        Args:
            gene_id: Gene ID to update
            chromosome: New chromosome
            start_position: New start position
            end_position: New end position

        Returns:
            Updated GeneModel instance

        Raises:
            ValueError: If positions are invalid
            NotFoundError: If gene not found
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

        return self.repository.update(gene_id, updates)

    def delete_gene(self, gene_id: str) -> None:
        """Delete a gene by its gene identifier."""
        gene = self.gene_repo.find_by_gene_id_or_fail(gene_id)
        self.repository.delete(gene.id)

    def get_gene_variants(self, gene_id: str) -> List[Dict[str, Any]]:
        """Return serialized variants associated with a gene."""
        gene = self.gene_repo.find_by_gene_id(gene_id)
        if gene is None:
            return []

        variants = self.variant_repo.find_by_gene(gene.id)
        serialized: List[Dict[str, Any]] = []
        for variant in variants:
            serialized.append(
                {
                    "variant_id": variant.variant_id,
                    "clinvar_id": variant.clinvar_id,
                    "chromosome": variant.chromosome,
                    "position": variant.position,
                    "clinical_significance": getattr(
                        variant, "clinical_significance", None
                    ),
                }
            )
        return serialized

    def get_gene_phenotypes(self, gene_id: str) -> List[Dict[str, Any]]:
        """Return related phenotypes for a gene (placeholder implementation)."""
        # Phenotype relationships are not yet modeled; return empty list for now.
        return []

    def gene_has_variants(self, gene_id: str) -> bool:
        """Check whether a gene has associated variants."""
        gene = self.gene_repo.find_by_gene_id(gene_id)
        if gene is None:
            return False
        variants = self.variant_repo.find_by_gene(gene.id, limit=1)
        return bool(variants)

    def get_gene_statistics(self, gene_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive statistics about genes.

        Returns:
            Dictionary with gene statistics
        """
        if gene_id:
            gene = self.gene_repo.find_by_gene_id_or_fail(gene_id)
            variants = self.variant_repo.find_by_gene(gene.id)
            return {
                "gene_id": gene.gene_id,
                "symbol": gene.symbol,
                "variant_count": len(variants),
                "has_location": gene.chromosome is not None,
            }

        stats = self.gene_repo.get_gene_statistics()

        # Add additional computed statistics
        total_genes = stats["total_genes"]
        if total_genes > 0:
            # Calculate additional metrics
            genes_with_location = len(
                [
                    g
                    for g in self.repository.find_all(limit=1000)
                    if g.chromosome is not None
                ]
            )
            stats["genes_with_location"] = genes_with_location
            stats["location_coverage"] = genes_with_location / total_genes

        return stats

    def validate_gene_exists(self, gene_id: int) -> bool:
        """
        Validate that a gene exists.

        Args:
            gene_id: Gene ID to validate

        Returns:
            True if gene exists, False otherwise
        """
        return bool(self.repository.exists(gene_id))

    def get_gene_summary(self, gene_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a summary of gene information including variant counts.

        Args:
            gene_id: Gene ID to summarize

        Returns:
            Dictionary with gene summary or None if not found
        """
        gene = self.repository.get_by_id(gene_id)
        if not gene:
            return None

        variant_count = len(self.variant_repo.find_by_gene(gene_id))

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
            "created_at": gene.created_at,
            "updated_at": gene.updated_at,
        }
